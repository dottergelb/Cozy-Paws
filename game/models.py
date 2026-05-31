from django.conf import settings
from django.db import models
from django.utils import timezone


class PlayerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=40, blank=True)
    bio = models.CharField(max_length=160, blank=True)
    coins = models.PositiveIntegerField(default=120)
    last_energy_tick = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    @property
    def total_pet_levels(self):
        return sum(pet.level for pet in self.user.pets.all())

    @property
    def public_name(self):
        return self.display_name or self.user.username


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


class Quest(models.Model):
    FEED = "feed"
    PLAY = "play"
    PET = "pet"
    WALK = "walk"
    BUY = "buy"
    ACTION_CHOICES = [
        (FEED, "Покормить"),
        (PLAY, "Поиграть"),
        (PET, "Погладить"),
        (WALK, "Прогулка"),
        (BUY, "Покупка"),
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
