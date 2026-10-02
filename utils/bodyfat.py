
import math


def calculate_body_fat(gender: str, height_cm: float, waist_cm: float,
                        neck_cm: float, hip_cm: float = None) -> float:
    if gender == "male":
        value = 495 / (
            1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)
        ) - 450
    else:
        value = 495 / (
            1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm)
            + 0.22100 * math.log10(height_cm)
        ) - 450
    return round(max(3, min(60, value)), 1)


def classify_body_fat(gender: str, percent: float) -> str:
    if gender == "male":
        ranges = [
            (6, "Sportchi darajasi 💪"),
            (14, "Fitness / sog'lom 🏃"),
            (18, "O'rtacha ⚖️"),
            (25, "Yuqori ⚠️"),
            (100, "Juda yuqori 🔴"),
        ]
    else:
        ranges = [
            (14, "Sportchi darajasi 💪"),
            (21, "Fitness / sog'lom 🏃"),
            (25, "O'rtacha ⚖️"),
            (32, "Yuqori ⚠️"),
            (100, "Juda yuqori 🔴"),
        ]
    for limit, label in ranges:
        if percent <= limit:
            return label
    return ranges[-1][1]
