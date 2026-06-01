from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    AssistantType,
    ChatMessage,
    Club,
    ClubBuilding,
    ClubBuildingType,
    ClubContribution,
    ClubMembership,
    CollectionPiece,
    CollectionSet,
    ExplorationLog,
    ExplorationSite,
    FurnitureItem,
    Item,
    OwnedCollectionPiece,
    OwnedFurniture,
    OwnedWearable,
    Pet,
    PetShow,
    PlayerAssistant,
    PlayerProfile,
    Quest,
    ShowEntry,
    SupportTicket,
    Trophy,
    WearableItem,
)


class GameFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="player", password="strong-pass-123")
        self.profile = PlayerProfile.objects.create(user=self.user, coins=100)
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
