from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Max, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import random

from .forms import ChatMessageForm, PetForm, PrivateMessageForm, ProfileSettingsForm, RegisterForm, SupportTicketForm, UserReportForm
from .models import (
    ActionCooldown,
    ActionLog,
    AdventureRoute,
    Achievement,
    AssistantType,
    ChestOpening,
    ChestType,
    ChatMessage,
    Club,
    ClubAnnouncement,
    ClubBuilding,
    ClubBuildingType,
    ClubContribution,
    ClubHistoryEvent,
    ClubJoinRequest,
    ClubMembership,
    CollectionPiece,
    CollectionSet,
    CompletedCollection,
    CompetitionEntry,
    CompetitionMode,
    EquippedWearable,
    ExplorationLog,
    ExplorationSite,
    ForumCategory,
    ForumPost,
    ForumThread,
    Friendship,
    FragmentType,
    FurnitureItem,
    GamePreference,
    GiftCatalogItem,
    HelpArticle,
    InventoryItem,
    Item,
    MemoryPrompt,
    OwnedCollectionPiece,
    OwnedFragment,
    OwnedFurniture,
    OwnedTrophy,
    OwnedWearable,
    Pet,
    PetAdventure,
    PetShow,
    PlayerAssistant,
    PlayerAchievement,
    PlayerProfile,
    PrivateMessage,
    Quest,
    QuestProgress,
    ShowEntry,
    SentGift,
    SupportTicket,
    Trophy,
    UserReport,
    WearableItem,
)
from .services.memories import MemoryCreationError, create_memory_chapter, memory_available_today


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
    "explore": 8,
    "assistant": 5,
    "club": 5,
    "adventure": 5,
    "competition": 5,
    "chest": 5,
    "gift": 5,
    "forum": 5,
    "memory": 5,
}


def get_profile(user):
    profile, _created = PlayerProfile.objects.get_or_create(user=user)
    profile.last_activity_at = timezone.now()
    profile.save(update_fields=["last_activity_at"])
    return profile


def get_preferences(profile):
    preferences, _created = GamePreference.objects.get_or_create(profile=profile)
    return preferences


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


def award_trophy(profile, trophy, pet=None):
    _owned, created = OwnedTrophy.objects.get_or_create(profile=profile, trophy=trophy)
    if created:
        log_action(profile, f"Trophy earned: {trophy.name}.", pet)
    return created


def award_random_fragment(profile):
    fragment_type = FragmentType.objects.order_by("?").first()
    if not fragment_type:
        return None
    owned, _created = OwnedFragment.objects.get_or_create(profile=profile, fragment_type=fragment_type)
    owned.quantity += 1
    owned.save(update_fields=["quantity"])
    return owned


def complete_ready_collections(profile):
    completed = []
    for collection in CollectionSet.objects.filter(active=True).prefetch_related("pieces"):
        if CompletedCollection.objects.filter(profile=profile, collection=collection).exists():
            continue
        pieces = list(collection.pieces.all())
        if pieces and all(OwnedCollectionPiece.objects.filter(profile=profile, piece=piece, quantity__gt=0).exists() for piece in pieces):
            CompletedCollection.objects.create(profile=profile, collection=collection)
            profile.coins += collection.reward_coins
            profile.hearts += collection.reward_hearts
            completed.append(collection)
    if completed:
        profile.save(update_fields=["coins", "hearts"])
    return completed


def assistant_bonus(profile, role):
    total = 0
    for assistant in profile.assistants.select_related("assistant_type").filter(assistant_type__role=role):
        total += assistant.bonus
    return total


def club_for_profile(profile):
    membership = profile.club_memberships.select_related("club").order_by("joined_at").first()
    return membership.club if membership else None


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
        "preferences": get_preferences(profile),
        "todays_memory": profile.memory_chapters.select_related("pet", "prompt").filter(date=timezone.localdate()).first(),
        "latest_memory": profile.memory_chapters.select_related("pet", "prompt").first(),
        "memory_prompt": MemoryPrompt.objects.filter(active=True).order_by("theme", "title").first(),
        "memory_count": profile.memory_chapters.count(),
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
def home_room(request):
    profile_obj = get_profile(request.user)
    owned = profile_obj.furniture.select_related("item").order_by("item__slot", "item__price")
    shop_items = FurnitureItem.objects.exclude(id__in=owned.values_list("item_id", flat=True)).order_by("slot", "price")
    placed = owned.filter(placed=True)
    return render(
        request,
        "game/home_room.html",
        {
            "profile": profile_obj,
            "owned": owned,
            "placed": placed,
            "shop_items": shop_items,
            "beauty_bonus": sum(item.beauty_total for item in placed),
            "xp_bonus": sum(item.xp_bonus_total for item in placed),
        },
    )


