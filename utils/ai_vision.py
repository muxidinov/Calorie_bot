
import base64
import json
import re

from anthropic import AsyncAnthropic
from config import ANTHROPIC_API_KEY

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

PROMPT = """Bu rasmda qanday ovqat borligini aniqla. Taxminiy porsiya og'irligi va \
oziqaviy tarkibini hisobla. Faqat quyidagi JSON formatda javob qaytar, boshqa hech \
qanday matn, izoh yoki markdown qo'shma:

{"food_name": "ovqat nomi (o'zbekcha)", "grams": raqam, "calories": raqam, \
"protein": raqam, "fat": raqam, "carbs": raqam, "confidence": "high/medium/low"}

Agar rasmda bir nechta ovqat bo'lsa, ularning umumiy summasini ber. \
Agar ovqat aniq ko'rinmasa yoki tanib bo'lmasa, "confidence": "low" qo'y."""


async def analyze_food_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """
    Rasm baytlarini qabul qiladi, Claude'ga yuboradi va
    {"food_name", "grams", "calories", "protein", "fat", "carbs", "confidence"} qaytaradi.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_image,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )

    raw_text = response.content[0].text.strip()

    # Model ba'zan ```json ... ``` bilan o'rab yuborishi mumkin - tozalaymiz
    raw_text = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # AI JSON qaytara olmasa, xatolikni tepaga uzatamiz
        raise ValueError(f"AI javobini o'qib bo'lmadi: {raw_text}")

    return data
