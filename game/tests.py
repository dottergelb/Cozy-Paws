from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Item, Pet, PlayerProfile, Quest


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
        self.assertEqual(self.profile.quest_progress.count(), 1)

    def test_buy_item_requires_enough_coins(self):
        self.profile.coins = 5
        self.profile.save()
        self.client.login(username="player", password="strong-pass-123")
        response = self.client.post(reverse("buy_item", args=[self.item.id]))
        self.assertRedirects(response, reverse("shop"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, 5)
