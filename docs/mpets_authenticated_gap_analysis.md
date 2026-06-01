# Cozy Paws: Authenticated Mpets Gap Analysis

Дата обзора: 2026-06-01

Этот документ составлен после авторизованного просмотра mpets.mobi. Использовать только как функциональный и продуктовый ориентир. Нельзя копировать бренд, название, тексты, изображения, иконки, CSS, HTML, JS, персонажей, item naming или уникальную визуальную подачу mpets.mobi.

## Просмотренные разделы

- Главная игровая страница.
- Профиль питомца.
- Магазин и категории магазина.
- Еда, игры, домик, бонусы.
- Задания.
- Рейтинг.
- Тренировка.
- Работники.
- Драгоценности.
- Зимний сад.
- Поляна.
- Прогулки.
- Выставка.
- Скачки.
- Снежки.
- Золотые сундуки.
- Клуб.
- Форум, новости, чат.
- Почта, друзья, черный список.
- Коллекции, призы, медали, подарки.
- Настройки игры.
- Онлайн-список.
- Служба поддержки.

## Главные наблюдения

mpets устроен как очень плотная мобильная браузерная игра: почти каждый экран короткий, быстрый, с одной-двумя основными кнопками и множеством долгосрочных счетчиков. Основная ценность не в сложном интерфейсе, а в количестве параллельных прогрессий.

У игрока одновременно развиваются:

- уровень питомца;
- опыт и рейтинг;
- красота;
- мягкая валюта;
- социальная/дополнительная валюта;
- домик;
- одежда и шкаф;
- медали;
- призы и кубки;
- подарки;
- коллекции;
- сад;
- драгоценности;
- работники;
- клубный прогресс;
- рейтинги отдельных режимов;
- задания и события.

Для Cozy Paws это значит: базовая игра уже есть, но следующая большая цель - добавить долгую мета-игру, где игрок каждый день закрывает маленькие действия и видит, что несколько коллекций понемногу растут.

## Что Уже Есть В Cozy Paws

- Регистрация, вход, выход.
- Профиль игрока.
- Питомцы и выбор активного питомца.
- Карточка питомца со статами.
- Базовые действия с питомцем.
- Опыт, уровни, энергия.
- Монеты и hearts.
- Магазин предметов.
- Инвентарь и использование предметов.
- Wearable shop, wardrobe, equip, unequip, sell.
- Красота, agility, obedience, charm.
- Тренировка.
- Выставки/shows с наградами.
- Ежедневные задания.
- Achievements и action log.
- Рейтинг.
- Friends, blocks, private messages.
- Global chat, reports, support tickets.
- Online presence.
- PostgreSQL/Docker/local network run.

## Самые Важные Gap'ы

### 1. Домик Как Отдельная Прогрессия

В mpets домик не просто декоративная страница. Это отдельная коллекционная зона с предметами, заполнением слотов и бонусом к прогрессии.

В Cozy Paws сейчас нет полноценного домика.

Что добавить:

- `HomeRoom` или `PetHome`.
- `HomeItem`, `OwnedHomeItem`, `PlacedHomeItem`.
- Слоты или категории: bed, toy corner, window, rug, plant, poster.
- Бонусы от предметов: beauty, mood cap, xp bonus, coin bonus.
- Страница `/home/` с текущим домиком.
- Магазин мебели как отдельная вкладка магазина.
- Ограничение вместимости и апгрейд домика.

Приоритет: very high.

### 2. Коллекции И Обмен Частями

У mpets есть отдельный слой коллекций: наборы состоят из частей, части копятся, их можно добирать и обменивать через клубный/социальный контур.

В Cozy Paws пока нет такой системы.

Что добавить:

- `CollectionSet`.
- `CollectionPiece`.
- `OwnedCollectionPiece`.
- `CompletedCollection`.
- Награда за завершение набора: beauty, title, coins, avatar frame.
- Дубликаты частей.
- Простая внутриигровая просьба/обмен дубликатами.
- Отдельная страница `/collections/`.

Приоритет: very high.

### 3. Призы, Кубки И Медали Как Постоянные Бонусы

В mpets медали/призы/кубки выглядят как отдельные постоянные достижения, которые дают накопительные бонусы.

В Cozy Paws есть `ShowEntry.medal`, но нет отдельной коллекции трофеев.

Что добавить:

