
from aiogram import Router, F
from aiogram.types import Message

from database import get_or_create_user, get_today_summary, get_stats, get_daily_totals
from anthropic import AsyncAnthropic
from config import ANTHROPIC_API_KEY, ADMIN_ID

router = Router()
client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

DIET_TEXT = {
    "standard": "cheklovsiz oddiy ovqatlanish",
    "vegetarian": "vegetarian (go'shtsiz)",
    "high_protein": "ko'p oqsilli (sportchi uchun)",
}


async def get_advice(eaten: float, target: float, goal: str, protein: float, diet_preference: str) -> str:
    goal_text = {"lose": "vazn tashlash", "gain": "vazn olish", "maintain": "vaznni saqlash"}[goal]
    diet_text = DIET_TEXT.get(diet_preference, "cheklovsiz oddiy ovqatlanish")
    remaining = target - eaten

    prompt = (
        f"Foydalanuvchi maqsadi: {goal_text}. Ovqatlanish turi: {diet_text}. "
        f"Kunlik norma: {target:.0f} kkal. Bugun yegani: {eaten:.0f} kkal (oqsil: {protein:.0f}g). "
        f"Qolgan: {remaining:.0f} kkal.\n"
        "1-2 gapdan iborat, o'zbek tilida, do'stona va amaliy maslahat ber, "
        "ovqatlanish turini hisobga olib (masalan vegetarian bo'lsa go'shtsiz variant taklif qil). "
        "Faqat maslahat matnini qaytar, boshqa hech narsa qo'shma."
    )

    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


@router.message(F.text == "/bugun")
async def cmd_today(message: Message):
    user = await get_or_create_user(message.from_user.id)

    if not user.daily_target:
        await message.answer("Avval /register orqali profilingizni to'ldiring.")
        return

    calories, protein, fat, carbs = await get_today_summary(message.from_user.id)
    remaining = user.daily_target - calories
    percent = min(100, round(calories / user.daily_target * 100)) if user.daily_target else 0

    bar_filled = "█" * (percent // 10)
    bar_empty = "░" * (10 - percent // 10)

    text = (
        f"📊 <b>Bugungi hisobot</b>\n\n"
        f"{bar_filled}{bar_empty} {percent}%\n\n"
        f"🔥 Yegani: {calories:.0f} / {user.daily_target:.0f} kkal\n"
        f"➡️ Qolgan: {max(0, remaining):.0f} kkal\n"
        f"🥩 Oqsil: {protein:.0f}g | 🧈 Yog: {fat:.0f}g | 🍞 Uglevod: {carbs:.0f}g\n"
    )

    if calories > 0:
        try:
            advice = await get_advice(calories, user.daily_target, user.goal, protein, user.diet_preference)
            text += f"\n💡 <i>{advice}</i>"
        except Exception:
            pass

    await message.answer(text, parse_mode="HTML")


WEEKDAY_NAMES = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]


async def build_period_report(user_id: int, days: int, title: str) -> str:
    user = await get_or_create_user(user_id)
    if not user.daily_target:
        return "Avval /register orqali profilingizni to'ldiring."

    totals = await get_daily_totals(user_id, days)
    target = user.daily_target

    lines = [f"📅 <b>{title}</b>\n"]
    over_days = []
    under_days = []

    for date, total in totals:
        weekday = WEEKDAY_NAMES[date.weekday()]
        date_str = date.strftime("%d.%m")

        if total == 0:
            status = "—"
        elif total > target * 1.15:
            status = "⚠️ ko'p"
            over_days.append(date_str)
        elif total < target * 0.7:
            status = "🔻 kam"
            under_days.append(date_str)
        else:
            status = "✅"

        lines.append(f"<code>{weekday} {date_str}</code>  {total:.0f} kkal  {status}")

    total_sum = sum(t for _, t in totals)
    avg = total_sum / days if days else 0
    lines.append(f"\n📊 O'rtacha: {avg:.0f} kkal/kun (norma: {target:.0f} kkal)")

    if over_days:
        lines.append(f"\n⚠️ Normadan ko'p yegan kunlar: {', '.join(over_days)}")
    if under_days:
        lines.append(f"🔻 Normadan kam yegan kunlar: {', '.join(under_days)}")

    return "\n".join(lines)


@router.message(F.text == "/hafta")
async def cmd_week(message: Message):
    text = await build_period_report(message.from_user.id, 7, "So'nggi 7 kunlik hisobot")
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/oy")
async def cmd_month(message: Message):
    text = await build_period_report(message.from_user.id, 30, "So'nggi 30 kunlik hisobot")
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/stats")
async def cmd_stats(message: Message):
    if ADMIN_ID == 0 or message.from_user.id != ADMIN_ID:
        return

    stats = await get_stats()
    text = (
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami botga kirganlar: {stats['total_users']}\n"
        f"✅ Profilni to'ldirganlar: {stats['registered_users']}\n"
        f"🍽 Jami saqlangan ovqatlar: {stats['total_meals']}\n"
        f"📅 Bugun qo'shilgan ovqatlar: {stats['today_meals']}\n"
        f"🎯 Faol challenge'lar: {stats['active_challenges']}\n"
    )
    await message.answer(text, parse_mode="HTML")