@login_required
def buy_furniture(request, item_id):
    if request.method != "POST":
        return redirect("home_room")
    profile_obj = get_profile(request.user)
    item = get_object_or_404(FurnitureItem, id=item_id)
    if profile_obj.coins < item.price:
        messages.error(request, "Not enough coins for this furniture.")
        return redirect("home_room")
    profile_obj.coins -= item.price
    profile_obj.save(update_fields=["coins"])
    owned, created = OwnedFurniture.objects.get_or_create(profile=profile_obj, item=item)
    if created and not profile_obj.furniture.filter(placed=True, item__slot=item.slot).exists():
        owned.placed = True
        owned.save(update_fields=["placed"])
    log_action(profile_obj, f"Furniture bought: {item.name}.")
    messages.success(request, f"{item.name} added to your home.")
    return redirect("home_room")


@login_required
def place_furniture(request, owned_id):
    if request.method != "POST":
        return redirect("home_room")
    profile_obj = get_profile(request.user)
    owned = get_object_or_404(OwnedFurniture.objects.select_related("item"), id=owned_id, profile=profile_obj)
    profile_obj.furniture.filter(item__slot=owned.item.slot).update(placed=False)
    owned.placed = True
    owned.save(update_fields=["placed"])
    log_action(profile_obj, f"Furniture placed: {owned.item.name}.")
    messages.success(request, f"{owned.item.name} placed in the room.")
    return redirect("home_room")


@login_required
def upgrade_furniture(request, owned_id):
    if request.method != "POST":
        return redirect("home_room")
    profile_obj = get_profile(request.user)
    owned = get_object_or_404(OwnedFurniture.objects.select_related("item"), id=owned_id, profile=profile_obj)
    if owned.level >= owned.item.max_level:
        messages.info(request, "This furniture is already fully upgraded.")
        return redirect("home_room")
    cost = owned.upgrade_cost
    if profile_obj.coins < cost:
        messages.error(request, "Not enough coins for this upgrade.")
        return redirect("home_room")
    profile_obj.coins -= cost
    profile_obj.save(update_fields=["coins"])
    owned.level += 1
    owned.save(update_fields=["level"])
    log_action(profile_obj, f"Furniture upgraded: {owned.item.name} level {owned.level}.")
    messages.success(request, f"{owned.item.name} upgraded to level {owned.level}.")
    return redirect("home_room")


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
def collections(request):
    profile_obj = get_profile(request.user)
    completed = complete_ready_collections(profile_obj)
    for collection in completed:
        messages.success(request, f"Collection completed: {collection.name}.")
        log_action(profile_obj, f"Collection completed: {collection.name}.")
    owned_map = {owned.piece_id: owned.quantity for owned in profile_obj.collection_pieces.select_related("piece")}
    completed_ids = set(profile_obj.completed_collections.values_list("collection_id", flat=True))
    collection_rows = []
    for collection in CollectionSet.objects.filter(active=True).prefetch_related("pieces").order_by("name"):
        pieces = list(collection.pieces.all())
        have = sum(1 for piece in pieces if owned_map.get(piece.id, 0) > 0)
        collection_rows.append(
            {
                "collection": collection,
                "pieces": [(piece, owned_map.get(piece.id, 0)) for piece in pieces],
                "have": have,
                "total": len(pieces),
                "completed": collection.id in completed_ids,
            }
        )
    return render(request, "game/collections.html", {"profile": profile_obj, "collection_rows": collection_rows})


@login_required
def trophies(request):
    profile_obj = get_profile(request.user)
    return render(
        request,
        "game/trophies.html",
        {
            "profile": profile_obj,
            "trophies": Trophy.objects.order_by("trophy_type", "rarity", "name"),
            "owned_ids": set(profile_obj.trophies.values_list("trophy_id", flat=True)),
            "owned": profile_obj.trophies.select_related("trophy"),
        },
    )


@login_required
def explore(request):
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    today = timezone.localdate()
    site_rows = []
    for site in ExplorationSite.objects.filter(active=True).order_by("min_level", "energy_cost"):
        used = profile_obj.explorations.filter(site=site, created_at__date=today).count()
        site_rows.append({"site": site, "used": used, "left": max(0, site.daily_limit - used)})
    return render(
        request,
        "game/explore.html",
        {
            "profile": profile_obj,
            "pet": pet,
            "site_rows": site_rows,
            "logs": profile_obj.explorations.select_related("site", "found_piece__collection", "found_trophy", "pet")[:12],
        },
    )


