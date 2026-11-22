"""Демо-данные: пользователи, мероприятия, записи и подтверждения участия.

Запуск из корня проекта: python -m src.seed
Все демо-пользователи имеют пароль: Demo1234!
"""

from datetime import datetime, timedelta, timezone

from .db import Base, SessionLocal, engine
from .models import Event, Participant, RefreshToken, User
from .security import hash_password

PASSWORD = "Demo1234!"


def days_from_now(days: int, hour: int = 10, minute: int = 0) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return dt.replace(tzinfo=None).isoformat(timespec="milliseconds")


def days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.replace(tzinfo=None).isoformat(timespec="milliseconds")


USERS = [
    (1, "Анна Соколова", "anna@eco.dev", "Организатор движения «Зелёный город»", 25),
    (2, "Михаил Романов", "mike@eco.dev", "Субботники — моя стихия", 50),
    (3, "София Ли", "sofia@eco.dev", "За раздельный сбор отходов", 35),
    (4, "Иван Кузнецов", "ivan@eco.dev", "Люблю чистые реки", 50),
    (5, "Дарья Орлова", "daria@eco.dev", "Эко-волонтёр со стажем", 25),
    (6, "Павел Морозов", "pavel@eco.dev", "Сажаю деревья каждую осень", 60),
    (7, "Елена Виноградова", "elena@eco.dev", "Популяризирую zero waste", 40),
    (8, "Олег Смирнов", "oleg@eco.dev", "Преподаватель, веду эко-лекции", 15),
]

EVENTS = [
    # id, organizer_id, title, description, type, location, starts_at, ends_at, capacity, points
    (1, 1, "Большой субботник в Приморском парке",
     "Собираем мусор, расчищаем дорожки и приводим в порядок зоны отдыха. Инвентарь и перчатки выдадим на месте, с собой — хорошее настроение!",
     "cleanup", "Приморский парк, главный вход", days_from_now(3, 10), days_from_now(3, 13), 30, 25),
    (2, 1, "Эко-лекция: ноль отходов дома",
     "Практические советы, как сократить мусор в быту: от многоразовых сумок до компостирования. После лекции — ответы на вопросы и обмен опытом.",
     "eco_lecture", "Библиотека им. Ленина, зал 3", days_from_now(2, 18, 30), days_from_now(2, 20, 30), 25, 10),
    (3, 3, "Сбор вторсырья: макулатура и пластик",
     "Принимаем макулатуру, ПЭТ-бутылки и пластиковые крышечки. Всё собранное отправится на переработку. Приходите — каждая пачка бумаги на счету!",
     "recycling", "ТЦ «Мега», парковка B", days_from_now(6, 12), days_from_now(6, 16), 50, 15),
    (4, 1, "Посадка клёнов на аллее Победы",
     "Высаживаем 60 саженцев клёна. Саженцы и инструменты предоставляются. Опыт не нужен — инструктаж на месте, работаем в парах.",
     "tree_planting", "Аллея Победы", days_from_now(10, 11), days_from_now(10, 14), 20, 30),
    (5, 1, "Очистка берега реки Каменки",
     "Убираем береговую линию: пластик, стекло, покрышки. Перчатки, мешки и лодки предоставляются. Финишируем общим пикником!",
     "water_cleanup", "Река Каменка, лодочная станция", days_from_now(14, 9), days_from_now(14, 13), 25, 35),
    (6, 8, "Эко-воркшоп: вещи из переработанных материалов",
     "Мастер-класс: делаем сумки и подставки из старых футболок и картона. Все материалы предоставляются, результат уносите с собой.",
     "eco_lecture", "Арт-пространство «Фабрика»", days_from_now(21, 15), days_from_now(21, 18), 30, 10),
    (7, 2, "Субботник у школьного двора",
     "Поможем школе подготовить двор к зиме: листва, ветки, клумбы. Чай и печенье гарантируем!",
     "cleanup", "Школа № 42", days_from_now(5, 10), days_from_now(5, 12, 30), 15, 20),
    (8, 1, "Субботник в городском бору",
     "Прошедшее мероприятие: убрали 2,5 км троп и 40 мешков мусора. Спасибо всем участникам!",
     "cleanup", "Городской бор", days_ago(5), days_ago(5), 20, 20),
    (9, 1, "Посадка елей на окраине города",
     "Прошедшее мероприятие: высажено 45 елей. Через 20 лет здесь будет лес!",
     "tree_planting", "Северная окраина", days_ago(12), days_ago(12), 15, 30),
    (10, 3, "Сбор батареек и лампочек",
     "Прошедшее мероприятие: собрано 120 кг батареек и 300 лампочек для безопасной утилизации.",
     "recycling", "Экоцентр", days_ago(20), days_ago(20), 40, 15),
    (11, 1, "Очистка пруда в Парке Горького",
     "Прошедшее мероприятие: очищено 300 метров береговой линии, вывезено 2 контейнера мусора.",
     "water_cleanup", "Парк Горького, пруд", days_ago(8), days_ago(8), 20, 30),
    (12, 8, "Эко-лекция: раздельный сбор отходов",
     "Прошедшее мероприятие: разобрали, как правильно сортировать отходы в нашем городе.",
     "eco_lecture", "Библиотека им. Ленина", days_ago(30), days_ago(30), 30, 10),
]

# (event_id, user_id, status)
PARTICIPATIONS = [
    # Предстоящие: записи
    (1, 2, "joined"), (1, 3, "joined"), (1, 6, "joined"),
    (2, 3, "joined"),
    (3, 5, "joined"), (3, 6, "joined"),
    (4, 7, "joined"), (4, 8, "joined"),
    (5, 4, "joined"), (5, 5, "joined"),
    (6, 2, "joined"),
    (7, 1, "joined"), (7, 7, "joined"),
    # Прошедшие: подтверждённые (баллы уже учтены в users.points)
    (8, 2, "confirmed"), (8, 3, "confirmed"), (8, 4, "confirmed"),
    (9, 6, "confirmed"), (9, 7, "confirmed"), (9, 2, "confirmed"),
    (10, 3, "confirmed"), (10, 8, "confirmed"), (10, 5, "confirmed"), (10, 1, "confirmed"),
    (11, 6, "confirmed"), (11, 4, "confirmed"),
    (12, 7, "confirmed"), (12, 5, "confirmed"), (12, 1, "confirmed"),
]


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Полная перезапись демо-данных
        db.query(Participant).delete()
        db.query(RefreshToken).delete()
        db.query(Event).delete()
        db.query(User).delete()
        db.commit()

        password_hash = hash_password(PASSWORD)
        for user_id, name, email, bio, points in USERS:
            db.add(
                User(
                    id=user_id, name=name, email=email, password_hash=password_hash,
                    bio=bio, points=points, created_at=days_ago(60),
                )
            )
        for event_id, organizer_id, title, description, type_, location, starts, ends, capacity, points in EVENTS:
            db.add(
                Event(
                    id=event_id, organizer_id=organizer_id, title=title, description=description,
                    type=type_, location=location, starts_at=starts, ends_at=ends,
                    capacity=capacity, points_reward=points, created_at=starts,
                )
            )
        for event_id, user_id, status in PARTICIPATIONS:
            db.add(Participant(event_id=event_id, user_id=user_id, status=status, joined_at=days_ago(3)))
        db.commit()

        print("🌱 Демо-данные загружены:")
        print(f"   • {len(USERS)} пользователей, {len(EVENTS)} мероприятий, {len(PARTICIPATIONS)} записей")
        print("   • Демо-вход (организатор): anna@eco.dev / Demo1234!")
        print(f"   • БД: {engine.url}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
