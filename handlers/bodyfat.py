]
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from states import BodyFatMeasurement
from database import get_or_create_user, save_body_measurements
from utils.bodyfat import calculate_body_fat, classify_body_fat

router = Router()


@router.message(F.text == "/yogfoizi")
async def cmd_bodyfat(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)

    if not user.height_cm or not user.gender:
        await message.answer("Avval /register orqali profilingizni to'ldiring.")
        return

    await message.answer(
        "📏 Yog' foizini hisoblash uchun sentimetrda o'lchamlaringiz kerak "
        "(moslashuvchan santimetr lentasi bilan o'lchang):\n\n"
        "Bel aylanangiz necha sm? (kindik balandligida o'lchang)"
    )
    await state.set_state(BodyFatMeasurement.waiting_waist)


@router.message(BodyFatMeasurement.waiting_waist)
async def process_waist(message: Message, state: FSMContext):
    try:
        waist = float(message.text.replace(",", "."))
        assert 40 < waist < 200
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 85)")
        return

    await state.update_data(waist=waist)
    await message.answer("Bo'yiningiz (bo'yin aylanasi) necha sm?")
    await state.set_state(BodyFatMeasurement.waiting_neck)


@router.message(BodyFatMeasurement.waiting_neck)
async def process_neck(message: Message, state: FSMContext):
    try:
        neck = float(message.text.replace(",", "."))
        assert 20 < neck < 60
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 38)")
        return

    data = await state.update_data(neck=neck)
    user = await get_or_create_user(message.from_user.id)

    if user.gender == "female":
        await message.answer("Yonbosh (hip) aylanangiz necha sm? (eng keng joyidan o'lchang)")
        await state.set_state(BodyFatMeasurement.waiting_hip)
    else:
        await finish_bodyfat(message, state, user, hip=None)


@router.message(BodyFatMeasurement.waiting_hip)
async def process_hip(message: Message, state: FSMContext):
    try:
        hip = float(message.text.replace(",", "."))
        assert 50 < hip < 200
    except (ValueError, AssertionError):
        await message.answer("Iltimos, to'g'ri son kiriting (masalan: 95)")
        return

    user = await get_or_create_user(message.from_user.id)
    await finish_bodyfat(message, state, user, hip=hip)


async def finish_bodyfat(message: Message, state: FSMContext, user, hip):
    data = await state.get_data()
    waist, neck = data["waist"], data["neck"]

    try:
        percent = calculate_body_fat(
            gender=user.gender, height_cm=user.height_cm,
            waist_cm=waist, neck_cm=neck, hip_cm=hip,
        )
    except (ValueError, ZeroDivisionError):
        await message.answer(
            "❗️O'lchamlarni hisoblab bo'lmadi — kiritilgan raqamlar noto'g'ri nisbatda "
            "bo'lishi mumkin. Qaytadan /yogfoizi buyrug'ini yuborib, aniqroq o'lchang."
        )
        await state.clear()
        return

    category = classify_body_fat(user.gender, percent)
    await save_body_measurements(message.from_user.id, waist, neck, hip, percent)
    await state.clear()

    await message.answer(
        f"📊 <b>Yog' foizingiz: ~{percent}%</b>\n"
        f"Toifa: {category}\n\n"
        f"⚠️ Bu — o'lchamlar asosidagi taxminiy hisob (US Navy usuli), "
        f"tibbiy asbob (DEXA yoki bioimpedans) darajasidagi aniqlikni bermaydi, "
        f"lekin vaqt o'tishi bilan o'zgarishni kuzatish uchun yetarli.",
        parse_mode="HTML",
    )
