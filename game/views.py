from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Max, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ChatMessageForm, PetForm, PrivateMessageForm, ProfileSettingsForm, RegisterForm, SupportTicketForm, UserReportForm
from .models import (
    ActionCooldown,
    ActionLog,
    Achievement,
    ChatMessage,
    EquippedWearable,
    Friendship,
    InventoryItem,
    Item,
    OwnedWearable,
    Pet,
    PetShow,
    PlayerAchievement,
    PlayerProfile,
    PrivateMessage,
    Quest,
    QuestProgress,
    ShowEntry,
    SupportTicket,
    UserReport,
    WearableItem,
)


ACTION_RULES = {
    "feed": {
        "label": "покормил",
        "energy": 0,
        "mood": 3,
        "hunger": 22,
        "experience": 8,
        "coins": 4,
        "quest": Quest.FEED,
        "requires": {},
    },
    "play": {
        "label": "поиграл с",
        "energy": -18,
        "mood": 20,
        "hunger": -7,
        "experience": 13,
        "coins": 7,
        "quest": Quest.PLAY,
        "requires": {"energy": 15},
    },
    "pet": {
        "label": "погладил",
        "energy": 0,
        "mood": 10,
        "hunger": -2,
        "experience": 5,
        "coins": 3,
        "quest": Quest.PET,
        "requires": {},
    },
    "walk": {
        "label": "вывел гулять",
        "energy": -25,
        "mood": 14,
        "hunger": -12,
        "experience": 18,
        "coins": 11,
        "quest": Quest.WALK,
        "requires": {"energy": 25},
    },
}

COOLDOWNS = {
    "pet_action": 8,
    "buy_item": 2,
    "claim_quest": 2,
    "train": 20,
    "show": 30,
    "chat": 10,
    "message": 10,
    "support": 60,
}


def get_profile(user):
    profile, _created = PlayerProfile.objects.get_or_create(user=user)
    profile.last_activity_at = timezone.now()
    profile.save(update_fields=["last_activity_at"])
    return profile


def online_count():
    cutoff = timezone.now() - timezone.timedelta(minutes=5)
    return PlayerProfile.objects.filter(last_activity_at__gte=cutoff).count()


def set_cooldown(profile, key, seconds):
    ActionCooldown.objects.update_or_create(
        profile=profile,
        key=key,
        defaults={"available_at": timezone.now() + timezone.timedelta(seconds=seconds)},
    )


def cooldown_seconds(profile, key):
    cooldown = ActionCooldown.objects.filter(profile=profile, key=key).first()
    if not cooldown:
        return 0
    remaining = int((cooldown.available_at - timezone.now()).total_seconds())
    if remaining <= 0:
        cooldown.delete()
        return 0
    return remaining


def enforce_cooldown(request, profile, key):
    remaining = cooldown_seconds(profile, key)
    if remaining:
        messages.error(request, f"Слишком быстро. Повтори действие через {remaining} сек.")
        return False
    set_cooldown(profile, key, COOLDOWNS[key])
    return True


def restore_energy(profile):
    now = timezone.now()
    elapsed_minutes = int((now - profile.last_energy_tick).total_seconds() // 60)
    ticks = elapsed_minutes // 5
    if ticks <= 0:
        return 0
    restored = 0
    for pet in profile.user.pets.all():
        before = pet.energy
        pet.energy = min(100, pet.energy + ticks)
        if pet.energy != before:
            pet.save(update_fields=["energy"])
            restored += pet.energy - before
    profile.last_energy_tick = profile.last_energy_tick + timezone.timedelta(minutes=ticks * 5)
    profile.save(update_fields=["last_energy_tick"])
    return restored


def active_pet(user):
    return user.pets.filter(active=True).first() or user.pets.order_by("created_at").first()


def sync_daily_quests(profile):
    today = timezone.localdate()
    progress_items = []
    for quest in Quest.objects.filter(active=True).order_by("id"):
        progress, _created = QuestProgress.objects.get_or_create(profile=profile, quest=quest, date=today)
        progress_items.append(progress)
    return progress_items


def add_quest_progress(profile, action, amount=1):
    today = timezone.localdate()
    for quest in Quest.objects.filter(active=True, action=action):
        progress, _created = QuestProgress.objects.get_or_create(profile=profile, quest=quest, date=today)
        if progress.completed:
            continue
        progress.count = min(quest.target_count, progress.count + amount)
        progress.completed = progress.count >= quest.target_count
        progress.save()


def log_action(profile, text, pet=None):
    ActionLog.objects.create(profile=profile, pet=pet, text=text)


def award_achievement(request, profile, code):
    achievement = Achievement.objects.filter(code=code).first()
    if not achievement:
        return
    _unlocked, created = PlayerAchievement.objects.get_or_create(profile=profile, achievement=achievement)
    if created:
        profile.coins += achievement.reward_coins
        profile.save(update_fields=["coins"])
        messages.success(request, f"Достижение: {achievement.title}. Бонус +{achievement.reward_coins} монет.")
        log_action(profile, f"Открыто достижение «{achievement.title}»")


def check_passive_achievements(request, profile):
    if profile.user.pets.count() >= 3:
        award_achievement(request, profile, Achievement.THREE_PETS)
    if profile.coins >= 250:
        award_achievement(request, profile, Achievement.RICH)
    if profile.user.pets.filter(level__gte=3).exists():
        award_achievement(request, profile, Achievement.LEVEL_3)


def ensure_starter_pet(user):
    if user.pets.exists():
        return
    Pet.objects.create(owner=user, name="Искорка", species=Pet.CAT, active=True)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "game/home.html")


