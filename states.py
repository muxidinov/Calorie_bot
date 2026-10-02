


class Registration(StatesGroup):
    """Bo'y -> vazn -> yosh -> jins -> faollik -> maqsad -> diet turi ketma-ketligi"""
    waiting_height = State()
    waiting_weight = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_activity = State()
    waiting_goal = State()
    waiting_diet_preference = State()


class MealConfirmation(StatesGroup):
    waiting_confirmation = State()
    waiting_correction = State()


class BodyFatMeasurement(StatesGroup):
    """Yog' foizini hisoblash uchun o'lchamlar so'raladi"""
    waiting_waist = State()
    waiting_neck = State()
    waiting_hip = State()  # faqat ayollar uchun


class ChallengeSetup(StatesGroup):
    """30 kunlik maqsad (challenge) sozlash"""
    waiting_target_weight = State()


class WeightUpdate(StatesGroup):
    """Joriy vaznni yangilash (/vazn buyrug'i)"""
    waiting_new_weight = State()
