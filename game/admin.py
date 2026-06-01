from django.contrib import admin

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


@admin.register(FurnitureItem)
class FurnitureItemAdmin(admin.ModelAdmin):
    list_display = ("name", "slot", "price", "beauty_bonus", "xp_bonus_percent", "max_level")
    list_filter = ("slot",)


@admin.register(OwnedFurniture)
class OwnedFurnitureAdmin(admin.ModelAdmin):
    list_display = ("profile", "item", "level", "placed")
    list_filter = ("placed",)


@admin.register(CollectionSet)
class CollectionSetAdmin(admin.ModelAdmin):
    list_display = ("name", "reward_coins", "reward_hearts", "beauty_bonus", "active")
    list_filter = ("active",)


@admin.register(CollectionPiece)
class CollectionPieceAdmin(admin.ModelAdmin):
    list_display = ("collection", "name", "order")
    list_filter = ("collection",)


@admin.register(OwnedCollectionPiece)
class OwnedCollectionPieceAdmin(admin.ModelAdmin):
    list_display = ("profile", "piece", "quantity")


@admin.register(CompletedCollection)
class CompletedCollectionAdmin(admin.ModelAdmin):
    list_display = ("profile", "collection", "completed_at")


@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ("name", "trophy_type", "source", "beauty_bonus", "rarity")
    list_filter = ("trophy_type", "rarity")


@admin.register(OwnedTrophy)
class OwnedTrophyAdmin(admin.ModelAdmin):
    list_display = ("profile", "trophy", "awarded_at")


@admin.register(ExplorationSite)
class ExplorationSiteAdmin(admin.ModelAdmin):
    list_display = ("name", "min_level", "energy_cost", "coin_cost", "daily_limit", "active")
    list_filter = ("active",)


@admin.register(ExplorationLog)
class ExplorationLogAdmin(admin.ModelAdmin):
    list_display = ("profile", "pet", "site", "found_piece", "found_trophy", "created_at")


@admin.register(AssistantType)
class AssistantTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "base_cost", "max_level", "bonus_per_level")
    list_filter = ("role",)


@admin.register(PlayerAssistant)
class PlayerAssistantAdmin(admin.ModelAdmin):
    list_display = ("profile", "assistant_type", "level")


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "experience", "coins", "hearts", "member_limit")
    search_fields = ("name",)


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ("club", "profile", "role", "contribution_score", "joined_at")
    list_filter = ("role",)


@admin.register(ClubJoinRequest)
class ClubJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("club", "profile", "status", "created_at")
    list_filter = ("status",)


@admin.register(ClubBuildingType)
class ClubBuildingTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "effect", "bonus_per_level", "max_level", "base_cost")
    list_filter = ("effect",)


@admin.register(ClubBuilding)
class ClubBuildingAdmin(admin.ModelAdmin):
    list_display = ("club", "building_type", "level")


@admin.register(ClubContribution)
class ClubContributionAdmin(admin.ModelAdmin):
    list_display = ("club", "profile", "coins", "hearts", "created_at")


@admin.register(ClubHistoryEvent)
class ClubHistoryEventAdmin(admin.ModelAdmin):
    list_display = ("club", "actor", "text", "created_at")


@admin.register(ClubAnnouncement)
class ClubAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("club", "author", "body", "created_at")


@admin.register(FragmentType)
class FragmentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "required_fragments", "beauty_bonus")
    list_filter = ("kind",)


@admin.register(OwnedFragment)
class OwnedFragmentAdmin(admin.ModelAdmin):
    list_display = ("profile", "fragment_type", "quantity", "completed_count")


@admin.register(AdventureRoute)
class AdventureRouteAdmin(admin.ModelAdmin):
    list_display = ("name", "min_level", "duration_minutes", "energy_cost", "reward_coins", "active")
    list_filter = ("active",)


@admin.register(PetAdventure)
class PetAdventureAdmin(admin.ModelAdmin):
    list_display = ("profile", "pet", "route", "finishes_at", "completed")
    list_filter = ("completed",)


@admin.register(CompetitionMode)
class CompetitionModeAdmin(admin.ModelAdmin):
    list_display = ("name", "stat", "min_level", "entry_fee", "reward_coins", "active")
    list_filter = ("stat", "active")


@admin.register(CompetitionEntry)
class CompetitionEntryAdmin(admin.ModelAdmin):
    list_display = ("mode", "profile", "pet", "score", "league", "created_at")
    list_filter = ("mode", "league")


@admin.register(ChestType)
class ChestTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "key_cost", "daily_limit", "min_coins", "max_coins")


@admin.register(ChestOpening)
class ChestOpeningAdmin(admin.ModelAdmin):
    list_display = ("profile", "chest_type", "reward_text", "coins", "hearts", "created_at")


@admin.register(GiftCatalogItem)
class GiftCatalogItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price_hearts")


@admin.register(SentGift)
class SentGiftAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "gift", "created_at")


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "is_news")
    list_filter = ("is_news",)


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "pinned", "locked", "updated_at")
    list_filter = ("pinned", "locked", "category")


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "hidden", "created_at")
    list_filter = ("hidden",)


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "active")
    list_filter = ("category", "active")


@admin.register(GamePreference)
class GamePreferenceAdmin(admin.ModelAdmin):
    list_display = ("profile", "compact_mode", "show_bottom_nav", "show_quick_actions", "low_bandwidth")
