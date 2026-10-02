
import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from states import ChallengeSetup, WeightUpdate
from database import (
    get_or_create_user, create_challenge, get_active_challenge, update_user_weight,
)
from utils.calories import calculate_daily_target, ACTIVITY_LEVELS

router = Router()


@router.message(F.text == "/challenge")
async def cmd_challenge(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)

    if not user.daily_target:
        await message.answer("Avval /register orqali profilingizni to'ldiring.")
        return

    active = await get_active_challenge(message.from_user.id)
    if active:
        today = datetime.date.today()
        days_left = (active.end_date - today).days
        days_passed = (today - active.start_date).days
        current_weight = user.weight_kg
        weight_change = round(current_weight - active.start_weight, 1)

        direction = "kamaydi" if active.goal_type == "lose" else "oshdi"
        text = (
            f"🎯 <b>Faol challenge</b>\n\n"
            f"📅 {days_passed}-kun / 30 kun ({max(0, days_left)} kun qoldi)\n"
            f"⚖️ Boshlang'ich vazn: {active.start_weight} kg\n"
            f"🎯 Maqsad vazn: {active.target_weight} kg\n"
            f"📈 Hozirgi vazn: {current_weight} kg ({abs(weight_change)} kg {direction})\n\n"
            f"Vazningizni yangilash uchun /vazn buyrug'ini yuboring."
        )
        await message.answer(text, parse_mode="HTML")
        return

    if user.goal not in ("lose", "gain"):
        await message.answer(
            "Challenge faqat 'vazn tashlash' yoki 'vazn olish' maqsadi uchun mavjud.\n"
            "Agar shu maqsadga o'tmoqchi bo'lsangiz, /register orqali profilni yangilang."
        )
        return

    goal_word = "tashlamoqchi" if user.goal == "lose" else "olmoqchi"
    await message.answer(
        f"🎯 30 kunlik challenge boshlaymiz! Siz vazn {goal_word}siz.\n"
        f"Hozirgi vazningiz: {user.weight_kg} kg\n\n"
        f"30 kun ichida qancha kilogramgacha yetishni xohlaysiz? "
        f"(masalan: {user.weight_kg - 3 if user.goal == 'lose' else user.weight_kg + 3})"
    )
    await state.set_state(ChallengeSetup.waiting_target_weight)


@router.message(ChallengeSetup.waiting_target_weight)
async def process_target_weight(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)

    try:
        target = float(message.text.replace(",", "."))
        assert 30 < target < 300
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 67)")
        return

    if user.goal == "lose" and target >= user.weight_kg:
        await message.answer("Vazn tashlash uchun maqsad hozirgi vazningizdan kichik bo'lishi kerak.")
        return
    if user.goal == "gain" and target <= user.weight_kg:
        await message.answer("Vazn olish uchun maqsad hozirgi vazningizdan katta bo'lishi kerak.")
        return

    await create_challenge(
        user_id=message.from_user.id, goal_type=user.goal,
        start_weight=user.weight_kg, target_weight=target, duration_days=30,
    )
    await state.clear()

    await message.answer(
        f"✅ Challenge boshlandi!\n"
        f"⚖️ {user.weight_kg} kg → 🎯 {target} kg (30 kun ichida)\n\n"
        f"Har kuni ovqatlaringizni kuzatib boring, vaznni /vazn orqali yangilab turing. "
        f"Holatni ko'rish uchun istalgan vaqt /challenge yozing. Omad! 💪"
    )


@router.message(F.text == "/vazn")
async def cmd_update_weight(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)
    if not user.daily_target:
        await message.answer("Avval /register orqali profilingizni to'ldiring.")
        return

    await message.answer(f"Joriy vazningiz {user.weight_kg} kg edi. Yangi vazningiz necha kg?")
    await state.set_state(WeightUpdate.waiting_new_weight)


@router.message(WeightUpdate.waiting_new_weight)
async def process_new_weight(message: Message, state: FSMContext):
    try:
        new_weight = float(message.text.replace(",", "."))
        assert 30 < new_weight < 300
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 68.5)")
        return

    user = await get_or_create_user(message.from_user.id)

    activity_key = next(
        (k for k, v in ACTIVITY_LEVELS.items() if v == user.activity), "moderate"
    )
    new_target = calculate_daily_target(
        weight_kg=new_weight, height_cm=user.height_cm, age=user.age,
        gender=user.gender, activity_key=activity_key, goal=user.goal,
    )

    await update_user_weight(message.from_user.id, new_weight, new_target)
    await state.clear()

    await message.answer(
        f"✅ Vazn yangilandi: {new_weight} kg\n"
        f"🎯 Yangi kunlik norma: {new_target:.0f} kkal\n\n"
        f"Faol challenge holatini ko'rish uchun /challenge yozing."
    )
