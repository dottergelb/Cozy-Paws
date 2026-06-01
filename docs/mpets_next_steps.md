# Mpets-Inspired Next Steps For Cozy Paws

This document lists mechanics and product surfaces observed from public mpets.mobi pages and compares them with the current Cozy Paws implementation.

Important boundary: use this as functional inspiration only. Do not copy mpets.mobi brand, names, texts, graphics, HTML, CSS, icons, item names, or distinctive visual presentation.

## Sources Reviewed

- https://mpets.mobi/
- https://mpets.mobi/start
- https://mpets.mobi/about_all
- https://mpets.mobi/agreement_all
- https://mpets.mobi/privacy_all
- https://mpets.mobi/rules1
- https://mpets.mobi/rules2
- indexed public prize pages such as `view_prizes`
- current Cozy Paws codebase models/routes/templates

## What Cozy Paws Already Has

- Registration, login, logout.
- Starter pet and multiple pets.
- Pet stats: level, experience, energy, mood, hunger, beauty, agility, obedience, charm.
- Pet actions: feed, play, pet, walk.
- Passive energy recovery.
- Coins and hearts.
- Item shop, inventory, item usage.
- Wearable shop, wardrobe, equip, unequip, sell.
- Daily quests.
- Achievements and action log.
- Training.
- Shows with entry fees, score, medals, and rewards.
- Rating.
- Friends, blocks, private messages.
- Global chat, chat report flow, support tickets.
- Online presence counter.
- PostgreSQL-ready production config.

## Gaps Still Worth Building

### 1. Trophy And Prize Collection

Observed mpets pattern:

- Public prize pages show long trophy/prize collections.
- Prizes give cumulative beauty bonuses.
- Prize collections appear separate from ordinary clothing.

Current Cozy Paws state:

- We have `ShowEntry.medal`, but no persistent collectible prize catalog.

Recommended implementation:

- Add `Prize` model with rarity, source show, beauty bonus, and display color/icon.
- Add `OwnedPrize` model per profile or pet.
- Shows should award a prize on first gold/silver/bronze milestone.
- Add `/prizes/` page showing collected and locked prizes.
- Add cumulative `prize_beauty_bonus` into `Pet.show_power`.

Priority: high.

### 2. Show Seasons And Country/Theme Ladder

Observed mpets pattern:

- Prize pages imply a ladder of themed championship wins with escalating beauty bonuses.

Current Cozy Paws state:

- Shows are static and independent.

Recommended implementation:

- Add `ShowSeason` and `ShowTier`.
- Each tier has unlock requirements: level, beauty, previous medal, entry fee.
- Add season progress page.
- Add resettable weekly/monthly leaderboards.

Priority: high.

### 3. Forum

Observed mpets pattern:

- Agreement explicitly mentions forum and chat as part of the game.

Current Cozy Paws state:

- We have global chat, private messages, reports, and support.
- We do not have persistent forum threads.

Recommended implementation:

- Add `ForumCategory`, `ForumThread`, `ForumPost`.
- Add lock/pin/hidden moderation flags.
- Add per-user post cooldown.
- Add admin tools for moderation.

Priority: medium-high.

### 4. Item Exchange / Trading

Observed mpets pattern:

- Agreement mentions technical ability to exchange game items between users.

Current Cozy Paws state:

- We have inventory and wardrobe ownership.
- No player-to-player trade.

Recommended implementation:

- Add `TradeOffer` and `TradeOfferItem`.
- Allow consumables, wearables, hearts/coins only if balance is acceptable.
- Add accept/cancel/decline states.
- Add anti-abuse limits and audit log.

Priority: medium-high.

### 5. Account Save / Guest Conversion Flow

Observed mpets pattern:

- Start page allows fast pet selection before full account commitment.
- Login/welcome has password recovery.

Current Cozy Paws state:

- Registration-first flow only.
- No guest mode and no password reset UI.

Recommended implementation:

- Add optional guest session with temporary pet and limited actions.
- Add conversion page to create username/password and persist progress.
- Add Django password reset views with email backend configuration.