@login_required
def run_explore(request, site_id):
    if request.method != "POST":
        return redirect("explore")
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    site = get_object_or_404(ExplorationSite, id=site_id, active=True)
    if not pet:
        messages.error(request, "Create a pet before exploring.")
        return redirect("create_pet")
    if not enforce_cooldown(request, profile_obj, "explore"):
        return redirect("explore")
    if pet.level < site.min_level:
        messages.error(request, "Your pet level is too low for this place.")
        return redirect("explore")
    if pet.energy < site.energy_cost:
        messages.error(request, "Not enough energy for exploration.")
        return redirect("explore")
    if profile_obj.coins < site.coin_cost:
        messages.error(request, "Not enough coins for this exploration.")
        return redirect("explore")
    used = profile_obj.explorations.filter(site=site, created_at__date=timezone.localdate()).count()
    if used >= site.daily_limit:
        messages.error(request, "No attempts left for this place today.")
        return redirect("explore")

    profile_obj.coins -= site.coin_cost
    profile_obj.coins += site.reward_coins
    pet.change_stats(energy=-site.energy_cost, mood=4, hunger=-4)
    pet.add_experience(site.reward_experience)
    pieces = list(CollectionPiece.objects.select_related("collection"))
    found_piece = random.choice(pieces) if pieces else None
    found_trophy = None
    if Trophy.objects.exists() and random.randint(1, 100) <= 10 + assistant_bonus(profile_obj, AssistantType.SCOUT):
        found_trophy = Trophy.objects.order_by("?").first()
        award_trophy(profile_obj, found_trophy, pet)
    if found_piece:
        owned, _created = OwnedCollectionPiece.objects.get_or_create(profile=profile_obj, piece=found_piece)
        owned.quantity += 1
        owned.save(update_fields=["quantity"])
    profile_obj.save(update_fields=["coins"])
    pet.save()
    ExplorationLog.objects.create(profile=profile_obj, pet=pet, site=site, found_piece=found_piece, found_trophy=found_trophy)
    completed = complete_ready_collections(profile_obj)
    if found_piece:
        messages.success(request, f"Found collection piece: {found_piece.name}.")
    if found_trophy:
        messages.success(request, f"Found trophy: {found_trophy.name}.")
    for collection in completed:
        messages.success(request, f"Collection completed: {collection.name}.")
    log_action(profile_obj, f"{pet.name} explored {site.name}.", pet)
    return redirect("explore")


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
def assistants(request):
    profile_obj = get_profile(request.user)
    rows = []
    for assistant_type in AssistantType.objects.order_by("role", "name"):
        assistant, _created = PlayerAssistant.objects.get_or_create(profile=profile_obj, assistant_type=assistant_type)
        rows.append(assistant)
    return render(request, "game/assistants.html", {"profile": profile_obj, "assistants": rows})


@login_required
def train_assistant(request, assistant_id):
    if request.method != "POST":
        return redirect("assistants")
    profile_obj = get_profile(request.user)
    assistant = get_object_or_404(PlayerAssistant.objects.select_related("assistant_type"), id=assistant_id, profile=profile_obj)
    if not enforce_cooldown(request, profile_obj, "assistant"):
        return redirect("assistants")
    if assistant.level >= assistant.assistant_type.max_level:
        messages.info(request, "This assistant is already at max level.")
        return redirect("assistants")
    cost = assistant.train_cost
    if profile_obj.hearts < cost:
        messages.error(request, "Not enough hearts for assistant training.")
        return redirect("assistants")
    profile_obj.hearts -= cost
    profile_obj.save(update_fields=["hearts"])
    assistant.level += 1
    assistant.save(update_fields=["level"])
    log_action(profile_obj, f"Assistant trained: {assistant.assistant_type.name} level {assistant.level}.")
    messages.success(request, f"{assistant.assistant_type.name} is now level {assistant.level}.")
    return redirect("assistants")


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
    trophy = Trophy.objects.filter(source__iexact=show.name, trophy_type=medal).first() or Trophy.objects.filter(trophy_type=medal).first()
    if trophy:
        award_trophy(profile_obj, trophy, pet)
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
def memory_trail(request):
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    today = timezone.localdate()
    prompts = MemoryPrompt.objects.filter(active=True).order_by("theme", "title")
    chapters = profile_obj.memory_chapters.select_related("pet", "prompt")[:12]
    return render(
        request,
        "game/memory_trail.html",
        {
            "profile": profile_obj,
            "pet": pet,
            "prompts": prompts,
            "chapters": chapters,
            "todays_memory": profile_obj.memory_chapters.select_related("pet", "prompt").filter(date=today).first(),
            "available_today": memory_available_today(profile_obj),
        },
    )


