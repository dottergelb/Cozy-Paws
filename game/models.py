from django.conf import settings
from django.db import models
from django.utils import timezone


class PlayerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=40, blank=True)
    bio = models.CharField(max_length=160, blank=True)
    coins = models.PositiveIntegerField(default=120)
    hearts = models.PositiveIntegerField(default=0)
    last_energy_tick = models.DateTimeField(default=timezone.now)
    last_activity_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    @property
    def total_pet_levels(self):
        return sum(pet.level for pet in self.user.pets.all())

    @property
    def public_name(self):
        return self.display_name or self.user.username

    @property
    def passive_beauty_bonus(self):
        furniture = sum(piece.beauty_total for piece in self.furniture.select_related("item").filter(placed=True))
        trophies = self.trophies.aggregate(total=models.Sum("trophy__beauty_bonus"))["total"] or 0
        collections = self.completed_collections.aggregate(total=models.Sum("collection__beauty_bonus"))["total"] or 0
        return furniture + trophies + collections


class Pet(models.Model):
    CAT = "cat"
    DOG = "dog"
    BUNNY = "bunny"
    FOX = "fox"
    SPECIES_CHOICES = [
        (CAT, "Котенок"),
        (DOG, "Щенок"),
        (BUNNY, "Кролик"),
        (FOX, "Лисенок"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField(max_length=40)
    species = models.CharField(max_length=16, choices=SPECIES_CHOICES, default=CAT)
    level = models.PositiveIntegerField(default=1)
    experience = models.PositiveIntegerField(default=0)
    energy = models.PositiveIntegerField(default=80)
    mood = models.PositiveIntegerField(default=80)
    hunger = models.PositiveIntegerField(default=70)
    beauty = models.PositiveIntegerField(default=5)
    agility = models.PositiveIntegerField(default=1)
    obedience = models.PositiveIntegerField(default=1)
    charm = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

    @property
    def next_level_experience(self):
        return 60 + (self.level - 1) * 35

    @property
    def experience_percent(self):
        return min(100, round(self.experience / self.next_level_experience * 100))

    def add_experience(self, amount):
        self.experience += max(0, amount)
        while self.experience >= self.next_level_experience:
            self.experience -= self.next_level_experience
            self.level += 1
            self.energy = min(100, self.energy + 18)
            self.mood = min(100, self.mood + 12)

    def change_stats(self, *, energy=0, mood=0, hunger=0):
        self.energy = min(100, max(0, self.energy + energy))
        self.mood = min(100, max(0, self.mood + mood))
        self.hunger = min(100, max(0, self.hunger + hunger))

    @property
    def equipped_beauty_bonus(self):
        total = self.equipped_wearables.select_related("wearable").aggregate(total=models.Sum("wearable__beauty_bonus"))["total"]
        return total or 0

    @property
    def show_power(self):
        profile = getattr(self.owner, "profile", None)
        profile_bonus = profile.passive_beauty_bonus if profile else 0
        return self.level * 8 + self.beauty + self.equipped_beauty_bonus + profile_bonus + self.agility + self.obedience + self.charm


class Item(models.Model):
    FOOD = "food"
    TOY = "toy"
    CARE = "care"
    ITEM_TYPES = [
        (FOOD, "Еда"),
        (TOY, "Игрушка"),
        (CARE, "Уход"),
    ]

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    item_type = models.CharField(max_length=16, choices=ITEM_TYPES)
    price = models.PositiveIntegerField()
    energy_delta = models.IntegerField(default=0)
    mood_delta = models.IntegerField(default=0)
    hunger_delta = models.IntegerField(default=0)
    experience_delta = models.PositiveIntegerField(default=0)
    beauty_delta = models.PositiveIntegerField(default=0)
    hearts_delta = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=24, default="spark")

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="inventory")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("profile", "item")

    def __str__(self):
        return f"{self.profile}: {self.item} x{self.quantity}"


