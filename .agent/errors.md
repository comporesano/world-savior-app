# .agent/errors.md — ошибки агента и способы их исправления

## Node-версия (первый подход, отменена пользователем)

| Ошибка | Причина | Исправление |
|---|---|---|
| zod `datetime()` не принимал `2026-…Z` | По умолчанию zod требует строку без таймзоны | `{ offset: true }` |
| Поиск `q=Парке` не находил «…в парке» | `LIKE` в SQLite регистронезависим только для ASCII | `lower()` по обеим сторонам (в Python-версии — кастомный `lower_utf8`) |
| Два JWT, выпущенные в одну секунду, совпадали | payload идентичен (iat в секундах) | тест сравнивает refresh-токены (там случайный jti) |
| `joined=false` в деталях события | Публичный GET не подшивал пользователя (нужен optional-auth middleware) | `optionalAuth` |
| 409 вместо 400 в тесте завершённого события | `endsAt === startsAt` → падал refine валидации | разные даты в тесте |

## Python-версия

| Ошибка | Причина | Исправление |
|---|---|---|
| Все 35 тестов: `unable to open database file` | Lifespan при старте TestClient создавал таблицы в файловой БД, а каталога `data/` не было | 1) `make_engine` создаёт каталог; 2) в тестах TestClient без контекстного менеджера — lifespan не запускается |
| Поиск «ПАРКЕ» → 0 результатов | `lower()` в SQLite не работает для кириллицы → `ilike` не спасает | Кастомная SQL-функция `lower_utf8` через `create_function` на connect + `func.lower_utf8(...).like()` |
| `ResponseValidationError` на GET `/events/{id}` | Сервис возвращал `{"event": {...}}`, а response_model был плоский `EventDetailOut` | Контейнер `EventDetailResponse { event: … }` |
| Ошибка `endsAt` не имела поля в `details` | `model_validator(mode="after")` не привязывает ошибку к полю | Проверка перенесена в `field_validator("endsAt")` с доступом к `info.data["startsAt"]` |
| Warning: короткий HMAC-ключ в тестах | `JWT_SECRET=test-secret` (11 байт) | Длинный тестовый секрет |
| Венв без pip | `uv venv` не ставит pip | `uv pip install --python .venv/bin/python …` |
| `playwright install chromium`: ECONNRESET с CDN | Сеть рвёт соединение с cdn.playwright.dev | Использован кэш `~/.cache/ms-playwright` (chromium-1208) через `executable_path`; версия пакета подобрана по ревизиям кэша через PyPI JSON API (1.58.0) |
| Запись видео не создавалась | Версия playwright требовала ffmpeg-1013, в кэше 1011; симлинк не помог (тихий отказ) | Установлен playwright==1.58.0 (ожидает ровно 1011 + chromium-1208) |
| `wait_for_function` падал: CSP violation | CSP `script-src 'self'` блокирует eval | Проверка через `wait_for_selector` |
| `add_init_script` молча не работал | CSP блокирует инлайн-скрипты Playwright | В демо-сценариях вход через UI-форму |
| `[data-confirm]` не находился в повторных прогонах | Это не баг: демо-видео уже подтвердило всех участников события №1 | Пересоздание данных (`python -m src.seed`) перед съёмкой |

## Выводы

- Дата-центричные баги (таймзоны, регистр) проявляются только на реальных
  данных — поэтому seed использует кириллицу и даты «относительно сейчас».
- Инструментальные конфликты (CSP × Playwright) — знак того, что защита
  работает; решения зафиксированы в `scripts/capture.py`.
