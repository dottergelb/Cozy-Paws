from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Max, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import PetForm, ProfileSettingsForm, RegisterForm
from .models import ActionLog, Achievement, InventoryItem, Item, Pet, PlayerAchievement, PlayerProfile, Quest, QuestProgress


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


def get_profile(user):
    profile, _created = PlayerProfile.objects.get_or_create(user=user)
    return profile


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
            "achievements": profile_obj.achievements.select_related("achievement"),
            "logs": profile_obj.logs.select_related("pet")[:12],
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
    profile_obj.save(update_fields=["coins"])
    add_quest_progress(profile_obj, rule["quest"])
    log_action(profile_obj, f"Действие с питомцем: {rule['label']} {pet.name}.", pet)
    if action == "feed":
        award_achievement(request, profile_obj, Achievement.FIRST_FEED)
    check_passive_achievements(request, profile_obj)
    messages.success(request, f"Ты {rule['label']} {pet.name}: +{rule['experience']} опыта, +{rule['coins']} монет.")
    return redirect("dashboard")


@login_required
def shop(request):
    return render(request, "game/shop.html", {"profile": get_profile(request.user), "items": Item.objects.order_by("price", "name")})


@login_required
def buy_item(request, item_id):
    if request.method != "POST":
        return redirect("shop")
    profile_obj = get_profile(request.user)
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
    pet.save()
    inventory_item.quantity -= 1
    inventory_item.save(update_fields=["quantity"])
    log_action(profile_obj, f"{pet.name} использует предмет: {item.name}.", pet)
    check_passive_achievements(request, profile_obj)
    messages.success(request, f"{pet.name} использует {item.name}: эффект применен.")
    return redirect("inventory")


@login_required
def quests(request):
    profile_obj = get_profile(request.user)
    return render(request, "game/quests.html", {"profile": profile_obj, "quest_progress": sync_daily_quests(profile_obj)})


@login_required
def claim_quest(request, progress_id):
    if request.method != "POST":
        return redirect("quests")
    profile_obj = get_profile(request.user)
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


def rating(request):
    players = (
        User.objects.filter(profile__isnull=False)
        .annotate(best_level=Max("pets__level"), pet_count=Count("pets"))
        .select_related("profile")
        .order_by("-best_level", "-profile__coins", "username")[:30]
    )
    return render(request, "game/rating.html", {"players": players})