class WearableItem(models.Model):
    OUTFIT = "outfit"
    COLLAR = "collar"
    HAT = "hat"
    CHARM = "charm"
    BACKGROUND = "background"
    SLOT_CHOICES = [
        (OUTFIT, "Наряд"),
        (COLLAR, "Ошейник"),
        (HAT, "Шапка"),
        (CHARM, "Талисман"),
        (BACKGROUND, "Фон"),
    ]

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    price = models.PositiveIntegerField()
    beauty_bonus = models.PositiveIntegerField(default=0)
    mood_bonus = models.PositiveIntegerField(default=0)
    show_bonus = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=16, default="#45b08c")

    def __str__(self):
        return self.name


class OwnedWearable(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="wardrobe")
    wearable = models.ForeignKey(WearableItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "wearable")

    def __str__(self):
        return f"{self.profile}: {self.wearable} x{self.quantity}"


class EquippedWearable(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="equipped_wearables")
    wearable = models.ForeignKey(WearableItem, on_delete=models.CASCADE)
    equipped_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("pet", "wearable")

    def __str__(self):
        return f"{self.pet}: {self.wearable}"


class Quest(models.Model):
    FEED = "feed"
    PLAY = "play"
    PET = "pet"
    WALK = "walk"
    BUY = "buy"
    TRAIN = "train"
    SHOW = "show"
    ACTION_CHOICES = [
        (FEED, "Покормить"),
        (PLAY, "Поиграть"),
        (PET, "Погладить"),
        (WALK, "Прогулка"),
        (BUY, "Покупка"),
        (TRAIN, "Тренировка"),
        (SHOW, "Выставка"),
    ]

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=220)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    target_count = models.PositiveIntegerField(default=1)
    reward_coins = models.PositiveIntegerField(default=0)
    reward_experience = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class QuestProgress(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="quest_progress")
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    count = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    claimed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("profile", "quest", "date")

    def __str__(self):
        return f"{self.profile} - {self.quest} ({self.date})"

    @property
    def percent(self):
        return min(100, round(self.count / self.quest.target_count * 100))


class Achievement(models.Model):
    FIRST_FEED = "first_feed"
    FIRST_BUY = "first_buy"
    LEVEL_3 = "level_3"
    THREE_PETS = "three_pets"
    RICH = "rich"
    CODES = [
        (FIRST_FEED, "Первое кормление"),
        (FIRST_BUY, "Первая покупка"),
        (LEVEL_3, "Уровень 3"),
        (THREE_PETS, "Команда питомцев"),
        (RICH, "Копилка"),
    ]

    code = models.CharField(max_length=32, choices=CODES, unique=True)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=180)
    reward_coins = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class PlayerAchievement(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "achievement")

    def __str__(self):
        return f"{self.profile} - {self.achievement}"


class ActionLog(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="logs")
    pet = models.ForeignKey(Pet, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text


class ActionCooldown(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="cooldowns")
    key = models.CharField(max_length=40)
    available_at = models.DateTimeField()

    class Meta:
        unique_together = ("profile", "key")

    def __str__(self):
        return f"{self.profile}: {self.key} until {self.available_at}"


class PetShow(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=220)
    min_level = models.PositiveIntegerField(default=1)
    entry_fee = models.PositiveIntegerField(default=0)
    reward_coins = models.PositiveIntegerField(default=0)
    reward_hearts = models.PositiveIntegerField(default=0)
    reward_experience = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ShowEntry(models.Model):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    MEDAL_CHOICES = [(BRONZE, "Бронза"), (SILVER, "Серебро"), (GOLD, "Золото")]

    show = models.ForeignKey(PetShow, on_delete=models.CASCADE, related_name="entries")
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="show_entries")
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="show_entries")
    score = models.PositiveIntegerField(default=0)
    medal = models.CharField(max_length=16, choices=MEDAL_CHOICES, default=BRONZE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "created_at"]

    def __str__(self):
        return f"{self.pet} in {self.show}: {self.score}"


class Friendship(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    STATUS_CHOICES = [(PENDING, "Ожидает"), (ACCEPTED, "Друзья"), (BLOCKED, "Заблокирован")]

    from_profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="sent_friendships")
    to_profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="received_friendships")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("from_profile", "to_profile")

    def __str__(self):
        return f"{self.from_profile} -> {self.to_profile}: {self.status}"