def health(request):
    return JsonResponse({"status": "ok"})


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        get_profile(user)
        ensure_starter_pet(user)
        login(request, user)
        messages.success(request, "Добро пожаловать! Стартовый питомец уже ждет тебя.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    profile = get_profile(request.user)
    ensure_starter_pet(request.user)
    restored = restore_energy(profile)
    if restored:
        messages.info(request, f"Питомцы отдохнули и восстановили {restored} энергии.")
    pet = active_pet(request.user)
    if pet and not pet.active:
        Pet.objects.filter(owner=request.user).update(active=False)
        pet.active = True
        pet.save(update_fields=["active"])
    context = {
        "profile": profile,
        "pet": pet,
        "pets": request.user.pets.order_by("-active", "created_at"),
        "quest_progress": sync_daily_quests(profile)[:3],
        "logs": profile.logs.select_related("pet")[:5],
        "achievements": profile.achievements.select_related("achievement")[:4],
        "equipped": pet.equipped_wearables.select_related("wearable") if pet else [],
        "online_count": online_count(),
        "actions": ACTION_RULES,
    }
    check_passive_achievements(request, profile)
    return render(request, "game/dashboard.html", context)


@login_required
def profile(request):
    profile_obj = get_profile(request.user)
    restore_energy(profile_obj)
    return render(
        request,
        "game/profile.html",
        {
            "profile": profile_obj,
            "pets": request.user.pets.order_by("-active", "-level", "name"),
            "inventory_count": profile_obj.inventory.aggregate(total=Sum("quantity"))["total"] or 0,
            "wearable_count": profile_obj.wardrobe.aggregate(total=Sum("quantity"))["total"] or 0,
            "achievements": profile_obj.achievements.select_related("achievement"),
            "logs": profile_obj.logs.select_related("pet")[:12],
            "medals": profile_obj.show_entries.values("medal").annotate(total=Count("id")),
        },
    )


@login_required
def settings(request):
    profile_obj = get_profile(request.user)
    form = ProfileSettingsForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Настройки профиля сохранены.")
        return redirect("profile")
    return render(request, "game/settings.html", {"form": form, "profile": profile_obj})


@login_required
def create_pet(request):
    form = PetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        pet = form.save(commit=False)
        pet.owner = request.user
        if not request.user.pets.exists():
            pet.active = True
        pet.save()
        log_action(get_profile(request.user), f"В команде появился питомец {pet.name}.", pet)
        check_passive_achievements(request, get_profile(request.user))
        messages.success(request, f"{pet.name} теперь в твоей команде.")
        return redirect("dashboard")
    return render(request, "game/pet_form.html", {"form": form})


@login_required
def select_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    Pet.objects.filter(owner=request.user).update(active=False)
    pet.active = True
    pet.save(update_fields=["active"])
    log_action(get_profile(request.user), f"{pet.name} выбран активным питомцем.", pet)
    messages.success(request, f"{pet.name} выбран активным питомцем.")
    return redirect("dashboard")


@login_required
def pet_action(request, action):
    if request.method != "POST":
        return redirect("dashboard")
    rule = ACTION_RULES.get(action)
    pet = active_pet(request.user)
    profile_obj = get_profile(request.user)
    if not rule or not pet:
        messages.error(request, "Это действие сейчас недоступно.")
        return redirect("dashboard")
    if not enforce_cooldown(request, profile_obj, "pet_action"):
        return redirect("dashboard")
    required_energy = rule["requires"].get("energy", 0)
    if pet.energy < required_energy:
        messages.error(request, "Питомцу не хватает энергии. Попробуй еду или заботу из инвентаря.")
        return redirect("dashboard")
    if action == "feed" and pet.hunger >= 100:
        messages.info(request, "Питомец уже сыт.")
        return redirect("dashboard")

    pet.change_stats(energy=rule["energy"], mood=rule["mood"], hunger=rule["hunger"])
    pet.add_experience(rule["experience"])
    pet.save()
    profile_obj.coins += rule["coins"]
    profile_obj.hearts += 1
    profile_obj.save(update_fields=["coins"])
    add_quest_progress(profile_obj, rule["quest"])
    log_action(profile_obj, f"Действие с питомцем: {rule['label']} {pet.name}.", pet)
    if action == "feed":
        award_achievement(request, profile_obj, Achievement.FIRST_FEED)
    check_passive_achievements(request, profile_obj)
    profile_obj.save(update_fields=["coins", "hearts"])
    messages.success(request, f"Ты {rule['label']} {pet.name}: +{rule['experience']} опыта, +{rule['coins']} монет, +1 сердечко.")
    return redirect("dashboard")


@login_required
def shop(request):
    return render(
        request,
        "game/shop.html",
        {"profile": get_profile(request.user), "items": Item.objects.order_by("item_type", "price", "name")},
    )


@login_required
def buy_item(request, item_id):
    if request.method != "POST":
        return redirect("shop")
    profile_obj = get_profile(request.user)
    if not enforce_cooldown(request, profile_obj, "buy_item"):
        return redirect("shop")
    item = get_object_or_404(Item, id=item_id)
    if profile_obj.coins < item.price:
        messages.error(request, "Не хватает монет для покупки.")
        return redirect("shop")
    profile_obj.coins -= item.price
    profile_obj.save(update_fields=["coins"])
    inventory_item, _created = InventoryItem.objects.get_or_create(profile=profile_obj, item=item)
    inventory_item.quantity += 1
    inventory_item.save(update_fields=["quantity"])
    add_quest_progress(profile_obj, Quest.BUY)
    log_action(profile_obj, f"Куплен предмет: {item.name}.")
    award_achievement(request, profile_obj, Achievement.FIRST_BUY)
    check_passive_achievements(request, profile_obj)
    messages.success(request, f"{item.name} добавлен в инвентарь.")
    return redirect("shop")


@login_required
def inventory(request):
    profile_obj = get_profile(request.user)
    return render(
        request,
        "game/inventory.html",
        {"profile": profile_obj, "pet": active_pet(request.user), "inventory": profile_obj.inventory.select_related("item").filter(quantity__gt=0)},
    )


@login_required
def use_item(request, inventory_id):
    if request.method != "POST":
        return redirect("inventory")
    profile_obj = get_profile(request.user)
    inventory_item = get_object_or_404(InventoryItem, id=inventory_id, profile=profile_obj)
    pet = active_pet(request.user)
    if not pet:
        messages.error(request, "Сначала создай питомца.")
        return redirect("create_pet")
    if inventory_item.quantity < 1:
        messages.error(request, "Такого предмета больше нет в инвентаре.")
        return redirect("inventory")

    item = inventory_item.item
    pet.change_stats(energy=item.energy_delta, mood=item.mood_delta, hunger=item.hunger_delta)
    pet.add_experience(item.experience_delta)
    pet.beauty += item.beauty_delta
    pet.save()
    profile_obj.hearts += item.hearts_delta
    profile_obj.save(update_fields=["hearts"])
    inventory_item.quantity -= 1
    inventory_item.save(update_fields=["quantity"])
    log_action(profile_obj, f"{pet.name} использует предмет: {item.name}.", pet)
    check_passive_achievements(request, profile_obj)
    messages.success(request, f"{pet.name} использует {item.name}: эффект применен.")
    return redirect("inventory")


@login_required
def wearable_shop(request):
    profile_obj = get_profile(request.user)
    return render(
        request,
        "game/wearable_shop.html",
        {"profile": profile_obj, "wearables": WearableItem.objects.order_by("slot", "price", "name")},
    )


@login_required
def buy_wearable(request, wearable_id):
    if request.method != "POST":
        return redirect("wearable_shop")
    profile_obj = get_profile(request.user)
    if not enforce_cooldown(request, profile_obj, "buy_item"):
        return redirect("wearable_shop")
    wearable = get_object_or_404(WearableItem, id=wearable_id)
    if profile_obj.coins < wearable.price:
        messages.error(request, "Не хватает монет для покупки.")
        return redirect("wearable_shop")
    profile_obj.coins -= wearable.price
    profile_obj.save(update_fields=["coins"])
    owned, _created = OwnedWearable.objects.get_or_create(profile=profile_obj, wearable=wearable)
    if not _created:
        owned.quantity += 1
        owned.save(update_fields=["quantity"])
    log_action(profile_obj, f"Куплен предмет гардероба: {wearable.name}.")
    messages.success(request, f"{wearable.name} добавлен в гардероб.")
    return redirect("wardrobe")


@login_required
def wardrobe(request):
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    return render(
        request,
        "game/wardrobe.html",
        {
            "profile": profile_obj,
            "pet": pet,
            "owned": profile_obj.wardrobe.select_related("wearable").filter(quantity__gt=0),
            "equipped": pet.equipped_wearables.select_related("wearable") if pet else [],
        },
    )


@login_required
def equip_wearable(request, owned_id):
    if request.method != "POST":
        return redirect("wardrobe")
    profile_obj = get_profile(request.user)
    owned = get_object_or_404(OwnedWearable, id=owned_id, profile=profile_obj, quantity__gt=0)
    pet = active_pet(request.user)
    if not pet:
        messages.error(request, "Сначала создай питомца.")
        return redirect("create_pet")
    EquippedWearable.objects.filter(pet=pet, wearable__slot=owned.wearable.slot).delete()
    EquippedWearable.objects.create(pet=pet, wearable=owned.wearable)
    pet.change_stats(mood=owned.wearable.mood_bonus)
    pet.save(update_fields=["mood"])
    log_action(profile_obj, f"{pet.name} надел {owned.wearable.name}.", pet)
    messages.success(request, f"{owned.wearable.name} надет.")
    return redirect("wardrobe")


@login_required
def unequip_wearable(request, equipped_id):
    if request.method != "POST":
        return redirect("wardrobe")
    profile_obj = get_profile(request.user)
    equipped = get_object_or_404(EquippedWearable, id=equipped_id, pet__owner=request.user)
    name = equipped.wearable.name
    equipped.delete()
    log_action(profile_obj, f"Снят предмет гардероба: {name}.")
    messages.success(request, f"{name} снят.")
    return redirect("wardrobe")


@login_required
def sell_wearable(request, owned_id):
    if request.method != "POST":
        return redirect("wardrobe")
    profile_obj = get_profile(request.user)
    owned = get_object_or_404(OwnedWearable, id=owned_id, profile=profile_obj, quantity__gt=0)
    EquippedWearable.objects.filter(pet__owner=request.user, wearable=owned.wearable).delete()
    sale_price = max(1, owned.wearable.price // 2)
    profile_obj.coins += sale_price
    profile_obj.save(update_fields=["coins"])
    owned.quantity -= 1
    owned.save(update_fields=["quantity"])
    log_action(profile_obj, f"Продан предмет гардероба: {owned.wearable.name}.")
    messages.success(request, f"Продано за {sale_price} монет.")
    return redirect("wardrobe")


@login_required
def training(request):
    profile_obj = get_profile(request.user)
    return render(request, "game/training.html", {"profile": profile_obj, "pet": active_pet(request.user)})


@login_required
def train_pet(request, trait):
    if request.method != "POST":
        return redirect("training")
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    if not pet:
        messages.error(request, "Сначала создай питомца.")
        return redirect("create_pet")
    if trait not in {"agility", "obedience", "charm"}:
        messages.error(request, "Такой тренировки нет.")
        return redirect("training")
    if not enforce_cooldown(request, profile_obj, "train"):
        return redirect("training")
    if pet.energy < 12:
        messages.error(request, "Для тренировки не хватает энергии.")
        return redirect("training")
    setattr(pet, trait, getattr(pet, trait) + 1)
    pet.change_stats(energy=-12, mood=4, hunger=-4)
    pet.add_experience(7)
    pet.save()
    profile_obj.hearts += 2
    profile_obj.save(update_fields=["hearts"])
    add_quest_progress(profile_obj, Quest.TRAIN)
    log_action(profile_obj, f"{pet.name} прошел тренировку.", pet)
    messages.success(request, "Тренировка завершена: +1 к навыку, +7 опыта, +2 сердечка.")
    return redirect("training")


@login_required
def shows(request):
    profile_obj = get_profile(request.user)
    return render(
        request,
        "game/shows.html",
        {
            "profile": profile_obj,
            "pet": active_pet(request.user),
            "shows": PetShow.objects.filter(active=True).order_by("min_level", "entry_fee"),
            "entries": profile_obj.show_entries.select_related("show", "pet")[:10],
        },
    )


@login_required
def enter_show(request, show_id):
    if request.method != "POST":
        return redirect("shows")
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    show = get_object_or_404(PetShow, id=show_id, active=True)
    if not pet:
        messages.error(request, "Сначала создай питомца.")
        return redirect("create_pet")
    if not enforce_cooldown(request, profile_obj, "show"):
        return redirect("shows")
    if pet.level < show.min_level:
        messages.error(request, "Уровень питомца слишком низкий для этой выставки.")
        return redirect("shows")
    if profile_obj.coins < show.entry_fee:
        messages.error(request, "Не хватает монет на взнос.")
        return redirect("shows")
    profile_obj.coins -= show.entry_fee
    score = pet.show_power + min(20, pet.mood // 5) + min(20, pet.energy // 5)
    if score >= 80:
        medal = ShowEntry.GOLD
        multiplier = 3
    elif score >= 55:
        medal = ShowEntry.SILVER
        multiplier = 2
    else:
        medal = ShowEntry.BRONZE
        multiplier = 1
    ShowEntry.objects.create(show=show, profile=profile_obj, pet=pet, score=score, medal=medal)
    reward_coins = show.reward_coins * multiplier
    reward_hearts = show.reward_hearts * multiplier
    profile_obj.coins += reward_coins
    profile_obj.hearts += reward_hearts
    profile_obj.save(update_fields=["coins", "hearts"])
    pet.add_experience(show.reward_experience * multiplier)
    pet.change_stats(energy=-10, mood=8)
    pet.save()
    add_quest_progress(profile_obj, Quest.SHOW)
    log_action(profile_obj, f"{pet.name} выступил на выставке «{show.name}» и получил {medal}.", pet)
    messages.success(request, f"Выставка завершена: {score} очков, медаль {medal}, +{reward_coins} монет.")
    return redirect("shows")


@login_required
def quests(request):
    profile_obj = get_profile(request.user)
    return render(request, "game/quests.html", {"profile": profile_obj, "quest_progress": sync_daily_quests(profile_obj)})


@login_required
def claim_quest(request, progress_id):
    if request.method != "POST":
        return redirect("quests")
    profile_obj = get_profile(request.user)
    if not enforce_cooldown(request, profile_obj, "claim_quest"):
        return redirect("quests")
    progress = get_object_or_404(QuestProgress, id=progress_id, profile=profile_obj)
    pet = active_pet(request.user)
    if not progress.completed:
        messages.error(request, "Задание еще не выполнено.")
        return redirect("quests")
    if progress.claimed:
        messages.info(request, "Награда за это задание уже получена.")
        return redirect("quests")
    profile_obj.coins += progress.quest.reward_coins
    profile_obj.save(update_fields=["coins"])
    if pet and progress.quest.reward_experience:
        pet.add_experience(progress.quest.reward_experience)
        pet.save()
    progress.claimed = True
    progress.save(update_fields=["claimed"])
    log_action(profile_obj, f"Получена награда за задание: {progress.quest.title}.", pet)
    check_passive_achievements(request, profile_obj)
    messages.success(request, f"Награда получена: +{progress.quest.reward_coins} монет.")
    return redirect("quests")


@login_required
def social(request):
    profile_obj = get_profile(request.user)
    friends = Friendship.objects.filter(
        Q(from_profile=profile_obj) | Q(to_profile=profile_obj),
        status=Friendship.ACCEPTED,
    ).select_related("from_profile__user", "to_profile__user")
    incoming = profile_obj.received_friendships.filter(status=Friendship.PENDING).select_related("from_profile__user")
    players = PlayerProfile.objects.exclude(id=profile_obj.id).select_related("user").order_by("user__username")[:25]
    return render(
        request,
        "game/social.html",
        {"profile": profile_obj, "players": players, "friends": friends, "incoming": incoming, "online_count": online_count()},
    )


@login_required
def send_friend_request(request, profile_id):
    if request.method != "POST":
        return redirect("social")
    profile_obj = get_profile(request.user)
    target = get_object_or_404(PlayerProfile, id=profile_id)
    if target == profile_obj:
        messages.error(request, "Нельзя добавить себя.")
        return redirect("social")
    Friendship.objects.get_or_create(from_profile=profile_obj, to_profile=target)
    messages.success(request, "Заявка отправлена.")
    return redirect("social")


@login_required
def accept_friend_request(request, friendship_id):
    if request.method != "POST":
        return redirect("social")
    profile_obj = get_profile(request.user)
    friendship = get_object_or_404(Friendship, id=friendship_id, to_profile=profile_obj, status=Friendship.PENDING)
    friendship.status = Friendship.ACCEPTED
    friendship.save(update_fields=["status", "updated_at"])
    messages.success(request, "Заявка принята.")
    return redirect("social")


@login_required
def block_profile(request, profile_id):
    if request.method != "POST":
        return redirect("social")
    profile_obj = get_profile(request.user)
    target = get_object_or_404(PlayerProfile, id=profile_id)
    Friendship.objects.update_or_create(from_profile=profile_obj, to_profile=target, defaults={"status": Friendship.BLOCKED})
    messages.success(request, "Игрок заблокирован.")
    return redirect("social")


@login_required
def messages_inbox(request):
    profile_obj = get_profile(request.user)
    inbox = profile_obj.received_messages.select_related("sender__user")
    outbox = profile_obj.sent_messages.select_related("recipient__user")[:10]
    return render(request, "game/messages.html", {"profile": profile_obj, "inbox": inbox, "outbox": outbox})


@login_required
def send_message(request, profile_id):
    profile_obj = get_profile(request.user)
    target = get_object_or_404(PlayerProfile, id=profile_id)
    form = PrivateMessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not enforce_cooldown(request, profile_obj, "message"):
            return redirect("send_message", profile_id=profile_id)
        message = form.save(commit=False)
        message.sender = profile_obj
        message.recipient = target
        message.save()
        messages.success(request, "Сообщение отправлено.")
        return redirect("messages_inbox")
    return render(request, "game/send_message.html", {"profile": profile_obj, "target": target, "form": form})


@login_required
def chat(request):
    profile_obj = get_profile(request.user)
    form = ChatMessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not enforce_cooldown(request, profile_obj, "chat"):
            return redirect("chat")
        message = form.save(commit=False)
        message.profile = profile_obj
        message.save()
        messages.success(request, "Сообщение опубликовано.")
        return redirect("chat")
    return render(
        request,
        "game/chat.html",
        {
            "profile": profile_obj,
            "form": form,
            "chat_messages": ChatMessage.objects.filter(hidden=False).select_related("profile__user")[:40],
        },
    )


@login_required
def report_chat_message(request, message_id):
    profile_obj = get_profile(request.user)
    chat_message = get_object_or_404(ChatMessage, id=message_id)
    form = UserReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.reporter = profile_obj
        report.reported_profile = chat_message.profile
        report.chat_message = chat_message
        report.save()
        messages.success(request, "Жалоба отправлена модераторам.")
        return redirect("chat")
    return render(request, "game/report.html", {"form": form, "chat_message": chat_message})


@login_required
def support(request):
    profile_obj = get_profile(request.user)
    form = SupportTicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not enforce_cooldown(request, profile_obj, "support"):
            return redirect("support")
        ticket = form.save(commit=False)
        ticket.profile = profile_obj
        ticket.save()
        messages.success(request, "Обращение создано.")
        return redirect("support")
    return render(
        request,
        "game/support.html",
        {"profile": profile_obj, "form": form, "tickets": profile_obj.support_tickets.order_by("-created_at")},
    )


def rating(request):
    players = (
        User.objects.filter(profile__isnull=False)
        .annotate(best_level=Max("pets__level"), pet_count=Count("pets"))
        .select_related("profile")
        .order_by("-best_level", "-profile__coins", "username")[:30]
    )
    return render(request, "game/rating.html", {"players": players})
