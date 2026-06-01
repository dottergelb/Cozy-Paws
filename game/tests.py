from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    AdventureRoute,
    AssistantType,
    ChestOpening,
    ChestType,
    ChatMessage,
    Club,
    ClubBuilding,
    ClubBuildingType,
    ClubContribution,
    ClubMembership,
    CollectionPiece,
    CollectionSet,
    CompetitionEntry,
    CompetitionMode,
    ExplorationLog,
    ExplorationSite,
    ForumCategory,
    ForumPost,
    ForumThread,
    FragmentType,
    FurnitureItem,
    GamePreference,
    GiftCatalogItem,
    HelpArticle,
    Item,
    OwnedCollectionPiece,
    OwnedFragment,
    OwnedFurniture,
    OwnedWearable,
    Pet,
    PetAdventure,
    PetShow,
    PlayerAssistant,
    PlayerProfile,
    Quest,
    SentGift,
    ShowEntry,
    SupportTicket,
    Trophy,
    WearableItem,
)


class GameFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="player", password="strong-pass-123")
        self.profile = PlayerProfile.objects.create(user=self.user, coins=100)
        self.friend_user = User.objects.create_user(username="friend", password="strong-pass-123")
        self.friend_profile = PlayerProfile.objects.create(user=self.friend_user, coins=100)
        self.pet = Pet.objects.create(owner=self.user, name="Пикс", active=True, energy=80, hunger=50, mood=70)
        self.item = Item.objects.create(
            name="Снэк",
            description="Тестовый предмет",
            item_type=Item.FOOD,
            price=20,
            hunger_delta=20,
            icon="food",
        )
        Quest.objects.create(title="Кормление", description="Тест", action=Quest.FEED, reward_coins=5)
        Quest.objects.create(title="Тренировка", description="Тест", action=Quest.TRAIN, reward_coins=5)
        Quest.objects.create(title="Выставка", description="Тест", action=Quest.SHOW, reward_coins=5)
        self.wearable = WearableItem.objects.create(
            name="Тестовый венок",
            description="Тест",
            slot=WearableItem.HAT,
            price=30,
            beauty_bonus=5,
        )
        self.show = PetShow.objects.create(
            name="Тестовый смотр",
            description="Тест",
            min_level=1,
            entry_fee=5,
            reward_coins=10,
            reward_hearts=2,
            reward_experience=5,
        )
        self.furniture = FurnitureItem.objects.create(
            name="Test Bed",
            description="Test furniture",
            slot=FurnitureItem.BED,
            price=25,
            beauty_bonus=3,
            xp_bonus_percent=1,
        )
        self.collection = CollectionSet.objects.create(
            name="Test Collection",
            description="Test pieces",
            reward_coins=10,
            reward_hearts=3,
            beauty_bonus=5,
        )
        self.piece = CollectionPiece.objects.create(collection=self.collection, name="Test Piece", order=1)
        self.site = ExplorationSite.objects.create(
            name="Test Meadow",
            description="Test explore",
            min_level=1,
            energy_cost=5,
            reward_coins=3,
            reward_experience=4,
            daily_limit=2,
        )
        self.trophy = Trophy.objects.create(name="Test Badge", description="Test trophy", trophy_type=Trophy.BADGE, beauty_bonus=2)
        self.assistant_type = AssistantType.objects.create(
            name="Test Scout",
            description="Test assistant",
            role=AssistantType.SCOUT,
            base_cost=5,
            max_level=3,
        )
        self.club_building_type = ClubBuildingType.objects.create(
            name="Test Hall",
            description="Club building",
            effect=ClubBuildingType.XP,
            base_cost=20,
        )
        self.fragment_type = FragmentType.objects.create(
            name="Test Seed",
            description="Test fragment",
            kind=FragmentType.GARDEN,
            required_fragments=3,
            beauty_bonus=4,
        )
        self.adventure_route = AdventureRoute.objects.create(
            name="Test Errand",
            description="Short test route",
            min_level=1,
            duration_minutes=1,
            energy_cost=5,
            reward_coins=12,
            reward_hearts=2,
            reward_experience=6,
        )
        self.competition_mode = CompetitionMode.objects.create(
            name="Test League",
            description="Test competition",
            stat=CompetitionMode.AGILITY,
            min_level=1,
            entry_fee=5,
            reward_coins=12,
            reward_hearts=2,
        )
        self.chest_type = ChestType.objects.create(
            name="Test Chest",
            description="Test chest",
            key_cost=2,
            daily_limit=2,
            min_coins=5,
            max_coins=5,
        )
        self.gift = GiftCatalogItem.objects.create(name="Test Card", description="Test gift", price_hearts=3)
        self.forum_category = ForumCategory.objects.create(name="Test Forum", description="Test forum")
        self.help_article = HelpArticle.objects.create(category="Basics", title="Test Help", body="Help body")

    def test_protected_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_pet_action_adds_rewards_and_progress(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("pet_action", args=["feed"]))
        self.assertRedirects(response, reverse("dashboard"))
        self.pet.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertGreater(self.pet.experience, 0)
        self.assertEqual(self.profile.coins, 104)
        self.assertTrue(self.profile.quest_progress.filter(quest__action=Quest.FEED, completed=True).exists())

    def test_buy_item_requires_enough_coins(self):
        self.profile.coins = 5
        self.profile.save()
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("buy_item", args=[self.item.id]))
        self.assertRedirects(response, reverse("shop"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, 5)

    def test_buy_and_equip_wearable(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("buy_wearable", args=[self.wearable.id]))
        self.assertRedirects(response, reverse("wardrobe"))
        owned = OwnedWearable.objects.get(profile=self.profile, wearable=self.wearable)
        response = self.client.post(reverse("equip_wearable", args=[owned.id]))
        self.assertRedirects(response, reverse("wardrobe"))
        self.assertEqual(self.pet.equipped_wearables.count(), 1)

    def test_training_updates_trait(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("train_pet", args=["agility"]))
        self.assertRedirects(response, reverse("training"))
        self.pet.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.pet.agility, 2)
        self.assertEqual(self.profile.hearts, 2)

    def test_show_entry_awards_rewards(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("enter_show", args=[self.show.id]))
        self.assertRedirects(response, reverse("shows"))
        self.assertEqual(ShowEntry.objects.filter(profile=self.profile).count(), 1)
        self.profile.refresh_from_db()
        self.assertGreaterEqual(self.profile.coins, 105)

    def test_chat_and_support_create_records(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("chat"), {"body": "Привет"})
        self.assertRedirects(response, reverse("chat"))
        self.assertEqual(ChatMessage.objects.filter(profile=self.profile).count(), 1)
        response = self.client.post(reverse("support"), {"subject": "Помощь", "body": "Нужна проверка"})
        self.assertRedirects(response, reverse("support"))
        self.assertEqual(SupportTicket.objects.filter(profile=self.profile).count(), 1)

    def test_home_room_buy_place_and_upgrade(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("buy_furniture", args=[self.furniture.id]))
        self.assertRedirects(response, reverse("home_room"))
        owned = OwnedFurniture.objects.get(profile=self.profile, item=self.furniture)
        self.assertTrue(owned.placed)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, 75)
        response = self.client.post(reverse("upgrade_furniture", args=[owned.id]))
        self.assertRedirects(response, reverse("home_room"))
        owned.refresh_from_db()
        self.assertEqual(owned.level, 2)

    def test_explore_awards_piece_and_log(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("run_explore", args=[self.site.id]))
        self.assertRedirects(response, reverse("explore"))
        self.assertEqual(ExplorationLog.objects.filter(profile=self.profile).count(), 1)
        self.assertTrue(OwnedCollectionPiece.objects.filter(profile=self.profile, quantity__gt=0).exists())
        self.pet.refresh_from_db()
        self.assertEqual(self.pet.energy, 75)

    def test_assistant_training_spends_hearts(self):
        self.profile.hearts = 20
        self.profile.save(update_fields=["hearts"])
        assistant = PlayerAssistant.objects.create(profile=self.profile, assistant_type=self.assistant_type)
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("train_assistant", args=[assistant.id]))
        self.assertRedirects(response, reverse("assistants"))
        assistant.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(assistant.level, 1)
        self.assertEqual(self.profile.hearts, 15)

    def test_club_contribution_and_building_upgrade(self):
        self.profile.coins = 500
        self.profile.hearts = 20
        self.profile.save(update_fields=["coins", "hearts"])
        club = Club.objects.create(name="Test Club", coins=50)
        ClubMembership.objects.create(club=club, profile=self.profile, role=ClubMembership.OWNER)
        building = ClubBuilding.objects.create(club=club, building_type=self.club_building_type)
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("contribute_club", args=[club.id]), {"coins": 40, "hearts": 5})
        self.assertRedirects(response, reverse("club_detail", args=[club.id]))
        self.assertEqual(ClubContribution.objects.filter(club=club, profile=self.profile).count(), 1)
        club.refresh_from_db()
        self.assertEqual(club.coins, 90)
        response = self.client.post(reverse("upgrade_club_building", args=[building.id]))
        self.assertRedirects(response, reverse("club_detail", args=[club.id]))
        building.refresh_from_db()
        self.assertEqual(building.level, 1)

    def test_fragment_completion_adds_passive_bonus(self):
        owned = OwnedFragment.objects.create(profile=self.profile, fragment_type=self.fragment_type, quantity=3)
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("craft_fragment", args=[owned.id]))
        self.assertRedirects(response, reverse("fragments"))
        owned.refresh_from_db()
        self.assertEqual(owned.completed_count, 1)
        self.assertEqual(self.profile.passive_beauty_bonus, 4)

    def test_adventure_start_and_finish_awards_rewards(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("start_adventure", args=[self.adventure_route.id]))
        self.assertRedirects(response, reverse("adventures"))
        adventure = PetAdventure.objects.get(profile=self.profile)
        adventure.finishes_at = timezone.now() - timezone.timedelta(minutes=1)
        adventure.save(update_fields=["finishes_at"])
        response = self.client.post(reverse("finish_adventure", args=[adventure.id]))
        self.assertRedirects(response, reverse("adventures"))
        adventure.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertTrue(adventure.completed)
        self.assertEqual(self.profile.coins, 112)
        self.assertTrue(OwnedFragment.objects.filter(profile=self.profile, quantity__gt=0).exists())

    def test_competition_entry_creates_score(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("enter_competition", args=[self.competition_mode.id]))
        self.assertRedirects(response, reverse("competitions"))
        self.assertEqual(CompetitionEntry.objects.filter(profile=self.profile, mode=self.competition_mode).count(), 1)
        self.profile.refresh_from_db()
        self.assertGreaterEqual(self.profile.coins, 107)

    def test_chest_opening_spends_hearts_and_records_reward(self):
        self.profile.hearts = 10
        self.profile.save(update_fields=["hearts"])
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("open_chest", args=[self.chest_type.id]))
        self.assertRedirects(response, reverse("chests"))
        self.assertEqual(ChestOpening.objects.filter(profile=self.profile).count(), 1)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, 105)

    def test_gift_send_records_message(self):
        self.profile.hearts = 10
        self.profile.save(update_fields=["hearts"])
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("send_gift", args=[self.gift.id, self.friend_profile.id]), {"message": "Enjoy"})
        self.assertRedirects(response, reverse("gifts"))
        self.assertEqual(SentGift.objects.filter(sender=self.profile, recipient=self.friend_profile).count(), 1)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.hearts, 7)

    def test_forum_thread_and_reply(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("create_forum_thread", args=[self.forum_category.id]), {"title": "Hello", "body": "First post"})
        thread = ForumThread.objects.get(category=self.forum_category)
        self.assertRedirects(response, reverse("forum_thread", args=[thread.id]))
        self.profile.cooldowns.all().delete()
        response = self.client.post(reverse("reply_forum_thread", args=[thread.id]), {"body": "Reply"})
        self.assertRedirects(response, reverse("forum_thread", args=[thread.id]))
        self.assertEqual(ForumPost.objects.filter(thread=thread).count(), 2)

    def test_help_and_game_settings_pages(self):
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.get(reverse("help_center"))
        self.assertContains(response, "Test Help")
        response = self.client.post(
            reverse("game_settings"),
            {"compact_mode": "on", "show_bottom_nav": "on", "show_quick_actions": "on", "low_bandwidth": "on"},
        )
        self.assertRedirects(response, reverse("game_settings"))
        preferences = GamePreference.objects.get(profile=self.profile)
        self.assertTrue(preferences.compact_mode)
        self.assertTrue(preferences.low_bandwidth)

    def test_new_sections_render_for_logged_in_user(self):
        self.client.login(username="player", password="strong-pass-123")
        for name in ["fragments", "adventures", "competitions", "chests", "gifts", "forum"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
