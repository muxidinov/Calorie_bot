
ACTIVITY_LEVELS = {
    "sedentary": 1.2,        # deyarli harakatsiz (ofis ishi)
    "light": 1.375,          # haftada 1-3 marta yengil mashq
    "moderate": 1.55,        # haftada 3-5 marta mashq
    "active": 1.725,         # haftada 6-7 marta mashq
    "very_active": 1.9,      # og'ir jismoniy mehnat / kundalik intensiv mashq
}

GOAL_ADJUSTMENT = {
    "lose": -500,      # ozish uchun taxminan haftada 0.5 kg
    "maintain": 0,      # vaznni saqlash
    "gain": 500,        # vazn olish uchun
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor formulasi"""
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def calculate_daily_target(weight_kg: float, height_cm: float, age: int,
                            gender: str, activity_key: str, goal: str) -> float:
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = bmr * ACTIVITY_LEVELS[activity_key]
    target = tdee + GOAL_ADJUSTMENT[goal]
    return round(target)