@login_required
def create_memory(request, prompt_id):
    if request.method != "POST":
        return redirect("memory_trail")
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    prompt = get_object_or_404(MemoryPrompt, id=prompt_id, active=True)
    if not pet:
        messages.error(request, "Сначала создай питомца.")
        return redirect("create_pet")
    if not enforce_cooldown(request, profile_obj, "memory"):
        return redirect("memory_trail")
    try:
        chapter = create_memory_chapter(
            profile=profile_obj,
            pet=pet,
            prompt=prompt,
            boosted=bool(request.POST.get("boosted")),
        )
    except MemoryCreationError as exc:
        messages.error(request, str(exc))
        return redirect("memory_trail")

    add_quest_progress(profile_obj, Quest.MEMORY)
    log_action(profile_obj, f"Создана глава памяти «{chapter.title}».", pet)
    check_passive_achievements(request, profile_obj)
    messages.success(
        request,
        f"Глава создана: +{chapter.reward_coins} монет, +{chapter.reward_hearts} сердечек, +{chapter.bond_delta} связи.",
    )
    return redirect("memory_trail")


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


@login_required
def clubs(request):
    profile_obj = get_profile(request.user)
    current_club = club_for_profile(profile_obj)
    return render(
        request,
        "game/clubs.html",
        {
            "profile": profile_obj,
            "current_club": current_club,
            "membership": profile_obj.club_memberships.select_related("club").first(),
            "clubs": Club.objects.annotate(member_count=Count("memberships")).order_by("-level", "name"),
            "requests": profile_obj.club_join_requests.select_related("club").order_by("-created_at")[:8],
        },
    )


@login_required
def create_club(request):
    if request.method != "POST":
        return redirect("clubs")
    profile_obj = get_profile(request.user)
    if club_for_profile(profile_obj):
        messages.error(request, "You are already in a club.")
        return redirect("clubs")
    if profile_obj.coins < 250:
        messages.error(request, "Creating a club costs 250 coins.")
        return redirect("clubs")
    name = request.POST.get("name", "").strip()[:80]
    description = request.POST.get("description", "").strip()[:180]
    if len(name) < 3:
        messages.error(request, "Club name must be at least 3 characters.")
        return redirect("clubs")
    if Club.objects.filter(name__iexact=name).exists():
        messages.error(request, "A club with this name already exists.")
        return redirect("clubs")
    profile_obj.coins -= 250
    profile_obj.save(update_fields=["coins"])
    club = Club.objects.create(name=name, description=description)
    ClubMembership.objects.create(club=club, profile=profile_obj, role=ClubMembership.OWNER)
    for building_type in ClubBuildingType.objects.all():
        ClubBuilding.objects.get_or_create(club=club, building_type=building_type)
    ClubHistoryEvent.objects.create(club=club, actor=profile_obj, text=f"{profile_obj.public_name} founded the club.")
    messages.success(request, f"Club created: {club.name}.")
    return redirect("club_detail", club_id=club.id)


@login_required
def club_detail(request, club_id):
    profile_obj = get_profile(request.user)
    club = get_object_or_404(Club.objects.annotate(member_count=Count("memberships")), id=club_id)
    membership = ClubMembership.objects.filter(club=club, profile=profile_obj).first()
    return render(
        request,
        "game/club_detail.html",
        {
            "profile": profile_obj,
            "club": club,
            "membership": membership,
            "members": club.memberships.select_related("profile__user").order_by("role", "-contribution_score"),
            "buildings": club.buildings.select_related("building_type").order_by("building_type__effect", "building_type__name"),
            "history": club.history.select_related("actor__user")[:12],
            "announcements": club.announcements.select_related("author__user")[:5],
            "join_requests": club.join_requests.filter(status=ClubJoinRequest.PENDING).select_related("profile__user")[:10],
        },
    )


@login_required
def request_club_join(request, club_id):
    if request.method != "POST":
        return redirect("club_detail", club_id=club_id)
    profile_obj = get_profile(request.user)
    club = get_object_or_404(Club, id=club_id)
    if club_for_profile(profile_obj):
        messages.error(request, "You are already in a club.")
        return redirect("club_detail", club_id=club_id)
    ClubJoinRequest.objects.get_or_create(
        club=club,
        profile=profile_obj,
        status=ClubJoinRequest.PENDING,
        defaults={"message": request.POST.get("message", "")[:160]},
    )
    messages.success(request, "Join request sent.")
    return redirect("club_detail", club_id=club_id)


@login_required
def accept_club_join(request, request_id):
    if request.method != "POST":
        return redirect("clubs")
    profile_obj = get_profile(request.user)
    join_request = get_object_or_404(ClubJoinRequest.objects.select_related("club", "profile"), id=request_id, status=ClubJoinRequest.PENDING)
    membership = ClubMembership.objects.filter(club=join_request.club, profile=profile_obj, role__in=[ClubMembership.OWNER, ClubMembership.DEPUTY]).first()
    if not membership:
        messages.error(request, "Only club leaders can accept requests.")
        return redirect("club_detail", club_id=join_request.club.id)
    if join_request.club.memberships.count() >= join_request.club.member_limit:
        messages.error(request, "The club is full.")
        return redirect("club_detail", club_id=join_request.club.id)
    if club_for_profile(join_request.profile):
        join_request.status = ClubJoinRequest.DECLINED
        join_request.save(update_fields=["status"])
        messages.error(request, "This player already joined another club.")
        return redirect("club_detail", club_id=join_request.club.id)
    ClubMembership.objects.create(club=join_request.club, profile=join_request.profile)
    join_request.status = ClubJoinRequest.ACCEPTED
    join_request.save(update_fields=["status"])
    ClubHistoryEvent.objects.create(club=join_request.club, actor=profile_obj, text=f"{join_request.profile.public_name} joined the club.")
    messages.success(request, "Join request accepted.")
    return redirect("club_detail", club_id=join_request.club.id)


