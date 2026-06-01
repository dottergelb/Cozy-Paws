from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from game.models import (
    Achievement,
    AdventureRoute,
    AssistantType,
    ChestType,
    Club,
    ClubBuilding,
    ClubBuildingType,
    ClubHistoryEvent,
    ClubMembership,
    CollectionPiece,
    CollectionSet,
    CompetitionMode,
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
    MemoryChapter,
    MemoryPrompt,
    OwnedCollectionPiece,
    OwnedFragment,
    OwnedFurniture,
    OwnedTrophy,
    Pet,
    PetShow,
    PlayerAssistant,
    PlayerProfile,
    Quest,
    Trophy,
    WearableItem,
)


class Command(BaseCommand):
    help = "Создает стартовые предметы, ежедневные задания и демо-игрока."

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
            {
                "title": "Глава дня",
                "description": "Создай новую главу в Тропе памяти.",
                "action": Quest.MEMORY,
                "target_count": 1,
                "reward_coins": 32,
                "reward_experience": 14,
            },
        ]
        for data in quests:
            Quest.objects.update_or_create(title=data["title"], defaults={**data, "active": True})

        memory_prompts = [
            {
                "title": "Солнечный домик",
                "description": "Питомец замечает маленькую деталь в комнате и превращает ее в историю.",
                "theme": MemoryPrompt.CARE,
                "energy_cost": 8,
                "coin_cost": 0,
                "reward_coins": 24,
                "reward_hearts": 1,
                "reward_experience": 10,
                "bond_delta": 14,
                "heart_boost_cost": 6,
            },
            {
                "title": "Записка с поляны",
                "description": "Короткая прогулка становится редкой страницей альбома.",
                "theme": MemoryPrompt.EXPLORE,
                "energy_cost": 12,
                "coin_cost": 6,
                "reward_coins": 34,
                "reward_hearts": 2,
                "reward_experience": 16,
                "bond_delta": 18,
                "heart_boost_cost": 8,
            },
            {
                "title": "Портрет для клуба",
                "description": "История, которую приятно показать друзьям и клубу.",
                "theme": MemoryPrompt.SOCIAL,
                "energy_cost": 10,
                "coin_cost": 4,
                "reward_coins": 30,
                "reward_hearts": 2,
                "reward_experience": 12,
                "bond_delta": 16,
                "heart_boost_cost": 7,
            },
            {
                "title": "Нарядная сцена",
                "description": "Питомец вспоминает день как мини-выставку с личной деталью.",
                "theme": MemoryPrompt.STYLE,
                "energy_cost": 10,
                "coin_cost": 8,
                "reward_coins": 38,
                "reward_hearts": 2,
                "reward_experience": 14,
                "bond_delta": 17,
                "heart_boost_cost": 9,
            },
        ]
        for data in memory_prompts:
            MemoryPrompt.objects.update_or_create(title=data["title"], defaults={**data, "active": True})

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

        furniture_items = [
            ("Облачная лежанка", "Мягкий уголок, где питомец чувствует себя дома.", FurnitureItem.BED, 65, 8, 1, "#75a7e6"),
            ("Корзина ленточных игрушек", "Аккуратное место для игрушек с небольшим бонусом стиля.", FurnitureItem.TOY_CORNER, 55, 6, 0, "#ef7b6a"),
            ("Солнечное окно", "Теплый свет для радостных тренировочных дней.", FurnitureItem.WINDOW, 80, 10, 1, "#f3b84b"),
            ("Мшистый ковер", "Спокойный зеленый ковер для тихих вечеров.", FurnitureItem.RUG, 45, 5, 0, "#45b08c"),
            ("Карманный папоротник", "Маленькое растение, которое освежает комнату.", FurnitureItem.PLANT, 50, 6, 0, "#23765d"),
            ("Праздничный постер", "Яркий постер с дружеской выставки питомцев.", FurnitureItem.POSTER, 70, 9, 1, "#9b8ee8"),
        ]
        for name, description, slot, price, beauty_bonus, xp_bonus_percent, color in furniture_items:
            FurnitureItem.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "slot": slot,
                    "price": price,
                    "beauty_bonus": beauty_bonus,
                    "xp_bonus_percent": xp_bonus_percent,
                    "max_level": 6,
                    "color": color,
                },
            )

        collection_data = [
            ("Пикниковые воспоминания", "Маленькие сувениры с солнечных прогулок.", ["Кусочек карты", "Ягодная салфетка", "Крошечная чашка", "Теплый камешек"], 45, 8, 10),
            ("Садовые талисманы", "Маленькие талисманы, найденные у цветов и мха.", ["Семенной колокольчик", "Листовая булавка", "Капля росы", "Лента ростка"], 55, 10, 12),
            ("Лунные безделушки", "Тихие ночные сокровища для терпеливых исследователей.", ["Лунная пуговица", "Синяя нить", "Звездный осколок", "Серебряная ракушка"], 70, 14, 16),
        ]
        for name, description, pieces, reward_coins, reward_hearts, beauty_bonus in collection_data:
            collection, _ = CollectionSet.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "reward_coins": reward_coins,
                    "reward_hearts": reward_hearts,
                    "beauty_bonus": beauty_bonus,
                    "active": True,
                },
            )
            for index, piece_name in enumerate(pieces, start=1):
                CollectionPiece.objects.update_or_create(collection=collection, order=index, defaults={"name": piece_name})

        trophies = [
            ("Первая выставочная лента", "Выдается за первые успехи на выставках.", Trophy.MEDAL, "Домашний смотр", 5, 1, "#f3b84b"),
            ("Кубок соседей", "Кубок для стабильных выступлений.", Trophy.CUP, "Городской подиум", 12, 2, "#75a7e6"),
            ("Большой уютный приз", "Редкий приз для ухоженных команд.", Trophy.PRIZE, "Большой финал", 20, 3, "#9b8ee8"),
            ("Значок искателя луга", "Иногда находится во время исследований.", Trophy.BADGE, "Исследования", 7, 1, "#45b08c"),
        ]
        for name, description, trophy_type, source, beauty_bonus, rarity, color in trophies:
            Trophy.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "trophy_type": trophy_type,
                    "source": source,
                    "beauty_bonus": beauty_bonus,
                    "rarity": rarity,
                    "color": color,
                },
            )

        sites = [
            ("Мягкий луг", "Безопасная поляна с частями коллекций и небольшими наградами.", 1, 10, 0, 8, 8, 6),
            ("Старая садовая тропа", "Лучшее место для редких сувениров.", 2, 16, 8, 14, 12, 4),
            ("Лунный холм", "Поздний маршрут с повышенным шансом трофеев.", 4, 24, 18, 24, 20, 3),
        ]
        for name, description, min_level, energy_cost, coin_cost, reward_coins, reward_experience, daily_limit in sites:
            ExplorationSite.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "min_level": min_level,
                    "energy_cost": energy_cost,
                    "coin_cost": coin_cost,
                    "reward_coins": reward_coins,
                    "reward_experience": reward_experience,
                    "daily_limit": daily_limit,
                    "active": True,
                },
            )

        fragment_types = [
            ("Семена розового окна", "Садовая реликвия, выращенная из фрагментов тропы.", FragmentType.GARDEN, 4, 5, "#ef7b6a"),
            ("Ростки папоротникового фонаря", "Свежие зеленые фрагменты для спокойного угла дома.", FragmentType.GARDEN, 5, 7, "#45b08c"),
            ("Осколки сапфировой лапки", "Маленькие синие самоцветы с бонусом стиля.", FragmentType.JEWEL, 5, 8, "#75a7e6"),
            ("Крошки янтарной звезды", "Теплые самоцветы из редких наград.", FragmentType.JEWEL, 6, 10, "#f3b84b"),
        ]
        for name, description, kind, required_fragments, beauty_bonus, color in fragment_types:
            FragmentType.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "kind": kind,
                    "required_fragments": required_fragments,
                    "beauty_bonus": beauty_bonus,
                    "color": color,
                },
            )

        adventures = [
            ("Поручение у пекарни", "Короткая прогулка мимо теплых окон и дружелюбных ароматов.", 1, 1, 8, 14, 1, 9),
            ("Пикниковая тропа", "Более длинный маршрут с лучшим шансом фрагментов.", 2, 3, 14, 28, 3, 18),
            ("Фонарный мост", "Спокойное вечернее приключение для тренированных питомцев.", 4, 5, 22, 55, 6, 30),
        ]
        for name, description, min_level, duration_minutes, energy_cost, reward_coins, reward_hearts, reward_experience in adventures:
            AdventureRoute.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "min_level": min_level,
                    "duration_minutes": duration_minutes,
                    "energy_cost": energy_cost,
                    "reward_coins": reward_coins,
                    "reward_hearts": reward_hearts,
                    "reward_experience": reward_experience,
                    "active": True,
                },
            )

        competitions = [
            ("Ленточный рывок", "Легкая лига ловкости для ежедневных тренировок.", CompetitionMode.AGILITY, 1, 8, 18, 2),
            ("Парад шарма", "Дружеская сцена, где важны стиль и шарм.", CompetitionMode.CHARM, 2, 16, 34, 4),
            ("Кубок уютной заботы", "Лига настроения для ухоженных питомцев.", CompetitionMode.MOOD, 3, 24, 48, 6),
        ]
        for name, description, stat, min_level, entry_fee, reward_coins, reward_hearts in competitions:
            CompetitionMode.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "stat": stat,
                    "min_level": min_level,
                    "entry_fee": entry_fee,
                    "reward_coins": reward_coins,
                    "reward_hearts": reward_hearts,
                    "active": True,
                },
            )

        chests = [
            ("Ежедневный ленточный сундук", "Маленький ежедневный сундук с монетами и фрагментами.", 2, 3, 18, 42, "#ef7b6a"),
            ("Садовый сундук", "Улучшенный сундук для сада и самоцветов.", 5, 2, 45, 95, "#45b08c"),
        ]
        for name, description, key_cost, daily_limit, min_coins, max_coins, color in chests:
            ChestType.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "key_cost": key_cost,
                    "daily_limit": daily_limit,
                    "min_coins": min_coins,
                    "max_coins": max_coins,
                    "color": color,
                },
            )

        gifts = [
            ("Уютная открытка", "Крошечная открытка для дружелюбного игрока.", 3, "#75a7e6"),
            ("Ленточный букет", "Радостный подарок для праздников.", 6, "#ef7b6a"),
            ("Коробка звездного печенья", "Сладкий премиальный подарок.", 9, "#f3b84b"),
        ]
        for name, description, price_hearts, color in gifts:
            GiftCatalogItem.objects.update_or_create(
                name=name,
                defaults={"description": description, "price_hearts": price_hearts, "color": color},
            )

        help_articles = [
            ("Основы", "Первые шаги", "Заботься об активном питомце, выполняй ежедневные задания и расширяй домик наградами."),
            ("Экономика", "Монеты и сердечки", "Монеты покупают предметы и улучшения. Сердечки открывают сундуки, обучают помощников и отправляют подарки."),
            ("Прогресс", "Коллекции и фрагменты", "Исследования, приключения и сундуки дают части, открывающие постоянные бонусы красоты."),
            ("Клубы", "Рост клуба", "Участники клуба жертвуют ресурсы, улучшают здания и координируются через объявления."),
        ]
        for category, title, body in help_articles:
            HelpArticle.objects.update_or_create(title=title, defaults={"category": category, "body": body, "active": True})

        forum_categories = [
            ("Доска новостей", "Обновления и объявления для локальной проверки Cozy Paws.", True),
            ("Разговоры хранителей", "Общие обсуждения игроков и советы.", False),
            ("Стол помощи", "Вопросы о питомцах, экономике, клубах и наградах.", False),
        ]
        seeded_categories = []
        for name, description, is_news in forum_categories:
            category, _ = ForumCategory.objects.update_or_create(name=name, defaults={"description": description, "is_news": is_news})
            seeded_categories.append(category)

        assistants = [
            ("Добрый заботник", "Улучшает эффективность долгосрочной заботы.", AssistantType.CARETAKER, 20, 20, 1),
            ("Стилист комнаты", "Усиливает планирование стиля и развитие комнаты.", AssistantType.STYLIST, 24, 20, 1),
            ("Разведчик троп", "Повышает шанс трофеев в исследованиях.", AssistantType.SCOUT, 22, 20, 1),
            ("Маленький строитель", "Помогает в строительстве дома и клуба.", AssistantType.BUILDER, 28, 20, 1),
        ]
        for name, description, role, base_cost, max_level, bonus_per_level in assistants:
            AssistantType.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "role": role,
                    "base_cost": base_cost,
                    "max_level": max_level,
                    "bonus_per_level": bonus_per_level,
                },
            )

        building_types = [
            ("Учебный уголок", "Добавляет личные бонусы опыта.", ClubBuildingType.XP, 2, 20, 100),
            ("Клубная библиотека", "Добавляет бонусы опыта клуба.", ClubBuildingType.CLUB_XP, 2, 20, 100),
            ("Студия дизайна", "Улучшает системы красоты дома.", ClubBuildingType.HOME, 2, 20, 120),
            ("Зал гардероба", "Улучшает бонусы красоты нарядов.", ClubBuildingType.WARDROBE, 2, 20, 120),
            ("Домик исследователя", "Улучшает системы исследований.", ClubBuildingType.EXPLORE, 2, 20, 140),
        ]
        for name, description, effect, bonus_per_level, max_level, base_cost in building_types:
            ClubBuildingType.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "effect": effect,
                    "bonus_per_level": bonus_per_level,
                    "max_level": max_level,
                    "base_cost": base_cost,
                },
            )

        demo, created = User.objects.get_or_create(username="demo")
        if created:
            demo.set_password("demo12345")
            demo.save()
        profile, _ = PlayerProfile.objects.get_or_create(user=demo, defaults={"coins": 180})
        profile.display_name = "Демо-хранитель"
        profile.coins = max(profile.coins, 180)
        profile.hearts = max(profile.hearts, 120)
        profile.save(update_fields=["display_name", "coins", "hearts"])
        GamePreference.objects.get_or_create(profile=profile)
        Pet.objects.filter(owner=demo).update(active=False)
        demo_pet, _ = Pet.objects.get_or_create(owner=demo, name="Мята", defaults={"species": Pet.FOX, "level": 2})
        demo_pet.species = Pet.FOX
        demo_pet.level = max(demo_pet.level, 2)
        demo_pet.active = True
        demo_pet.save(update_fields=["species", "level", "active"])
        demo_pet = Pet.objects.filter(owner=demo, name="Мята").first()

        for furniture in FurnitureItem.objects.order_by("price")[:2]:
            owned, _ = OwnedFurniture.objects.get_or_create(profile=profile, item=furniture)
            owned.placed = True
            owned.save(update_fields=["placed"])
        first_collection = CollectionSet.objects.order_by("name").first()
        if first_collection:
            for piece in first_collection.pieces.all()[:2]:
                owned_piece, _ = OwnedCollectionPiece.objects.get_or_create(profile=profile, piece=piece)
                owned_piece.quantity = max(owned_piece.quantity, 1)
                owned_piece.save(update_fields=["quantity"])
        first_trophy = Trophy.objects.order_by("rarity", "name").first()
        if first_trophy:
            OwnedTrophy.objects.get_or_create(profile=profile, trophy=first_trophy)
        for fragment_type in FragmentType.objects.order_by("kind", "name")[:3]:
            owned_fragment, _ = OwnedFragment.objects.get_or_create(profile=profile, fragment_type=fragment_type)
            owned_fragment.quantity = max(owned_fragment.quantity, 3)
            owned_fragment.save(update_fields=["quantity"])
        for assistant_type in AssistantType.objects.all():
            PlayerAssistant.objects.get_or_create(profile=profile, assistant_type=assistant_type)
        club, _ = Club.objects.get_or_create(
            name="Клуб уютной тропы",
            defaults={"description": "Стартовый клуб для дружелюбной локальной проверки.", "coins": 300, "hearts": 120, "level": 2},
        )
        ClubMembership.objects.get_or_create(club=club, profile=profile, defaults={"role": ClubMembership.OWNER, "contribution_score": 420})
        for building_type in ClubBuildingType.objects.all():
            ClubBuilding.objects.get_or_create(club=club, building_type=building_type, defaults={"level": 1})
        ClubHistoryEvent.objects.get_or_create(club=club, actor=profile, text="Клуб открыл свои уютные двери.")
        news_category = ForumCategory.objects.filter(is_news=True).first()
        if news_category:
            thread, _ = ForumThread.objects.get_or_create(category=news_category, title="Добро пожаловать в Cozy Paws", defaults={"author": profile, "pinned": True})
            ForumPost.objects.get_or_create(thread=thread, author=profile, body="Эта локальная сборка включает клубы, приключения, сундуки, подарки и форум.")
        starter_prompt = MemoryPrompt.objects.filter(active=True).order_by("theme", "title").first()
        if demo_pet and starter_prompt:
            starter_date = timezone.localdate() - timezone.timedelta(days=1)
            MemoryChapter.objects.filter(
                profile=profile,
                date=timezone.localdate(),
                title="Солнечный домик: первая глава",
            ).exclude(date=starter_date).update(date=starter_date)
            MemoryChapter.objects.get_or_create(
                profile=profile,
                date=starter_date,
                defaults={
                    "pet": demo_pet,
                    "prompt": starter_prompt,
                    "title": "Солнечный домик: первая глава",
                    "story": "Мята нашла теплое место у окна и сделала первый день в Cozy Paws похожим на маленький праздник.",
                    "reward_coins": 24,
                    "reward_hearts": 1,
                    "reward_experience": 10,
                    "bond_delta": 14,
                },
            )

        self.stdout.write(self.style.SUCCESS("Стартовые данные готовы. Демо-вход: demo / demo12345"))
