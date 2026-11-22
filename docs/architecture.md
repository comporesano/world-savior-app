# Архитектура EcoSavior

## Компоненты

```mermaid
flowchart LR
    B[Браузер<br/>Vanilla JS SPA<br/>hash-роутер] -->|REST / JSON<br/>Bearer JWT| F[FastAPI]
    F --> V[Pydantic v2<br/>валидация]
    V --> R[routers/]
    R --> S[services/<br/>бизнес-логика]
    S --> O[SQLAlchemy 2.0 ORM]
    O --> D[(SQLite<br/>data/ecosavior.db)]
    F --> ST[static/<br/>index.html + css/js]
```

- **SPA** — статика без сборки; клиентский роутинг на хешах (`#/events/3`),
  поэтому серверу не нужен SPA-fallback — он всегда отдаёт `index.html`.
- **Routers** — тонкий слой: маршруты, зависимости, response-модели.
- **Services** — вся бизнес-логика (регистрация, запись, подтверждение,
  начисление баллов). Слой отделён от HTTP — легко переиспользовать.
- **Ошибки** — единый формат `{error: {code, message, details}}` через
  `ApiError` + обработчики FastAPI (см. `src/errors.py`).

## Схема БД

```mermaid
erDiagram
    users ||--o{ events : организует
    users ||--o{ participants : участвует
    users ||--o{ refresh_tokens : имеет
    events ||--o{ participants : собирает

    users {
        int id PK
        string name
        string email UK
        string password_hash
        string bio
        int points
        string created_at
    }
    events {
        int id PK
        int organizer_id FK
        string title
        string description
        string type
        string location
        string starts_at
        string ends_at
        int capacity
        int points_reward
    }
    participants {
        int id PK
        int event_id FK
        int user_id FK
        string status
        string joined_at
    }
    refresh_tokens {
        int id PK
        int user_id FK
        string jti
        string token_hash UK
        string expires_at
        string revoked_at
    }
```

Все даты — **строки ISO 8601 в UTC** (без суффикса таймзоны). Причина: SQLite
хранит datetime без таймзоны, и сравнение aware/naive объектов — классический
источник багов; строки сравниваются и сортируются лексикографически корректно,
а конвертация происходит только на границе API (схемы Pydantic).

## Поток авторизации

```mermaid
sequenceDiagram
    participant C as Клиент (SPA)
    participant A as API /auth
    participant D as БД

    C->>A: POST /auth/login {email, password}
    A->>D: SELECT user WHERE email
    A->>A: bcrypt.checkpw
    A->>D: INSERT refresh_tokens (sha256(token), jti)
    A-->>C: { accessToken (15m), refreshToken (30d) }

    Note over C: access истёк → 401
    C->>A: POST /auth/refresh {refreshToken}
    A->>D: найти по sha256, проверить revoked_at/expires_at
    A->>D: отозвать старый, выдать новую пару
    A-->>C: { accessToken, refreshToken }

    Note over C: повторное использование отозванного токена
    C->>A: POST /auth/refresh {старый token}
    A->>D: UPDATE refresh_tokens SET revoked_at (все сессии юзера)
    A-->>C: 401 TOKEN_REUSE_DETECTED
```

## Подтверждение участия и баллы

`POST /events/{id}/participants/{uid}/confirm` (только организатор):

1. Проверки: событие существует, вызывающий — организатор (403 иначе),
   запись существует (404), статус ещё `joined` (409 при повторе).
2. В одной транзакции: `status = confirmed` и `user.points += points_reward`.
3. Ответ содержит начисленные баллы и обновлённый уровень участника.

Уровни: `level = 1 + ⌊√(points/100)⌋`, звания по уровню.

## Безопасность

| Механизм | Реализация |
|---|---|
| Пароли | bcrypt, 10 раундов; максимум 72 символа (ограничение bcrypt) |
| Токены | JWT HS256; refresh хранится в БД только как SHA-256-хеш |
| Ротация | refresh одноразовый; reuse → отзыв всех сессий |
| CSP | `script-src 'self'` без `unsafe-inline`/`unsafe-eval` (для `/docs` — исключение, там CDN) |
| Rate limit | slowapi: 30 req/мин на `/api/v1/auth/*` |
| CORS | настраивается через `CORS_ORIGINS` |
| Заголовки | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` |

## Цвет и визуализация (принятые решения)

- Диаграмма «Мероприятия по типам» — **рейтинговые горизонтальные бары одним
  оттенком** (сравнение величин, а не различение серий).
- Цвета типов событий — категориальная палитра, **валидированная скриптом** на
  CVD-различимость (OKLab ΔE ≥ 8) и контраст в обеих темах; идентичность типа
  всегда дублируется иконкой и текстом (цвет не единственный канал).
- Статусные цвета (good/warning/critical) зарезервированы и не используются
  как «цвета серий».
- KPI-тайлы — числа с автокомпактом (1 284 / 12.9K), метры — трек светлее
  заливки (та же рампа).

## Тесты

`tests/` — 35 тестов на `httpx`-клиенте FastAPI с **in-memory SQLite**
(`StaticPool`) на каждый тест: полная изоляция, lifespan приложения не
запускается (реальная БД не затрагивается). Покрытие: регистрация/вход,
валидация, ротация и компрометация токенов, CRUD событий, права организатора,
запись/отмена, вместимость, начисление баллов ровно один раз, рейтинг,
статистика, профили.