class PrivateMessage(models.Model):
    sender = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="received_messages")
    body = models.CharField(max_length=500)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.recipient}"


class ChatMessage(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="chat_messages")
    body = models.CharField(max_length=240)
    hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile}: {self.body[:40]}"


class SupportTicket(models.Model):
    OPEN = "open"
    CLOSED = "closed"
    STATUS_CHOICES = [(OPEN, "Открыт"), (CLOSED, "Закрыт")]

    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=120)
    body = models.TextField(max_length=1000)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class UserReport(models.Model):
    reporter = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="reports_sent")
    reported_profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="reports_received", null=True, blank=True)
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=240)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reason


class FurnitureItem(models.Model):
    BED = "bed"
    TOY_CORNER = "toy_corner"
    WINDOW = "window"
    RUG = "rug"
    PLANT = "plant"
    POSTER = "poster"
    SLOT_CHOICES = [
        (BED, "Bed"),
        (TOY_CORNER, "Toy corner"),
        (WINDOW, "Window"),
        (RUG, "Rug"),
        (PLANT, "Plant"),
        (POSTER, "Poster"),
    ]

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    slot = models.CharField(max_length=24, choices=SLOT_CHOICES)
    price = models.PositiveIntegerField(default=0)
    beauty_bonus = models.PositiveIntegerField(default=0)
    xp_bonus_percent = models.PositiveIntegerField(default=0)
    max_level = models.PositiveIntegerField(default=5)
    color = models.CharField(max_length=16, default="#45b08c")

    def __str__(self):
        return self.name


class OwnedFurniture(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="furniture")
    item = models.ForeignKey(FurnitureItem, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=1)
    placed = models.BooleanField(default=False)
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "item")

    @property
    def beauty_total(self):
        return self.item.beauty_bonus * self.level

    @property
    def xp_bonus_total(self):
        return self.item.xp_bonus_percent * self.level

    @property
    def upgrade_cost(self):
        return self.item.price + self.level * 35

    def __str__(self):
        return f"{self.profile}: {self.item} L{self.level}"


class CollectionSet(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    reward_coins = models.PositiveIntegerField(default=0)
    reward_hearts = models.PositiveIntegerField(default=0)
    beauty_bonus = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CollectionPiece(models.Model):
    collection = models.ForeignKey(CollectionSet, on_delete=models.CASCADE, related_name="pieces")
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("collection", "order")
        ordering = ["collection", "order"]

    def __str__(self):
        return f"{self.collection}: {self.name}"


class OwnedCollectionPiece(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="collection_pieces")
    piece = models.ForeignKey(CollectionPiece, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("profile", "piece")

    def __str__(self):
        return f"{self.profile}: {self.piece} x{self.quantity}"


class CompletedCollection(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="completed_collections")
    collection = models.ForeignKey(CollectionSet, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "collection")

    def __str__(self):
        return f"{self.profile}: {self.collection}"


class Trophy(models.Model):
    MEDAL = "medal"
    PRIZE = "prize"
    CUP = "cup"
    BADGE = "badge"
    TYPE_CHOICES = [(MEDAL, "Medal"), (PRIZE, "Prize"), (CUP, "Cup"), (BADGE, "Badge")]

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    trophy_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=BADGE)
    source = models.CharField(max_length=80, blank=True)
    beauty_bonus = models.PositiveIntegerField(default=0)
    rarity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=16, default="#f3b84b")

    def __str__(self):
        return self.name


class OwnedTrophy(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="trophies")
    trophy = models.ForeignKey(Trophy, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "trophy")

    def __str__(self):
        return f"{self.profile}: {self.trophy}"