@login_required
def contribute_club(request, club_id):
    if request.method != "POST":
        return redirect("club_detail", club_id=club_id)
    profile_obj = get_profile(request.user)
    club = get_object_or_404(Club, id=club_id)
    membership = get_object_or_404(ClubMembership, club=club, profile=profile_obj)
    coins = max(0, int(request.POST.get("coins") or 0))
    hearts = max(0, int(request.POST.get("hearts") or 0))
    if coins == 0 and hearts == 0:
        messages.error(request, "Choose coins or hearts to contribute.")
        return redirect("club_detail", club_id=club.id)
    if profile_obj.coins < coins or profile_obj.hearts < hearts:
        messages.error(request, "Not enough resources for this contribution.")
        return redirect("club_detail", club_id=club.id)
    profile_obj.coins -= coins
    profile_obj.hearts -= hearts
    profile_obj.save(update_fields=["coins", "hearts"])
    club.coins += coins
    club.hearts += hearts
    club.experience += coins + hearts
    while club.experience >= club.level * 500:
        club.experience -= club.level * 500
        club.level += 1
        club.member_limit += 2
    club.save(update_fields=["coins", "hearts", "experience", "level", "member_limit"])
    membership.contribution_score += coins + hearts
    membership.save(update_fields=["contribution_score"])
    ClubContribution.objects.create(club=club, profile=profile_obj, coins=coins, hearts=hearts)
    ClubHistoryEvent.objects.create(club=club, actor=profile_obj, text=f"{profile_obj.public_name} contributed to the club.")
    messages.success(request, "Contribution added to club treasury.")
    return redirect("club_detail", club_id=club.id)


@login_required
def upgrade_club_building(request, building_id):
    if request.method != "POST":
        return redirect("clubs")
    profile_obj = get_profile(request.user)
    building = get_object_or_404(ClubBuilding.objects.select_related("club", "building_type"), id=building_id)
    membership = ClubMembership.objects.filter(club=building.club, profile=profile_obj, role__in=[ClubMembership.OWNER, ClubMembership.DEPUTY]).first()
    if not membership:
        messages.error(request, "Only club leaders can upgrade buildings.")
        return redirect("club_detail", club_id=building.club.id)
    if building.level >= building.building_type.max_level:
        messages.info(request, "This building is already max level.")
        return redirect("club_detail", club_id=building.club.id)
    cost = building.upgrade_cost
    if building.club.coins < cost:
        messages.error(request, "Club treasury does not have enough coins.")
        return redirect("club_detail", club_id=building.club.id)
    building.club.coins -= cost
    building.club.save(update_fields=["coins"])
    building.level += 1
    building.save(update_fields=["level"])
    ClubHistoryEvent.objects.create(club=building.club, actor=profile_obj, text=f"{building.building_type.name} upgraded to level {building.level}.")
    messages.success(request, f"{building.building_type.name} upgraded.")
    return redirect("club_detail", club_id=building.club.id)


@login_required
def post_club_announcement(request, club_id):
    if request.method != "POST":
        return redirect("club_detail", club_id=club_id)
    profile_obj = get_profile(request.user)
    club = get_object_or_404(Club, id=club_id)
    membership = ClubMembership.objects.filter(club=club, profile=profile_obj, role__in=[ClubMembership.OWNER, ClubMembership.DEPUTY, ClubMembership.OFFICER]).first()
    if not membership:
        messages.error(request, "Only club officers can post announcements.")
        return redirect("club_detail", club_id=club.id)
    body = request.POST.get("body", "").strip()[:240]
    if not body:
        messages.error(request, "Announcement cannot be empty.")
        return redirect("club_detail", club_id=club.id)
    ClubAnnouncement.objects.create(club=club, author=profile_obj, body=body)
    ClubHistoryEvent.objects.create(club=club, actor=profile_obj, text="Club announcement posted.")
    messages.success(request, "Announcement posted.")
    return redirect("club_detail", club_id=club.id)


