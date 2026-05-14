# Task Board API — лабораторная работа №12

## Данные для проверки

| Поле | Значение |
|------|-----------|
| **ФИО** | Кузьмищев Родион Ильич |
| **Группа** | 221331 |
| **Вариант** | 8 |
| **Предметная область** | Система управления задачами (Trello-клон): доски, колонки, карточки, комментарии, сроки |
| **Номер лабораторной** | 12 |

## Выполненные задания повышенной сложности (адаптация под вариант 8)

Согласно методичке для вариантов 11–30 выполняются **8 заданий** повышенной сложности. Исключены по условию: **3** (локальная LLM), **5** (плагин IDE), **6** (сравнение моделей), **8** (эссе про галлюцинации).

| № в методичке | Содержание | Где в репозитории |
|----------------|------------|-------------------|
| 1 | Полноценное веб-приложение: JWT, CRUD, ≥3 связанных сущностей, аналитика, админ-доступ | `src/taskboard/` |
| 2 | Code review ИИ-кода, ≥5 исправлений | `docs/CODE_REVIEW.md` |
| 4 | GitHub Actions: при PR — комментарий с описанием diff (OpenAI при наличии секрета) | `.github/workflows/ai-pr-summary.yml`, `scripts/pr_ai_comment.py` |
| 7 | Промпты для генерации тестов, покрытие ≥90% (проверка в CI) | `docs/TEST_PROMPTS_AND_COVERAGE.md`, `pyproject.toml`, CI |

Дополнительно: зафиксированы использованные промпты — `PROMPTS.md`.

## Стек и качество кода

- **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, **JWT** (python-jose), хеширование паролей (passlib/bcrypt).
- Разделение по слоям: модели, схемы, роутеры, безопасность, зависимости — без монолитных «бог-файлов».
- Тесты: **pytest** + **httpx** (TestClient), изоляция БД через in-memory SQLite и подмену `SessionLocal` в `tests/conftest.py`.

## Локальный запуск (рекомендуется Python 3.12)

На **Python 3.14** под Windows колёса `pydantic-core` могут не ставиться без MSVC/Rust toolchain — для локальной разработки используйте **Python 3.11–3.12** или Docker.

```bash
pip install -r requirements.txt
set PYTHONPATH=src
pytest tests/ -q --cov=taskboard --cov-report=term-missing --cov-fail-under=90
uvicorn taskboard.main:app --app-dir src --reload
```

## Docker

```bash
docker compose up --build
```

Сервис: `http://localhost:8000/docs` (Swagger).

## Переменные окружения

| Переменная | Назначение | По умолчанию |
|------------|------------|--------------|
| `SECRET_KEY` | Подпись JWT | см. `taskboard/config.py` (смените в prod) |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./data/app.db` |

## CI и секреты GitHub

- **CI** (`.github/workflows/ci.yml`): Python **3.12**, `pytest` с `--cov-fail-under=90`.
- **AI PR summary** (`.github/workflows/ai-pr-summary.yml`): для генерации текста добавьте в секреты репозитория **`OPENAI_API_KEY`**. Если секрет не задан, в PR всё равно будет комментарий с усечённым diff (режим fallback), чтобы можно было сделать скриншот для отчёта.

## Основные эндпоинты

- `POST /auth/register`, `POST /auth/token` (OAuth2 password form: поле `username` = email), `GET /auth/me`
- `GET|POST|PUT|DELETE /boards/...`
- `GET|POST /boards/{id}/lists`, `DELETE /lists/{id}`
- `GET|POST /lists/{id}/cards`, `PUT|DELETE /cards/{id}`
- `GET|POST /cards/{id}/comments`, `DELETE /comments/{id}`
- `GET /analytics/boards/{board_id}` — сводка по карточкам, просрочкам, комментариям
- `GET /admin/users`, `DELETE /admin/users/{id}`, `DELETE /admin/cards/{id}` — только `is_admin`

## Примеры `curl`

```bash
curl -s -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\",\"password\":\"password12\"}"
curl -s -X POST http://localhost:8000/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=user@example.com&password=password12"
```

Дальше подставьте `Authorization: Bearer <token>` для защищённых маршрутов.

## Организация коммитов и push

В истории git сохранены **атомарные** коммиты по этапам: инфраструктура и зависимости → тесты и «красная» фаза для контракта API → реализация (**зелёная** фаза) → CI/CD и документация. После значимых этапов выполнялся **`git push`** в `origin` (см. `git log`).
