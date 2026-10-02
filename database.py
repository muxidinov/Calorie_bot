
import datetime
from sqlalchemy import String, Integer, Float, Date, ForeignKey, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import DATABASE_URL


class Base(DeclarativeBase):
    pass



class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)              # Telegram user_id
    height_cm: Mapped[float] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String, nullable=True)      # "male" / "female"
    activity: Mapped[float] = mapped_column(Float, nullable=True)   # faollik koeffitsienti
    goal: Mapped[str] = mapped_column(String, nullable=True)        # "lose" / "gain" / "maintain"
    diet_preference: Mapped[str] = mapped_column(String, nullable=True)  # "standard"/"vegetarian"/"high_protein"
    daily_target: Mapped[float] = mapped_column(Float, nullable=True)  # kunlik kaloriya normasi

    waist_cm: Mapped[float] = mapped_column(Float, nullable=True)
    neck_cm: Mapped[float] = mapped_column(Float, nullable=True)
    hip_cm: Mapped[float] = mapped_column(Float, nullable=True)
    body_fat_percent: Mapped[float] = mapped_column(Float, nullable=True)

    meals: Mapped[list["Meal"]] = relationship(back_populates="user")


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
        date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    food_name: Mapped[str] = mapped_column(String)
    grams: Mapped[float] = mapped_column(Float)
    calories: Mapped[float] = mapped_column(Float)
    protein: Mapped[float] = mapped_column(Float)
    fat: Mapped[float] = mapped_column(Float)
    carbs: Mapped[float] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="meals")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    start_date: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    end_date: Mapped[datetime.date] = mapped_column(Date)
    goal_type: Mapped[str] = mapped_column(String)          # "lose" yoki "gain"
    start_weight: Mapped[float] = mapped_column(Float)
    target_weight: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="active")  # active/finished


engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(user_id: int) -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user is None:
            user = User(id=user_id)
            session.add(user)
            await session.commit()  
            await session.refresh(user)
        return user


async def save_user_profile(user_id: int, height_cm, weight_kg, age, gender, activity, goal,
                             diet_preference, daily_target):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user is None:
            user = User(id=user_id)
            session.add(user)
        user.height_cm = height_cm
        user.weight_kg = weight_kg
        user.age = age
        user.gender = gender
        user.activity = activity
        user.goal = goal
        user.diet_preference = diet_preference
        user.daily_target = daily_target
        await session.commit()


async def update_user_weight(user_id: int, new_weight: float, new_daily_target: float):
    """Vaznni yangilaydi va kunlik normani qayta hisoblaydi."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.weight_kg = new_weight
            user.daily_target = new_daily_target
            await session.commit()


async def save_body_measurements(user_id: int, waist_cm: float, neck_cm: float,
                                  hip_cm, body_fat_percent: float):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.waist_cm = waist_cm
            user.neck_cm = neck_cm
            user.hip_cm = hip_cm
            user.body_fat_percent = body_fat_percent
            await session.commit()


async def add_meal(user_id: int, food_name, grams, calories, protein, fat, carbs):
    async with async_session() as session:
        meal = Meal(
            user_id=user_id, food_name=food_name, grams=grams,
            calories=calories, protein=protein, fat=fat, carbs=carbs
        )
        session.add(meal)
        await session.commit()


async def create_challenge(user_id: int, goal_type: str, start_weight: float,
                            target_weight: float, duration_days: int = 30):
    async with async_session() as session:
        old = (await session.execute(
            select(Challenge).where(Challenge.user_id == user_id, Challenge.status == "active")
        )).scalars().all()
        for ch in old:
            ch.status = "finished"

        challenge = Challenge(
            user_id=user_id,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=duration_days),
            goal_type=goal_type,
            start_weight=start_weight,
            target_weight=target_weight,
            status="active",
        )
        session.add(challenge)
        await session.commit()
        await session.refresh(challenge)
        return challenge


async def get_active_challenge(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Challenge).where(Challenge.user_id == user_id, Challenge.status == "active")
        )
        return result.scalars().first()


async def get_stats():
    async with async_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar()
        registered_users = (await session.execute(
            select(func.count(User.id)).where(User.daily_target.is_not(None))
        )).scalar()
        total_meals = (await session.execute(select(func.count(Meal.id)))).scalar()
        today_meals = (await session.execute(
            select(func.count(Meal.id)).where(Meal.date == datetime.date.today())
        )).scalar()
        active_challenges = (await session.execute(
            select(func.count(Challenge.id)).where(Challenge.status == "active")
        )).scalar()
        return {
            "total_users": total_users,
            "registered_users": registered_users,
            "total_meals": total_meals,
            "today_meals": today_meals,
            "active_challenges": active_challenges,
        }


async def get_daily_totals(user_id: int, days: int):
    """So'nggi N kunlik har bir kun bo'yicha jami kaloriya ro'yxatini qaytaradi."""
    start_date = datetime.date.today() - datetime.timedelta(days=days - 1)
    async with async_session() as session:
        result = await session.execute(
            select(Meal.date, func.sum(Meal.calories))
            .where(Meal.user_id == user_id, Meal.date >= start_date)
            .group_by(Meal.date)
        )
        totals_by_date = {row[0]: row[1] for row in result.all()}
 for i in range(days):
        d = start_date + datetime.timedelta(days=i)
        full_list.append((d, totals_by_date.get(d, 0)))
    return full_list


async def get_today_summary(user_id: int):
    today = datetime.date.today()
    async with async_session() as session:
        result = await session.execute(
            select(
                func.coalesce(func.sum(Meal.calories), 0),
                func.coalesce(func.sum(Meal.protein), 0),
                func.coalesce(func.sum(Meal.fat), 0),
                func.coalesce(func.sum(Meal.carbs), 0),
            ).where(Meal.user_id == user_id, Meal.date == today)
        )
        return result.one()
    full_list = []