@login_required
def fragments(request):
    profile_obj = get_profile(request.user)
    owned_map = {owned.fragment_type_id: owned for owned in profile_obj.fragments.select_related("fragment_type")}
    rows = []
    for fragment_type in FragmentType.objects.order_by("kind", "name"):
        owned = owned_map.get(fragment_type.id)
        rows.append(
            {
                "fragment_type": fragment_type,
                "owned": owned,
                "quantity": owned.quantity if owned else 0,
                "completed_count": owned.completed_count if owned else 0,
                "progress": min(100, round(((owned.quantity if owned else 0) / fragment_type.required_fragments) * 100)),
            }
        )
    return render(request, "game/fragments.html", {"profile": profile_obj, "rows": rows})


@login_required
def craft_fragment(request, fragment_id):
    if request.method != "POST":
        return redirect("fragments")
    profile_obj = get_profile(request.user)
    owned = get_object_or_404(OwnedFragment.objects.select_related("fragment_type"), id=fragment_id, profile=profile_obj)
    required = owned.fragment_type.required_fragments
    if owned.quantity < required:
        messages.error(request, "Not enough fragments to complete this keepsake.")
        return redirect("fragments")
    owned.quantity -= required
    owned.completed_count += 1
    owned.save(update_fields=["quantity", "completed_count"])
    log_action(profile_obj, f"Completed fragment keepsake: {owned.fragment_type.name}.")
    messages.success(request, f"{owned.fragment_type.name} completed. Permanent beauty +{owned.fragment_type.beauty_bonus}.")
    return redirect("fragments")


@login_required
def adventures(request):
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    return render(
        request,
        "game/adventures.html",
        {
            "profile": profile_obj,
            "pet": pet,
            "routes": AdventureRoute.objects.filter(active=True).order_by("min_level", "duration_minutes"),
            "active_adventures": profile_obj.adventures.filter(completed=False).select_related("route", "pet"),
            "history": profile_obj.adventures.filter(completed=True).select_related("route", "pet")[:12],
        },
    )


@login_required
def start_adventure(request, route_id):
    if request.method != "POST":
        return redirect("adventures")
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    route = get_object_or_404(AdventureRoute, id=route_id, active=True)
    if not pet:
        messages.error(request, "Create a pet before starting adventures.")
        return redirect("create_pet")
    if not enforce_cooldown(request, profile_obj, "adventure"):
        return redirect("adventures")
    if PetAdventure.objects.filter(profile=profile_obj, pet=pet, completed=False).exists():
        messages.error(request, f"{pet.name} is already on an adventure.")
        return redirect("adventures")
    if pet.level < route.min_level:
        messages.error(request, "Your pet level is too low for this adventure.")
        return redirect("adventures")
    if pet.energy < route.energy_cost:
        messages.error(request, "Not enough energy for this adventure.")
        return redirect("adventures")
    pet.change_stats(energy=-route.energy_cost, mood=2, hunger=-3)
    pet.save()
    finishes_at = timezone.now() + timezone.timedelta(minutes=route.duration_minutes)
    PetAdventure.objects.create(profile=profile_obj, pet=pet, route=route, finishes_at=finishes_at)
    log_action(profile_obj, f"{pet.name} started adventure: {route.name}.", pet)
    messages.success(request, f"{pet.name} started {route.name}.")
    return redirect("adventures")


@login_required
def finish_adventure(request, adventure_id):
    if request.method != "POST":
        return redirect("adventures")
    profile_obj = get_profile(request.user)
    adventure = get_object_or_404(PetAdventure.objects.select_related("route", "pet"), id=adventure_id, profile=profile_obj, completed=False)
    if not adventure.is_ready:
        messages.error(request, "This adventure is still in progress.")
        return redirect("adventures")
    route = adventure.route
    pet = adventure.pet
    profile_obj.coins += route.reward_coins
    profile_obj.hearts += route.reward_hearts
    pet.add_experience(route.reward_experience)
    pet.change_stats(mood=8, hunger=-2)
    fragment = award_random_fragment(profile_obj)
    adventure.completed = True
    profile_obj.save(update_fields=["coins", "hearts"])
    pet.save()
    adventure.save(update_fields=["completed"])
    reward_note = f", fragment {fragment.fragment_type.name}" if fragment else ""
    log_action(profile_obj, f"{pet.name} completed adventure: {route.name}{reward_note}.", pet)
    messages.success(request, f"Adventure complete: +{route.reward_coins} coins, +{route.reward_hearts} hearts{reward_note}.")
    return redirect("adventures")


@login_required
def competitions(request):
    profile_obj = get_profile(request.user)
    return render(
        request,
        "game/competitions.html",
        {
            "profile": profile_obj,
            "pet": active_pet(request.user),
            "modes": CompetitionMode.objects.filter(active=True).order_by("min_level", "entry_fee"),
            "entries": profile_obj.competition_entries.select_related("mode", "pet")[:12],
            "leaders": CompetitionEntry.objects.select_related("profile__user", "pet", "mode")[:20],
        },
    )