Priority: medium.

### 6. Password Recovery

Observed mpets pattern:

- Welcome/login page exposes password recovery.

Current Cozy Paws state:

- No password reset flow.

Recommended implementation:

- Add Django `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, `PasswordResetCompleteView`.
- Add templates.
- Add env docs for SMTP.

Priority: high for production.

### 7. Legal And Rules Pages

Observed mpets pattern:

- Public pages expose agreement, privacy policy, game rules, and communication rules.
- Agreement describes user content, chat/forum rules, sanctions, paid feature terms, and support/contact expectations.

Current Cozy Paws state:

- README has developer docs.
- App has no public rules/privacy/terms pages.

Recommended implementation:

- Add `/terms/`, `/privacy/`, `/rules/`, `/chat-rules/`.
- Use original Cozy Paws text drafted for this project.
- Link these pages from footer/auth pages.
- Add consent checkbox during registration if legal requirements demand it.

Priority: high before public launch.

### 8. Moderation Sanctions

Observed mpets pattern:

- Agreement/rules refer to limitations and sanctions for violations.

Current Cozy Paws state:

- We have reports and hidden chat flag, but no sanction model.

Recommended implementation:

- Add `UserSanction` model: mute, chat ban, message ban, login ban.
- Enforce sanctions in chat/messages/social.
- Add admin filters for active sanctions.
- Add reason and expiry timestamp.

Priority: high if social features are public.

### 9. Notification Preferences

Observed mpets pattern:

- Agreement describes notifications and user ability to regulate them.

Current Cozy Paws state:

- No notifications or preference center.

Recommended implementation:

- Add `Notification` and `NotificationPreference`.
- In-app notifications first.
- Optional email notifications later.
- Add settings toggles for messages, friends, shows, support.

Priority: medium.

### 10. Premium / Expanded Features

Observed mpets pattern:

- Agreement describes paid expanded functionality and payment flows.

Current Cozy Paws state:

- No premium currency or payments, intentionally.

Recommended implementation:

- Do not implement payments yet.
- If needed later, first define legal, refund, platform, parental/age, tax, and moderation policy.
- Consider non-paid supporter cosmetics before gameplay advantages.

Priority: low until product/legal direction is clear.

### 11. Better Mobile Web Constraints

Observed mpets pattern:

- The game is built around very lightweight mobile web pages.

Current Cozy Paws state:

- UI is responsive and mobile-first, but richer than classic lightweight browser games.

Recommended implementation:

- Add low-bandwidth mode toggle.
- Avoid heavy assets.
- Add page-weight budget.
- Add no-JS fallback for every core action.

Priority: medium.

### 12. Stronger Economy Balance Tools

Observed mpets pattern:

- Mature pet games usually rely on long progression ladders, rewards, item sinks, and collection bonuses.

Current Cozy Paws state:

- Economy exists but is simple.

Recommended implementation:

- Add admin-editable economy config.
- Add item rarity and limited shop rotations.
- Add daily login rewards.
- Add coin/hearts sinks: training fees, show entries, wardrobe upgrades, prize upgrades.
- Add analytics counters for generated/spent currency.

Priority: medium-high.

## Recommended Build Order

1. Password recovery.
2. Public legal/rules/privacy pages.
3. Moderation sanctions.
4. Prize collection and prize beauty bonuses.
5. Show seasons/tier ladder.
6. Forum.
7. Item trading.
8. Notification preferences.
9. Daily login rewards and rotating shop.
10. Guest-to-account conversion.
11. Low-bandwidth mode.
12. Premium/supporter features only after legal/product review.

## Immediate Next Sprint Proposal

Best next sprint:

- Add password reset.
- Add terms/privacy/rules/chat-rules pages.
- Add moderation sanctions and enforce mutes in chat/messages.
- Add prize collection model and `/prizes/` page.

Reason:

- This improves production readiness and gives the shows system a stronger long-term reward loop.
- It also closes the biggest public-launch gaps before adding more social complexity.
