from django.contrib import admin

from .models import ActionLog, Achievement, InventoryItem, Item, Pet, PlayerAchievement, PlayerProfile, Quest, QuestProgress


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "coins", "created_at")
    search_fields = ("user__username", "display_name")


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "species", "level", "experience", "energy", "mood", "hunger", "active")
    list_filter = ("species", "active")
    search_fields = ("name", "owner__username")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "price", "energy_delta", "mood_delta", "hunger_delta", "experience_delta")
    list_filter = ("item_type",)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("profile", "item", "quantity")
    search_fields = ("profile__user__username", "item__name")


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("title", "action", "target_count", "reward_coins", "reward_experience", "active")
    list_filter = ("action", "active")


@admin.register(QuestProgress)
class QuestProgressAdmin(admin.ModelAdmin):
    list_display = ("profile", "quest", "date", "count", "completed", "claimed")
    list_filter = ("date", "completed", "claimed")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "reward_coins")
    search_fields = ("title", "code")


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ("profile", "achievement", "unlocked_at")
    search_fields = ("profile__user__username", "achievement__title")


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ("profile", "pet", "text", "created_at")
    search_fields = ("profile__user__username", "pet__name", "text")
