from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from game.models import Achievement, Item, Pet, PetShow, PlayerProfile, Quest, WearableItem


class Command(BaseCommand):
    help = "Create starter shop items, daily quests, and an optional demo player."

    def handle(self, *args, **options):
        items = [
            {
                "name": "Ягодный завтрак",
                "description": "Легкая еда для бодрого утра.",
                "item_type": Item.FOOD,
                "price": 28,
                "energy_delta": 6,
                "mood_delta": 2,
                "hunger_delta": 28,
                "experience_delta": 4,
                "beauty_delta": 1,
                "hearts_delta": 1,
                "icon": "food",
            },
            {
                "name": "Мяч с лентой",
                "description": "Игрушка для веселой тренировки.",
                "item_type": Item.TOY,
                "price": 42,
                "energy_delta": -5,
                "mood_delta": 24,
                "hunger_delta": -4,
                "experience_delta": 10,
                "beauty_delta": 1,
                "hearts_delta": 2,
                "icon": "toy",
            },
            {
                "name": "Теплый плед",
                "description": "Возвращает силы после прогулок.",
                "item_type": Item.CARE,
                "price": 36,
                "energy_delta": 26,
                "mood_delta": 8,
                "hunger_delta": 0,
                "experience_delta": 3,
                "beauty_delta": 0,
                "hearts_delta": 1,
                "icon": "care",
            },
            {
                "name": "Хрустящие звездочки",
                "description": "Редкое лакомство с бонусом опыта.",
                "item_type": Item.FOOD,
                "price": 55,
                "energy_delta": 8,
                "mood_delta": 8,
                "hunger_delta": 34,
                "experience_delta": 12,
                "beauty_delta": 2,
                "hearts_delta": 3,
                "icon": "food",
            },
        ]
        for data in items:
            Item.objects.update_or_create(name=data["name"], defaults=data)

        quests = [
            {
                "title": "Доброе утро",
                "description": "Покорми активного питомца один раз.",
                "action": Quest.FEED,
                "target_count": 1,
                "reward_coins": 18,
                "reward_experience": 6,
            },
            {
                "title": "Игровая пауза",
                "description": "Поиграй с питомцем два раза.",
                "action": Quest.PLAY,
                "target_count": 2,
                "reward_coins": 30,
                "reward_experience": 12,
            },
            {
                "title": "Мягкая забота",
                "description": "Погладь питомца три раза.",
                "action": Quest.PET,
                "target_count": 3,
                "reward_coins": 24,
                "reward_experience": 8,
            },
            {
                "title": "Свежий воздух",
                "description": "Отправь питомца на прогулку.",
                "action": Quest.WALK,
                "target_count": 1,
                "reward_coins": 34,
                "reward_experience": 14,
            },
            {
                "title": "Полезная покупка",
                "description": "Купи любой предмет в магазине.",
                "action": Quest.BUY,
                "target_count": 1,
                "reward_coins": 15,
                "reward_experience": 5,
            },
            {
                "title": "Тихая тренировка",
                "description": "Проведи любую тренировку питомца.",
                "action": Quest.TRAIN,
                "target_count": 1,
                "reward_coins": 22,
                "reward_experience": 8,
            },
            {
                "title": "Показ талантов",
                "description": "Участвуй в любой выставке.",
                "action": Quest.SHOW,
                "target_count": 1,
                "reward_coins": 28,
                "reward_experience": 10,
            },
        ]
        for data in quests:
            Quest.objects.update_or_create(title=data["title"], defaults={**data, "active": True})

        wearables = [
            {
                "name": "Листовой венок",
                "description": "Легкий природный аксессуар для прогулок.",
                "slot": WearableItem.HAT,
                "price": 45,
                "beauty_bonus": 8,
                "mood_bonus": 3,
                "show_bonus": 2,
                "color": "#45b08c",
            },
            {
                "name": "Лунный ошейник",
                "description": "Аккуратная вещь для спокойного питомца.",
                "slot": WearableItem.COLLAR,
                "price": 60,
                "beauty_bonus": 10,
                "mood_bonus": 2,
                "show_bonus": 4,
                "color": "#75a7e6",
            },
            {
                "name": "Праздничный плащ",
                "description": "Наряд для первых выставок.",
                "slot": WearableItem.OUTFIT,
                "price": 80,
                "beauty_bonus": 16,
                "mood_bonus": 4,
                "show_bonus": 8,
                "color": "#9b8ee8",
            },
            {
                "name": "Солнечный талисман",
                "description": "Маленький бонус к выступлениям.",
                "slot": WearableItem.CHARM,
                "price": 70,
                "beauty_bonus": 7,
                "mood_bonus": 1,
                "show_bonus": 10,
                "color": "#f3b84b",
            },
        ]
        for data in wearables:
            WearableItem.objects.update_or_create(name=data["name"], defaults=data)

        shows = [
            {
                "name": "Домашний смотр",
                "description": "Небольшая выставка для начинающих питомцев.",
                "min_level": 1,
                "entry_fee": 10,
                "reward_coins": 18,
                "reward_hearts": 3,
                "reward_experience": 8,
            },
            {
                "name": "Городской подиум",
                "description": "Соревнование для подготовленных питомцев.",
                "min_level": 2,
                "entry_fee": 25,
                "reward_coins": 36,
                "reward_hearts": 6,
                "reward_experience": 16,
            },
            {
                "name": "Большой финал",
                "description": "Серьезная выставка для опытных команд.",
                "min_level": 4,
                "entry_fee": 60,
                "reward_coins": 80,
                "reward_hearts": 12,
                "reward_experience": 28,
            },
        ]
        for data in shows:
            PetShow.objects.update_or_create(name=data["name"], defaults={**data, "active": True})

        achievements = [
            {
                "code": Achievement.FIRST_FEED,
                "title": "Первое кормление",
                "description": "Питомец получил первую заботливую порцию еды.",
                "reward_coins": 12,
            },
            {
                "code": Achievement.FIRST_BUY,
                "title": "Первая покупка",
                "description": "В инвентаре появился первый полезный предмет.",
                "reward_coins": 12,
            },
            {
                "code": Achievement.LEVEL_3,
                "title": "Уровень 3",
                "description": "Любой питомец вырос до третьего уровня.",
                "reward_coins": 35,
            },
            {
                "code": Achievement.THREE_PETS,
                "title": "Команда питомцев",
                "description": "У игрока есть три питомца.",
                "reward_coins": 40,
            },
            {
                "code": Achievement.RICH,
                "title": "Копилка",
                "description": "На счете накопилось 250 монет.",
                "reward_coins": 25,
            },
        ]
        for data in achievements:
            Achievement.objects.update_or_create(code=data["code"], defaults=data)

        demo, created = User.objects.get_or_create(username="demo")
        if created:
            demo.set_password("demo12345")
            demo.save()
        profile, _ = PlayerProfile.objects.get_or_create(user=demo, defaults={"coins": 180})
        profile.display_name = "Demo Keeper"
        profile.coins = max(profile.coins, 180)
        profile.save(update_fields=["display_name", "coins"])
        Pet.objects.get_or_create(owner=demo, name="Мята", defaults={"species": Pet.FOX, "active": True, "level": 2})

        self.stdout.write(self.style.SUCCESS("Starter data is ready. Demo login: demo / demo12345"))
