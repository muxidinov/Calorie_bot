
import json
import re

from anthropic import AsyncAnthropic
from config import ANTHROPIC_API_KEY

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

PROMPT_TEMPLATE = """Foydalanuvchi ovqatini matn bilan yozdi: "{text}"

Agar bu haqiqatan ham ovqat/ichimlik tavsifi bo'lsa, taxminiy porsiya og'irligi va \
oziqaviy tarkibini hisobla. Agar matn ovqatga umuman aloqasi bo'lmasa (masalan savol, \
salom yoki boshqa mavzu), "confidence": "not_food" qo'y.

Faqat quyidagi JSON formatda javob qaytar, boshqa hech qanday matn, izoh yoki markdown qo'shma:

{{"food_name": "ovqat nomi (o'zbekcha)", "grams": raqam, "calories": raqam, \
"protein": raqam, "fat": raqam, "carbs": raqam, "confidence": "high/medium/low/not_food"}}

Agar matnda bir nechta ovqat bo'lsa, ularning umumiy summasini ber."""


async def analyze_food_text(text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=text)

    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    raw_text = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError(f"AI javobini o'qib bo'lmadi: {raw_text}")

    return data
