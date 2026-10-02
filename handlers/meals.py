
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from states import MealConfirmation
from utils.ai_vision import analyze_food_image
from utils.ai_text import analyze_food_text
from database import add_meal

router = Router()

KNOWN_COMMANDS = {"/start", "/register", "/bugun", "/yogfoizi", "/challenge", "/vazn", "/stats",
                  "/hafta", "/oy"}


def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ To'g'ri", callback_data="meal_confirm"),
        InlineKeyboardButton(text="✏️ Tuzatish", callback_data="meal_correct"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="meal_cancel"),
    ]])


def format_result_text(result: dict) -> str:
    return (
        f"🍽 <b>{result['food_name']}</b>\n"
        f"⚖️ Taxminiy porsiya: {result['grams']:.0f} g\n"
        f"🔥 Kaloriya: {result['calories']:.0f} kkal\n"
        f"🥩 Oqsil: {result['protein']:.1f} g | 🧈 Yog: {result['fat']:.1f} g | 🍞 Uglevod: {result['carbs']:.1f} g\n\n"
        f"Bu to'g'rimi?"
    )


@router.message(F.photo)
async def handle_food_photo(message: Message, state: FSMContext):
    processing_msg = await message.answer("🔍 Ovqatni tahlil qilyapman...")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes_io = await message.bot.download_file(file.file_path)
    image_bytes = file_bytes_io.read()

    try:
        result = await analyze_food_image(image_bytes)
    except Exception as e:
        await processing_msg.edit_text(
            "❗️Rasmni tahlil qilib bo'lmadi. Iltimos, yorug'roq va aniqroq rasm yuboring.\n"
            f"(Texnik xato: {str(e)[:200]})"
        )
        return

    if result.get("confidence") == "low":
        await processing_msg.edit_text(
            "🤔 Ovqatni aniq tanib bo'lmadi. Yaqinroq va yorug'roq rasm yuborib qayta urinib ko'ring, "
            "yoki ovqat nomini matn bilan yozing (masalan: 'osh 350 gramm')."
        )
        return

    await state.update_data(pending_meal=result)
    await state.set_state(MealConfirmation.waiting_confirmation)
    await processing_msg.edit_text(format_result_text(result), parse_mode="HTML",
                                    reply_markup=confirmation_keyboard())


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def handle_food_text(message: Message, state: FSMContext):
    """Foydalanuvchi ovqatni matn bilan yozganda (rasmsiz)"""
    if message.text.strip() in KNOWN_COMMANDS:
        return

    processing_msg = await message.answer("🔍 Yozganingizni tahlil qilyapman...")

    try:
        result = await analyze_food_text(message.text)
    except Exception as e:
        await processing_msg.edit_text(
            "❗️Tahlil qilib bo'lmadi. Iltimos, ovqat nomini aniqroq yozing "
            "(masalan: 'osh 350 gramm' yoki '2 ta non va choy').\n"
            f"(Texnik xato: {str(e)[:200]})"
        )
        return

    if result.get("confidence") == "not_food":
        await processing_msg.edit_text(
            "Bu ovqat tavsifiga o'xshamayapti 🤔 Agar ovqat haqida yozmoqchi bo'lsangiz, "
            "masalan: 'lag'mon 400 gramm' deb yozib ko'ring.\n\n"
            "Buyruqlar: /bugun /yogfoizi /challenge /vazn /hafta /oy"
        )
        return

    if result.get("confidence") == "low":
        await processing_msg.edit_text(
            "🤔 Aniq tushunolmadim. Iltimos, ovqat va taxminiy miqdorini aniqroq yozing "
            "(masalan: 'osh 350 gramm')."
        )
        return

    await state.update_data(pending_meal=result)
    await state.set_state(MealConfirmation.waiting_confirmation)
    await processing_msg.edit_text(format_result_text(result), parse_mode="HTML",
                                    reply_markup=confirmation_keyboard())


@router.callback_query(F.data == "meal_confirm")
async def confirm_meal(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    meal = data.get("pending_meal")

    if not meal:
        await callback.answer("Ma'lumot topilmadi, qaytadan yuboring.")
        return

    await add_meal(
        user_id=callback.from_user.id,
        food_name=meal["food_name"], grams=meal["grams"],
        calories=meal["calories"], protein=meal["protein"],
        fat=meal["fat"], carbs=meal["carbs"],
    )

    await state.clear()
    await callback.message.edit_text(
        f"✅ Saqlandi: {meal['food_name']} — {meal['calories']:.0f} kkal\n\n"
        f"Kunlik hisobotni ko'rish uchun /bugun yozing."
    )
    await callback.answer()


@router.callback_query(F.data == "meal_correct")
async def correct_meal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MealConfirmation.waiting_correction)
    await callback.message.edit_text(
        "Ovqat va kaloriyasini o'zingiz yozing.\n"
        "Format: <b>nomi, gramm, kaloriya, oqsil, yog, uglevod</b>\n"
        "Masalan: <i>Osh, 350, 550, 15, 20, 70</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(MealConfirmation.waiting_correction)
async def process_correction(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) != 6:
        await message.answer("Format noto'g'ri. Masalan: Osh, 350, 550, 15, 20, 70")
        return

    try:
        name = parts[0]
        grams, calories, protein, fat, carbs = map(float, parts[1:])
    except ValueError:
        await message.answer("Raqamlarni to'g'ri kiriting. Masalan: Osh, 350, 550, 15, 20, 70")
        return

    await add_meal(
        user_id=message.from_user.id, food_name=name, grams=grams,
        calories=calories, protein=protein, fat=fat, carbs=carbs,
    )
    await state.clear()
    await message.answer(f"✅ Saqlandi: {name} — {calories:.0f} kkal")


@router.callback_query(F.data == "meal_cancel")
async def cancel_meal(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bekor qilindi. Yangi ovqat yuborishingiz mumkin.")
    await callback.answer()
