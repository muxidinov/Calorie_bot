
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from states import Registration
from database import get_or_create_user, save_user_profile
from utils.calories import calculate_daily_target, ACTIVITY_LEVELS

router = Router()

ACTIVITY_LABELS = {
    "Harakatsiz (ofis ishi)": "sedentary",
    "Yengil faol (haftada 1-3 mashq)": "light",
    "O'rtacha faol (haftada 3-5 mashq)": "moderate",
    "Yuqori faol (haftada 6-7 mashq)": "active",
    "Juda yuqori faol (og'ir jismoniy mehnat)": "very_active",
}

GOAL_LABELS = {
    "Vazn tashlash": "lose",
    "Vaznni saqlash": "maintain",
    "Vazn olish": "gain",
}

DIET_LABELS = {
    "Oddiy (cheklovsiz)": "standard",
    "Vegetarian": "vegetarian",
    "Ko'p oqsilli (sport uchun)": "high_protein",
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)

    if user.daily_target:
        await message.answer(
            f"Xush kelibsiz qaytib! Kunlik normangiz: {user.daily_target:.0f} kkal.\n"
            f"Ovqat rasmini yuboring yoki quyidagi buyruqlardan foydalaning:\n\n"
            f"/bugun — kunlik hisobot\n"
            f"/yogfoizi — yog' foizini hisoblash\n"
            f"/challenge — 30 kunlik maqsad boshlash\n"
            f"/vazn — vaznni yangilash\n"
            f"/register — profilni qayta to'ldirish"
        )
        return

    await message.answer(
        "Assalomu alaykum! Men sizga ovqatlaringizni kuzatib borishga yordam beraman 🍽\n\n"
        "Avval qisqa anketa to'ldiraylik.\nBo'yingiz necha sm? (masalan: 175)"
    )
    await state.set_state(Registration.waiting_height)


@router.message(F.text == "/register")
async def cmd_register(message: Message, state: FSMContext):
    await message.answer("Keling, profilingizni qayta to'ldiramiz.\nBo'yingiz necha sm?")
    await state.set_state(Registration.waiting_height)


@router.message(Registration.waiting_height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text.replace(",", "."))
        assert 100 < height < 250
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 175)")
        return

    await state.update_data(height=height)
    await message.answer("Vazningiz necha kg? (masalan: 70)")
    await state.set_state(Registration.waiting_weight)


@router.message(Registration.waiting_weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        assert 30 < weight < 300
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 70)")
        return

    await state.update_data(weight=weight)
    await message.answer("Yoshingiz nechada?")
    await state.set_state(Registration.waiting_age)


@router.message(Registration.waiting_age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        assert 10 < age < 100
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri yosh kiriting (masalan: 25)")
        return

    await state.update_data(age=age)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Erkak"), KeyboardButton(text="Ayol")]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Jinsingiz?", reply_markup=kb)
    await state.set_state(Registration.waiting_gender)


@router.message(Registration.waiting_gender, F.text.in_(["Erkak", "Ayol"]))
async def process_gender(message: Message, state: FSMContext):
    gender = "male" if message.text == "Erkak" else "female"
    await state.update_data(gender=gender)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in ACTIVITY_LABELS],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Faollik darajangiz qanday?", reply_markup=kb)
    await state.set_state(Registration.waiting_activity)


@router.message(Registration.waiting_activity, F.text.in_(ACTIVITY_LABELS.keys()))
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=ACTIVITY_LABELS[message.text])

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in GOAL_LABELS],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Maqsadingiz nima?", reply_markup=kb)
    await state.set_state(Registration.waiting_goal)


@router.message(Registration.waiting_goal, F.text.in_(GOAL_LABELS.keys()))
async def process_goal(message: Message, state: FSMContext):
    await state.update_data(goal=GOAL_LABELS[message.text])

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in DIET_LABELS],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Ovqatlanish turingiz qanday?", reply_markup=kb)
    await state.set_state(Registration.waiting_diet_preference)


@router.message(Registration.waiting_diet_preference, F.text.in_(DIET_LABELS.keys()))
async def process_diet_preference(message: Message, state: FSMContext):
    data = await state.update_data(diet_preference=DIET_LABELS[message.text])

    daily_target = calculate_daily_target(
        weight_kg=data["weight"], height_cm=data["height"], age=data["age"],
        gender=data["gender"], activity_key=data["activity"], goal=data["goal"],
    )

    await save_user_profile(
        user_id=message.from_user.id,
        height_cm=data["height"], weight_kg=data["weight"], age=data["age"],
        gender=data["gender"], activity=ACTIVITY_LEVELS[data["activity"]],
        goal=data["goal"], diet_preference=data["diet_preference"],
        daily_target=daily_target,
    )

    await state.clear()
    await message.answer(
        f"Rahmat! Kunlik kaloriya normangiz: {daily_target:.0f} kkal 🎯\n\n"
        "Endi quyidagilardan foydalanishingiz mumkin:\n"
        "📸 Ovqat rasmini yuboring — tahlil qilaman\n"
        "📊 /bugun — kunlik hisobot\n"
        "📏 /yogfoizi — yog' foizini hisoblash\n"
        "🎯 /challenge — 30 kunlik maqsad boshlash\n"
        "⚖️ /vazn — vaznni yangilash",
        reply_markup=ReplyKeyboardRemove(),
    )
