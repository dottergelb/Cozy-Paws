from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ChatMessage, Item, OwnedWearable, Pet, PetShow, PlayerProfile, Quest, ShowEntry, SupportTicket, WearableItem


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