class ExplorationSite(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    min_level = models.PositiveIntegerField(default=1)
    energy_cost = models.PositiveIntegerField(default=10)
    coin_cost = models.PositiveIntegerField(default=0)
    reward_coins = models.PositiveIntegerField(default=0)
    reward_experience = models.PositiveIntegerField(default=0)
    daily_limit = models.PositiveIntegerField(default=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ExplorationLog(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="explorations")
    pet = models.ForeignKey(Pet, on_delete=models.SET_NULL, null=True, blank=True)
    site = models.ForeignKey(ExplorationSite, on_delete=models.CASCADE)
    found_piece = models.ForeignKey(CollectionPiece, on_delete=models.SET_NULL, null=True, blank=True)
    found_trophy = models.ForeignKey(Trophy, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile}: {self.site}"


class AssistantType(models.Model):
    CARETAKER = "caretaker"
    STYLIST = "stylist"
    SCOUT = "scout"
    BUILDER = "builder"
    ROLE_CHOICES = [
        (CARETAKER, "Care"),
        (STYLIST, "Style"),
        (SCOUT, "Explore"),
        (BUILDER, "Home"),
    ]

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    role = models.CharField(max_length=24, choices=ROLE_CHOICES)
    base_cost = models.PositiveIntegerField(default=50)
    max_level = models.PositiveIntegerField(default=20)
    bonus_per_level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class PlayerAssistant(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="assistants")
    assistant_type = models.ForeignKey(AssistantType, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("profile", "assistant_type")

    @property
    def train_cost(self):
        return self.assistant_type.base_cost + self.level * 25

    @property
    def bonus(self):
        return self.level * self.assistant_type.bonus_per_level

    def __str__(self):
        return f"{self.profile}: {self.assistant_type} L{self.level}"


class Club(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180, blank=True)
    crest_color = models.CharField(max_length=16, default="#45b08c")
    level = models.PositiveIntegerField(default=1)
    experience = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    hearts = models.PositiveIntegerField(default=0)
    member_limit = models.PositiveIntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ClubMembership(models.Model):
    OWNER = "owner"
    DEPUTY = "deputy"
    OFFICER = "officer"
    MEMBER = "member"
    ROLE_CHOICES = [(OWNER, "Owner"), (DEPUTY, "Deputy"), (OFFICER, "Officer"), (MEMBER, "Member")]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="memberships")
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="club_memberships")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=MEMBER)
    contribution_score = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("club", "profile")

    def __str__(self):
        return f"{self.profile} in {self.club}"


class ClubJoinRequest(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    STATUS_CHOICES = [(PENDING, "Pending"), (ACCEPTED, "Accepted"), (DECLINED, "Declined")]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="join_requests")
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="club_join_requests")
    message = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("club", "profile", "status")

    def __str__(self):
        return f"{self.profile} -> {self.club}: {self.status}"


class ClubBuildingType(models.Model):
    XP = "xp"
    CLUB_XP = "club_xp"
    HOME = "home"
    WARDROBE = "wardrobe"
    EXPLORE = "explore"
    EFFECT_CHOICES = [(XP, "XP"), (CLUB_XP, "Club XP"), (HOME, "Home"), (WARDROBE, "Wardrobe"), (EXPLORE, "Explore")]

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=180)
    effect = models.CharField(max_length=24, choices=EFFECT_CHOICES)
    bonus_per_level = models.PositiveIntegerField(default=1)
    max_level = models.PositiveIntegerField(default=20)
    base_cost = models.PositiveIntegerField(default=100)

    def __str__(self):
        return self.name


class ClubBuilding(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="buildings")
    building_type = models.ForeignKey(ClubBuildingType, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("club", "building_type")

    @property
    def upgrade_cost(self):
        return self.building_type.base_cost + self.level * 75

    @property
    def bonus(self):
        return self.level * self.building_type.bonus_per_level

    def __str__(self):
        return f"{self.club}: {self.building_type} L{self.level}"


class ClubContribution(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="contributions")
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="club_contributions")
    coins = models.PositiveIntegerField(default=0)
    hearts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile} -> {self.club}"


class ClubHistoryEvent(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(PlayerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text


class ClubAnnouncement(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="announcements")
    author = models.ForeignKey(PlayerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    body = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.body[:40]
