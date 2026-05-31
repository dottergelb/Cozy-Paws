# Cozy Paws Product Gap Analysis

This document compares Cozy Paws with public gameplay mechanics observed on mpets.mobi and adjacent public descriptions of that game. It is a functional analysis only. Do not copy mpets.mobi branding, text, images, CSS, HTML, item names, or unique visual presentation.

## Sources Reviewed

- https://mpets.mobi/welcome
- https://mpets.mobi/start
- https://mpets.mobi/
- https://mpets.mobi/profile
- https://mpets.mobi/categories
- https://mpets.mobi/items?category=food
- https://mpets.mobi/items?category=play
- https://mpets.mobi/items?category=effect
- https://mpets.mobi/sets
- https://mpets.mobi/gear
- https://mpets.mobi/chest
- https://mpets.mobi/chat
- https://mpets.mobi/view_posters
- https://mpets.mobi/settings
- https://on-game.mobi/arcade/mpets.html

## Already Covered In Cozy Paws

- Account registration, login, logout.
- Initial pet creation/selection.
- Pet profile with level, experience, currency, and care stats.
- Basic care actions: feed, play, pet, walk.
- Shop, inventory, item usage.
- Daily quests and rewards.
- Player rating.
- Profile settings.
- Achievements and action history.
- Mobile-first interface.
- Production configuration with `DATABASE_URL`, PostgreSQL support, WhiteNoise, Gunicorn, and health check.

## Functional Gaps Worth Adding

### 1. Appearance System

Observed pattern: mpets has a dedicated clothing/equipment surface with multiple slots, a wardrobe/chest, and shop categories for outfits/accessories.

Recommended Cozy Paws implementation:

- Add `EquipmentSlot`, `WearableItem`, `OwnedWearable`, and `EquippedWearable` models.
- Add slots such as outfit, collar, hat, charm, background.
- Add wardrobe page separate from consumable inventory.
- Add equip/unequip/sell actions.
- Give wearables stat bonuses such as beauty, mood, quest bonus, or show score.

Priority: high. This adds long-term collection goals.

### 2. Beauty / Style Stat

Observed pattern: profile/shop pages emphasize a beauty-like stat that grows through food, toys, and clothing.

Recommended Cozy Paws implementation:

- Add `beauty` to `Pet`.
- Let some items permanently increase beauty.
- Let wearables add temporary/equipped beauty.
- Use beauty in future competitions and rankings.

Priority: high. It gives non-level progression.

### 3. Competitions / Shows

Observed pattern: public descriptions mention training, shows, medals, and showing pets against others.

Recommended Cozy Paws implementation:

- Add timed pet shows with entry requirements.
- Score entries from level, beauty, mood, energy, and random variance.
- Award medals, coins, experience, and profile badges.
- Add leaderboards per show season.

Priority: high. This is the main missing meta-game loop.

### 4. Training

Observed pattern: public descriptions mention training as a way to prepare pets.

Recommended Cozy Paws implementation:

- Add training actions with cooldowns.
- Add trainable traits such as agility, obedience, charm.
- Use traits in competitions.
- Add training items or boosts.

Priority: medium-high. It supports competitions and gives more daily decisions.

### 5. Social Layer

Observed pattern: mpets exposes global chat, mail, friends, blacklist, and player-to-player profile links.

Recommended Cozy Paws implementation:

- Add friend requests.
- Add private messages.
- Add basic moderation controls: report, mute/block user.
- Add global chat with rate limit and minimum account age.
- Keep chat optional for production; moderation is mandatory before opening it publicly.

Priority: medium. Valuable, but moderation burden is real.

### 6. Multiple Currencies

Observed pattern: mpets has several counters, including soft currency and premium/social currency.

Recommended Cozy Paws implementation:

- Keep coins as soft currency.
- Add hearts as care/social currency earned from pet actions and quests.
- Optionally add gems only if monetization is planned.
- Avoid paid mechanics until legal/compliance requirements are clear.

Priority: medium.

### 7. Account Persistence Prompt

Observed pattern: anonymous/quick-start flow exists, with prompts to save before using some social functions.

Recommended Cozy Paws implementation:

- Add guest mode only if needed for conversion.
- If added, restrict social/chat/rating until account is saved.
- Provide a clear account-save flow.

Priority: low-medium. Current full registration is simpler and safer.

### 8. Anti-Spam / Rate Limits

Observed pattern: mpets displays a click-speed warning.

Recommended Cozy Paws implementation:

- Add server-side cooldowns for pet actions.
- Add rate limits for chat, messages, buying, and quest claiming.
- Add clear user-facing cooldown messages.

Priority: high for production.

### 9. Online Counter / Presence

Observed pattern: mpets displays online user count.

Recommended Cozy Paws implementation:

- Track recent activity timestamp on profile.
- Show count of active players in the last 5 minutes.
- Use cache if traffic grows.

Priority: low. Good atmosphere, not core gameplay.

### 10. Support / Reports

Observed pattern: support and complaint links exist.

Recommended Cozy Paws implementation:

- Add support ticket model.
- Add report model for chat/profile/message abuse.
- Add admin filters for unresolved reports.

Priority: medium-high if social features are added.

## Recommended Implementation Order

1. Add action cooldowns and rate-limit protections.
2. Add beauty stat and item effects.
3. Add wardrobe/wearable equipment.
4. Add competitions/shows and medals.
5. Add friends and private messages.
6. Add moderated global chat.
7. Add support/report workflow.
8. Add online presence counter.
9. Consider guest mode only after measuring registration friction.

## Implementation Status

Implemented in Cozy Paws:

- Server-side cooldowns for pet actions, buying, quest claiming, training, shows, chat, messages, and support tickets.
- `beauty`, `agility`, `obedience`, and `charm` pet progression stats.
- Hearts as a second non-premium currency.
- Consumable item effects for beauty and hearts.
- Wardrobe system with wearable shop, ownership, equip, unequip, sell, slots, and wearable bonuses.
- Competitions/shows with level requirements, entry fees, score calculation, medals, and rewards.
- Training actions for agility, obedience, and charm.
- Friend requests, accepting friends, blocking profiles.
- Private messages.
- Moderated global chat with report flow.
- Support tickets.
- Online presence counter based on recent activity.
- Admin registration for all new moderation and gameplay models.

Deferred intentionally:

- Guest mode. Current registration-first flow is simpler and avoids edge cases around anonymous state migration, chat abuse, and account recovery.
- Paid/premium currency. This requires legal/compliance and payment-provider decisions before implementation.

## Non-Goals

- Do not copy mpets.mobi UI, layout, icons, images, item names, texts, or brand.
- Do not implement premium currency or payment logic without legal/compliance planning.
- Do not add public chat without moderation and rate limiting.