@login_required
def enter_competition(request, mode_id):
    if request.method != "POST":
        return redirect("competitions")
    profile_obj = get_profile(request.user)
    pet = active_pet(request.user)
    mode = get_object_or_404(CompetitionMode, id=mode_id, active=True)
    if not pet:
        messages.error(request, "Create a pet before entering competitions.")
        return redirect("create_pet")
    if not enforce_cooldown(request, profile_obj, "competition"):
        return redirect("competitions")
    if pet.level < mode.min_level:
        messages.error(request, "Your pet level is too low for this competition.")
        return redirect("competitions")
    if profile_obj.coins < mode.entry_fee:
        messages.error(request, "Not enough coins for the entry fee.")
        return redirect("competitions")
    if pet.energy < 8:
        messages.error(request, "Not enough energy for competition.")
        return redirect("competitions")
    base_stat = pet.mood if mode.stat == CompetitionMode.MOOD else getattr(pet, mode.stat)
    score = base_stat * 4 + pet.level * 9 + pet.beauty + profile_obj.passive_beauty_bonus + random.randint(1, 18)
    league = "Diamond" if score >= 120 else "Gold" if score >= 90 else "Silver" if score >= 60 else "Sprout"
    profile_obj.coins -= mode.entry_fee
    profile_obj.coins += mode.reward_coins
    profile_obj.hearts += mode.reward_hearts
    pet.change_stats(energy=-8, mood=5, hunger=-4)
    pet.add_experience(10)
    profile_obj.save(update_fields=["coins", "hearts"])
    pet.save()
    CompetitionEntry.objects.create(mode=mode, profile=profile_obj, pet=pet, score=score, league=league)
    add_quest_progress(profile_obj, Quest.SHOW)
    log_action(profile_obj, f"{pet.name} entered {mode.name} and reached {league} league.", pet)
    messages.success(request, f"Competition complete: {score} points, {league} league.")
    return redirect("competitions")


@login_required
def chests(request):
    profile_obj = get_profile(request.user)
    today = timezone.localdate()
    rows = []
    for chest in ChestType.objects.order_by("key_cost", "name"):
        used = profile_obj.chest_openings.filter(chest_type=chest, created_at__date=today).count()
        rows.append({"chest": chest, "used": used, "left": max(0, chest.daily_limit - used)})
    return render(request, "game/chests.html", {"profile": profile_obj, "rows": rows, "openings": profile_obj.chest_openings.select_related("chest_type")[:12]})


@login_required
def open_chest(request, chest_id):
    if request.method != "POST":
        return redirect("chests")
    profile_obj = get_profile(request.user)
    chest = get_object_or_404(ChestType, id=chest_id)
    if not enforce_cooldown(request, profile_obj, "chest"):
        return redirect("chests")
    used = profile_obj.chest_openings.filter(chest_type=chest, created_at__date=timezone.localdate()).count()
    if used >= chest.daily_limit:
        messages.error(request, "Daily limit for this chest is reached.")
        return redirect("chests")
    if profile_obj.hearts < chest.key_cost:
        messages.error(request, "Not enough hearts to open this chest.")
        return redirect("chests")
    coins = random.randint(chest.min_coins, chest.max_coins)
    hearts = random.randint(0, 2)
    profile_obj.hearts -= chest.key_cost
    profile_obj.coins += coins
    profile_obj.hearts += hearts
    fragment = award_random_fragment(profile_obj)
    reward_text = f"+{coins} coins, +{hearts} hearts" + (f", {fragment.fragment_type.name} fragment" if fragment else "")
    profile_obj.save(update_fields=["coins", "hearts"])
    ChestOpening.objects.create(profile=profile_obj, chest_type=chest, reward_text=reward_text, coins=coins, hearts=hearts)
    log_action(profile_obj, f"Opened chest {chest.name}: {reward_text}.")
    messages.success(request, f"Chest opened: {reward_text}.")
    return redirect("chests")


@login_required
def gifts(request):
    profile_obj = get_profile(request.user)
    players = PlayerProfile.objects.exclude(id=profile_obj.id).select_related("user").order_by("user__username")[:25]
    return render(
        request,
        "game/gifts.html",
        {
            "profile": profile_obj,
            "gifts": GiftCatalogItem.objects.order_by("price_hearts", "name"),
            "players": players,
            "sent": profile_obj.sent_gifts.select_related("recipient__user", "gift")[:10],
            "received": profile_obj.received_gifts.select_related("sender__user", "gift")[:10],
        },
    )


