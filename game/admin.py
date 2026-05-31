from django.contrib import admin

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


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "coins", "hearts", "last_activity_at", "created_at")
    search_fields = ("user__username", "display_name")


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "species", "level", "experience", "energy", "mood", "hunger", "beauty", "active")
    list_filter = ("species", "active")
    search_fields = ("name", "owner__username")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "price", "energy_delta", "mood_delta", "hunger_delta", "experience_delta", "beauty_delta", "hearts_delta")
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


@admin.register(WearableItem)
class WearableItemAdmin(admin.ModelAdmin):
    list_display = ("name", "slot", "price", "beauty_bonus", "mood_bonus", "show_bonus")
    list_filter = ("slot",)


@admin.register(OwnedWearable)
class OwnedWearableAdmin(admin.ModelAdmin):
    list_display = ("profile", "wearable", "quantity")


@admin.register(EquippedWearable)
class EquippedWearableAdmin(admin.ModelAdmin):
    list_display = ("pet", "wearable", "equipped_at")


@admin.register(ActionCooldown)
class ActionCooldownAdmin(admin.ModelAdmin):
    list_display = ("profile", "key", "available_at")
    list_filter = ("key",)


@admin.register(PetShow)
class PetShowAdmin(admin.ModelAdmin):
    list_display = ("name", "min_level", "entry_fee", "reward_coins", "active")
    list_filter = ("active",)


@admin.register(ShowEntry)
class ShowEntryAdmin(admin.ModelAdmin):
    list_display = ("show", "profile", "pet", "score", "medal", "created_at")
    list_filter = ("show", "medal")


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("from_profile", "to_profile", "status", "created_at")
    list_filter = ("status",)


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "read", "created_at")
    list_filter = ("read",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("profile", "body", "hidden", "created_at")
    list_filter = ("hidden",)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("profile", "subject", "status", "created_at")
    list_filter = ("status",)


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ("reporter", "reported_profile", "reason", "resolved", "created_at")
    list_filter = ("resolved",)