- `Trophy`.
- `OwnedTrophy`.
- Типы: medal, prize, cup, badge.
- Источник получения: show, race, quest, event, collection.
- Постоянные бонусы к beauty/show power/profile score.
- Страница `/trophies/`.
- Отображение части трофеев в профиле.

Приоритет: very high.

### 4. Клубы

Клуб в mpets - большой социальный и экономический контур: уровень клуба, опыт, копилка, роли, участники, постройки, клубный форум/чат, набор, объявления, история, обмен коллекциями.

В Cozy Paws есть социальные функции, но нет клубов.

Что добавить:

- `Club`.
- `ClubMembership` with roles.
- `ClubJoinRequest`.
- `ClubContribution`.
- `ClubBuilding`.
- Club treasury: coins/hearts balance.
- Club chat or club thread.
- Club announcements.
- Club history log.
- Club leaderboard.
- Club collection exchange later.

Приоритет: high.

### 5. Работники / Помощники

В mpets работники являются permanent upgrade layer: игрок вкладывает валюту, а работники усиливают другие системы.

В Cozy Paws такого нет.

Что добавить:

- `AssistantType`.
- `PlayerAssistant`.
- Уровни помощников.
- Стоимость тренировки.
- Бонусы к конкретным системам:
  - caretaker: больше mood/hunger от care actions;
  - stylist: больше beauty от wardrobe;
  - gardener: лучше сад;
  - jeweler: лучше драгоценности;
  - trainer: дешевле training;
  - scout: лучше прогулки.

Приоритет: high.

### 6. Сад И Драгоценности

В mpets есть две похожие коллекционные подсистемы: сад из семян и драгоценности из частей. Они дают beauty и требуют накопления фрагментов.

В Cozy Paws этого нет.

Что добавить:

- Общий механизм `FragmentCollection`, чтобы не плодить разные реализации.
- Garden layer:
  - `SeedType`;
  - `OwnedSeed`;
  - `Flower`;
  - planting/harvest action.
- Jewel layer:
  - `GemType`;
  - `GemShard`;
  - crafted gem.
- Правило: N fragments -> 1 permanent collectible.
- Бонусы beauty/profile score.

Приоритет: high.

### 7. Поляна / Поиск Ресурсов

В mpets поляна - отдельный action sink: игрок тратит ресурс или попытку, получает шанс найти части для сада, шанс улучшается навыками.

В Cozy Paws walk сейчас проще.

Что добавить:

- `/explore/` или `/meadow/`.
- Daily attempts.
- Несколько территорий с unlock по уровню.
- Разные таблицы наград.
- Влияние trait/assistant на шанс.
- Результаты: seeds, shards, collection pieces, small coins.

Приоритет: high.

### 8. Длинные Прогулки

В mpets прогулки имеют длительность: 3, 4, 8, 12 часов, с наградой после ожидания и рекордами за сутки.

В Cozy Paws прогулка сейчас как быстрый action.

Что добавить:

- `PetAdventure`.
- Start/finish flow.
- Длительность зависит от уровня.
- Награда после завершения.
- Daily adventure score.
- Возможность отправлять питомца на долгую активность без постоянного клика.

Приоритет: medium-high.

### 9. Соревновательные Очереди: Скачки И Снежки

В mpets есть отдельные режимы с очередью, лигами, рейтингом режима и заданиями на участие.

В Cozy Paws есть shows, но нет queue-based мини-соревнований.

Что добавить:

- `CompetitionMode`.
- `CompetitionQueueEntry`.
- `CompetitionMatch`.
- Modes:
  - races: agility/speed based;
  - snowball-like original mode: reaction/charm based, but with a Cozy Paws-original theme;
  - cozy contest: care/mood based.
- Лиги по рейтингу.
- Награды за участие и призовые места.

Приоритет: medium-high.

### 10. Сундуки, Ключи И Публичная Лента Наград

В mpets сундуки работают как ежедневный reward sink с ключами, лимитами и публичной лентой последних выигрышей.

В Cozy Paws этого нет.

Что добавить:

- `ChestType`.
- `ChestKey`.
- `ChestReward`.
- Daily open limit.
- Keys earned from shows/adventures/quests.
- Public reward feed with privacy-safe names.
- Admin-configurable reward weights.

Приоритет: medium-high.

### 11. Расширенные Задания

В mpets задания делятся на daily/single/all, связаны с конкретными режимами и показывают прогресс.

В Cozy Paws daily quests есть, но можно расширить структуру.

Что добавить:

- Quest categories: daily, weekly, one-time, event, club.
- Quest chains.
- Quest detail page.
- Multi-reward display.
- Quest requirements tied to trophies, collections, races, adventures, club contribution.

Приоритет: medium-high.

### 12. Форум И Новости

В Cozy Paws есть чат и личные сообщения, но нет форума.

Что добавить:

- `ForumCategory`.
- `ForumThread`.
- `ForumPost`.
- Read/unread state.
- Pinned/locked threads.
- Moderator list.
- Report post.
- News category managed by admin.

Приоритет: medium.

### 13. Подарки

У mpets подарки являются отдельной социальной памятью профиля.

В Cozy Paws подарков нет.

Что добавить:

- `GiftCatalogItem`.
- `SentGift`.
- Gift message.
- Gift privacy/moderation.
- Profile gift shelf.
- Gifts bought with hearts or event tokens.

Приоритет: medium.

### 14. Почта, Друзья И Черный Список

Cozy Paws уже имеет private messages, friends и blocks, но UX можно усилить.

Что улучшить:

- Conversation detail page instead of only inbox/send.
- Read/unread states.
- Mark all as read.
- Delete/hide conversation.
- Friend list page.
- Block list page.
- Reply shortcut from chat/profile.

Приоритет: medium.

### 15. Настройки Игры

В mpets есть настройки удобства интерфейса: нижнее меню и кнопки действий.

В Cozy Paws можно добавить:

- Compact mode.
- Low bandwidth mode.
- Show/hide bottom nav.
- Show/hide quick actions.
- Theme selector.
- Reduced animation toggle.

Приоритет: medium.

### 16. Служба Поддержки С Базой Помощи

Cozy Paws имеет support tickets, но mpets сначала ведет к помощи, а потом к созданию обращения.

Что добавить:

- `/help/`.
- Help categories.
- Suggested article before ticket creation.
- Ticket categories.
- Ticket statuses and conversation thread.
- Admin assignment.

Приоритет: medium.

## Предлагаемый Roadmap

### Sprint 1: Long-Term Rewards Core

1. Trophies: prizes/cups/medals as permanent bonuses.
2. Collections with pieces and completion rewards.
3. Home with furniture bonuses.
4. Profile blocks for trophies, home, collections.

Почему первым: это сразу добавит долгосрочную мотивацию без сложной модерации.

### Sprint 2: Resource Loops

1. Meadow/explore with daily attempts.
2. Garden fragments -> flowers.
3. Jewel shards -> gems.
4. Workers/assistants that boost these systems.

Почему вторым: появятся ежедневные действия, которые кормят коллекции.

### Sprint 3: Clubs

1. Clubs, membership, roles.
2. Club treasury and contribution.
3. Club announcements/history.
4. Club leaderboard.
5. Club collection exchange.

Почему третьим: клубы сильно увеличивают retention, но требуют больше правил и модерации.

### Sprint 4: More Competitions

1. Adventure/walk timers.
2. Queue-based races.
3. Original themed multiplayer contest.
4. Mode-specific ratings and leagues.
5. Weekly rewards.

Почему четвертым: когда есть коллекции/traits/workers, соревнования получают больше смысла.

### Sprint 5: Social Polish

1. Forum/news.
2. Gifts.
3. Better inbox.
4. Friend and block list pages.
5. Help center before support ticket.

Почему пятым: это повышает зрелость проекта, но требует аккуратной модерации.

### Sprint 6: UX And Operations

1. Game settings page.
2. Low bandwidth mode.
3. Admin economy dashboard.
4. Reward feed.
5. Event configuration.
6. Audit logs for economy-sensitive actions.

Почему шестым: это делает проект удобнее поддерживать и балансировать.

## Самый Ближайший Практичный План

Если продолжать автономную разработку, лучший следующий блок:

1. Добавить trophies/prizes/cups.
2. Добавить collections with pieces.
3. Добавить home/furniture.
4. Добавить explore action, который выдает collection pieces/seeds/shards.
5. Покрыть это тестами и пройти кнопки в браузере.

Это даст Cozy Paws новый слой прогрессии, который заметно приблизит игру к полноценному long-term pet browser game, но останется оригинальным по названию, визуалу и реализации.

## Non-Goals

- Не копировать mpets.mobi пиксель-в-пиксель.
- Не использовать чужие ассеты, тексты, названия предметов, логотипы или HTML/CSS/JS.
- Не добавлять реальные платежи без отдельного legal/compliance проекта.
- Не открывать сложные социальные функции без модерации, rate limits и отчетности.
