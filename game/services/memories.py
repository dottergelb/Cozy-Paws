from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from game.models import MemoryChapter, MemoryPrompt, Pet, PlayerProfile


class MemoryCreationError(ValueError):
    pass


@dataclass(frozen=True)
class MemoryReward:
    coins: int
    hearts: int
    experience: int
    bond: int


THEME_SCENES = {
    MemoryPrompt.CARE: (
        "нашел самый солнечный уголок домика",
        "терпеливо ждал, пока миска наполнится любимым лакомством",
        "принес игрушку и устроился рядом",
    ),
    MemoryPrompt.EXPLORE: (
        "заметил за окном тропинку, которую раньше никто не видел",
        "вернулся с прогулки с крошечным листом в зубах",
        "уверенно повел тебя к старому садовому фонарю",
    ),
    MemoryPrompt.STYLE: (
        "проверил отражение в окне и довольно прищурился",
        "выбрал самый аккуратный аксессуар перед выходом",
        "прошелся по комнате так, будто это маленький подиум",
    ),
    MemoryPrompt.SOCIAL: (
        "оставил теплый привет для клуба",
        "поделился находкой с друзьями",
        "стал героем короткой истории в общем журнале",
    ),
}


def memory_available_today(profile):
    return not MemoryChapter.objects.filter(profile=profile, date=timezone.localdate()).exists()


def calculate_memory_reward(prompt, pet, boosted=False):
    level_bonus = max(0, pet.level - 1)
    boosted_bonus = 1 if boosted else 0
    return MemoryReward(
        coins=prompt.reward_coins + level_bonus * 2 + boosted_bonus * 12,
        hearts=prompt.reward_hearts,
        experience=prompt.reward_experience + level_bonus + boosted_bonus * 10,
        bond=prompt.bond_delta + boosted_bonus * 14,
    )


def build_memory_story(profile, pet, prompt, boosted=False):
    scenes = THEME_SCENES.get(prompt.theme, THEME_SCENES[MemoryPrompt.CARE])
    scene = scenes[(pet.id + timezone.localdate().toordinal()) % len(scenes)]
    strongest_trait = max(
        (("ловкость", pet.agility), ("послушание", pet.obedience), ("обаяние", pet.charm)),
        key=lambda item: item[1],
    )[0]
    room_bonus = profile.passive_beauty_bonus
    room_line = (
        f"Домик добавил +{room_bonus} уюта, поэтому история получилась особенно яркой."
        if room_bonus
        else "Домик пока простой, но эта глава уже делает его живее."
    )
    boost_line = " Премиальная искра добавила редкую деталь в альбом памяти." if boosted else ""
    title = f"{prompt.title}: глава {pet.bond_level}"
    story = (
        f"{pet.name} {scene}. "
        f"Главной чертой дня стало {strongest_trait}, а настроение держалось на {pet.mood}/100. "
        f"{room_line}{boost_line}"
    )
    return title, story


@transaction.atomic
def create_memory_chapter(*, profile, pet, prompt, boosted=False):
    profile = PlayerProfile.objects.select_for_update().get(pk=profile.pk)
    pet = Pet.objects.select_for_update().get(pk=pet.pk, owner=profile.user)
    prompt = MemoryPrompt.objects.get(pk=prompt.pk, active=True)
    today = timezone.localdate()

    if MemoryChapter.objects.filter(profile=profile, date=today).exists():
        raise MemoryCreationError("Сегодняшняя глава уже создана. Завтра откроется новая.")
    if pet.energy < prompt.energy_cost:
        raise MemoryCreationError("Питомцу не хватает энергии для новой главы.")
    if profile.coins < prompt.coin_cost:
        raise MemoryCreationError("Не хватает монет для этого воспоминания.")
    if boosted and profile.hearts < prompt.heart_boost_cost:
        raise MemoryCreationError("Не хватает сердечек для премиальной искры.")

    reward = calculate_memory_reward(prompt, pet, boosted=boosted)
    title, story = build_memory_story(profile, pet, prompt, boosted=boosted)

    profile.coins = profile.coins - prompt.coin_cost + reward.coins
    profile.hearts = profile.hearts - (prompt.heart_boost_cost if boosted else 0) + reward.hearts
    profile.save(update_fields=["coins", "hearts"])

    pet.change_stats(energy=-prompt.energy_cost, mood=8, hunger=-3)
    pet.add_experience(reward.experience)
    pet.add_bond(reward.bond)
    pet.save()

    try:
        return MemoryChapter.objects.create(
            profile=profile,
            pet=pet,
            prompt=prompt,
            date=today,
            title=title,
            story=story,
            reward_coins=reward.coins,
            reward_hearts=reward.hearts,
            reward_experience=reward.experience,
            bond_delta=reward.bond,
            boosted=boosted,
        )
    except IntegrityError as exc:
        raise MemoryCreationError("Сегодняшняя глава уже создана. Завтра откроется новая.") from exc