@login_required
def send_gift(request, gift_id, profile_id):
    if request.method != "POST":
        return redirect("gifts")
    profile_obj = get_profile(request.user)
    gift = get_object_or_404(GiftCatalogItem, id=gift_id)
    recipient = get_object_or_404(PlayerProfile, id=profile_id)
    if recipient == profile_obj:
        messages.error(request, "You cannot send a gift to yourself.")
        return redirect("gifts")
    if not enforce_cooldown(request, profile_obj, "gift"):
        return redirect("gifts")
    if profile_obj.hearts < gift.price_hearts:
        messages.error(request, "Not enough hearts for this gift.")
        return redirect("gifts")
    message = request.POST.get("message", "").strip()[:160]
    profile_obj.hearts -= gift.price_hearts
    profile_obj.save(update_fields=["hearts"])
    SentGift.objects.create(sender=profile_obj, recipient=recipient, gift=gift, message=message)
    log_action(profile_obj, f"Sent gift {gift.name} to {recipient.public_name}.")
    messages.success(request, f"Gift sent to {recipient.public_name}.")
    return redirect("gifts")


@login_required
def forum(request):
    profile_obj = get_profile(request.user)
    return render(
        request,
        "game/forum.html",
        {
            "profile": profile_obj,
            "categories": ForumCategory.objects.annotate(thread_count=Count("threads")).order_by("-is_news", "name"),
            "recent_threads": ForumThread.objects.select_related("category", "author__user")[:10],
        },
    )


@login_required
def forum_category(request, category_id):
    profile_obj = get_profile(request.user)
    category = get_object_or_404(ForumCategory, id=category_id)
    return render(
        request,
        "game/forum_category.html",
        {
            "profile": profile_obj,
            "category": category,
            "threads": category.threads.select_related("author__user").annotate(post_count=Count("posts")),
        },
    )


@login_required
def create_forum_thread(request, category_id):
    if request.method != "POST":
        return redirect("forum_category", category_id=category_id)
    profile_obj = get_profile(request.user)
    category = get_object_or_404(ForumCategory, id=category_id)
    if not enforce_cooldown(request, profile_obj, "forum"):
        return redirect("forum_category", category_id=category.id)
    title = request.POST.get("title", "").strip()[:120]
    body = request.POST.get("body", "").strip()[:1200]
    if len(title) < 3 or len(body) < 3:
        messages.error(request, "Thread title and text must be filled.")
        return redirect("forum_category", category_id=category.id)
    thread = ForumThread.objects.create(category=category, author=profile_obj, title=title)
    ForumPost.objects.create(thread=thread, author=profile_obj, body=body)
    messages.success(request, "Thread created.")
    return redirect("forum_thread", thread_id=thread.id)


@login_required
def forum_thread(request, thread_id):
    profile_obj = get_profile(request.user)
    thread = get_object_or_404(ForumThread.objects.select_related("category", "author__user"), id=thread_id)
    return render(request, "game/forum_thread.html", {"profile": profile_obj, "thread": thread, "posts": thread.posts.filter(hidden=False).select_related("author__user")})


@login_required
def reply_forum_thread(request, thread_id):
    if request.method != "POST":
        return redirect("forum_thread", thread_id=thread_id)
    profile_obj = get_profile(request.user)
    thread = get_object_or_404(ForumThread, id=thread_id)
    if thread.locked:
        messages.error(request, "This thread is locked.")
        return redirect("forum_thread", thread_id=thread.id)
    if not enforce_cooldown(request, profile_obj, "forum"):
        return redirect("forum_thread", thread_id=thread.id)
    body = request.POST.get("body", "").strip()[:1200]
    if len(body) < 2:
        messages.error(request, "Reply cannot be empty.")
        return redirect("forum_thread", thread_id=thread.id)
    ForumPost.objects.create(thread=thread, author=profile_obj, body=body)
    thread.save(update_fields=["updated_at"])
    messages.success(request, "Reply posted.")
    return redirect("forum_thread", thread_id=thread.id)


@login_required
def help_center(request):
    profile_obj = get_profile(request.user)
    articles = HelpArticle.objects.filter(active=True).order_by("category", "title")
    return render(request, "game/help_center.html", {"profile": profile_obj, "articles": articles})


@login_required
def game_settings(request):
    profile_obj = get_profile(request.user)
    preferences = get_preferences(profile_obj)
    if request.method == "POST":
        preferences.compact_mode = bool(request.POST.get("compact_mode"))
        preferences.show_bottom_nav = bool(request.POST.get("show_bottom_nav"))
        preferences.show_quick_actions = bool(request.POST.get("show_quick_actions"))
        preferences.reduced_motion = bool(request.POST.get("reduced_motion"))
        preferences.low_bandwidth = bool(request.POST.get("low_bandwidth"))
        preferences.save()
        messages.success(request, "Game settings saved.")
        return redirect("game_settings")
    return render(request, "game/game_settings.html", {"profile": profile_obj, "preferences": preferences})


def rating(request):
    players = (
        User.objects.filter(profile__isnull=False)
        .annotate(best_level=Max("pets__level"), pet_count=Count("pets"))
        .select_related("profile")
        .order_by("-best_level", "-profile__coins", "username")[:30]
    )
    return render(request, "game/rating.html", {"players": players})
