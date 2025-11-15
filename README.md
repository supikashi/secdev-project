# SecDev Course Project - Suggestion Box

Проект: Suggestion Box (система предложений с аутентификацией и авторизацией)

Технологии: Python 3.11, FastAPI, PostgreSQL, Docker, SQLAlchemy, Argon2id

> 💡 **Для быстрого старта**: См. [QUICKSTART.md](QUICKSTART.md) - запуск за 3 команды!

## 🚀 Быстрый старт

### Требования

- Docker и Docker Compose (рекомендуется)
- Python 3.11+ (для локальной разработки)
- PostgreSQL 16 (если без Docker)

### Установка и запуск с Docker Compose (рекомендуется)

1. **Клонировать репозиторий**
   ```bash
   git clone <repository-url>
   cd course-project-supikashi
   ```

2. **Настроить переменные окружения**
   ```bash
   # Скопировать пример конфигурации
   cp .env.example .env

   # Отредактировать .env файл и установить БЕЗОПАСНЫЕ пароли!
   # ВАЖНО: Измените все пароли перед запуском!
   nano .env  # или используйте любой редактор
   ```

3. **Запустить приложение**
   ```bash
   # Собрать и запустить контейнеры
   docker-compose --profile dev up -d --build

   # Проверить статус
   docker-compose --profile dev ps

   # Посмотреть логи
   docker-compose --profile dev logs -f app
   ```

4. **Проверить работоспособность**
   ```bash
   # Проверить health endpoint
   curl http://localhost:8000/health
   # Ожидаемый ответ: {"status":"ok"}

   # Открыть Swagger UI в браузере
   open http://localhost:8000/docs
   ```

5. **Остановить приложение**
   ```bash
   # Остановить контейнеры (данные в БД сохранятся)
   docker-compose --profile dev down

   # Остановить и удалить данные БД
   docker-compose --profile dev down -v
   ```

### Локальная разработка без Docker

1. **Установить PostgreSQL 16**
   ```bash
   # macOS
   brew install postgresql@16
   brew services start postgresql@16

   # Ubuntu/Debian
   sudo apt-get install postgresql-16
   ```

2. **Создать базу данных**
   ```bash
   psql postgres
   CREATE DATABASE supikashi;
   CREATE USER postgres WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE supikashi TO postgres;
   \q
   ```

3. **Настроить Python окружение**
   ```bash
   # Создать виртуальное окружение
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

   # Установить зависимости
   pip install -r requirements.txt -r requirements-dev.txt

   # Настроить pre-commit hooks
   pre-commit install
   ```

4. **Настроить переменные окружения**
   ```bash
   # Создать .env файл
   cp .env.example .env

   # Отредактировать DATABASE_URL в .env
   # DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/supikashi
   ```

5. **Запустить приложение**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📚 API Endpoints

### Аутентификация

- `POST /auth/register` - Регистрация нового пользователя
  - Query params: `username` (3-50 символов), `password` (мин 8 символов)
  - Пароль хешируется с Argon2id перед сохранением

- `POST /auth/login` - Вход в систему
  - Query params: `username`, `password`
  - Возвращает JWT Bearer token с TTL 1 час
  - Rate limiting: 5 попыток/60 сек по username, 10 попыток/60 сек по IP

- `POST /auth/logout` - Выход (инвалидация токена)
  - Требует Authorization header

- `GET /auth/token-info` - Информация о токене
  - Возвращает TTL и время создания токена

### Suggestions (предложения)

Все endpoints требуют авторизации (Bearer token в Authorization header).

- `POST /suggestions` - Создать предложение
  - Body: `{"title": "...", "text": "...", "status": "new"}`
  - Статусы: `new`, `reviewing`, `approved`, `rejected`

- `GET /suggestions` - Получить все предложения
  - Query param (опционально): `status`

- `GET /suggestions/{id}` - Получить предложение по ID

- `PUT /suggestions/{id}` - Обновить предложение
  - Только владелец может обновить

- `DELETE /suggestions/{id}` - Удалить предложение
  - Только владелец может удалить

### Другое

- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI (интерактивная документация)
- `GET /openapi.json` - OpenAPI спецификация

## 🔐 Безопасность

### Реализовано

✅ **Argon2id** для хеширования паролей (NFR-01)
  - time_cost=3, memory_cost=256MB, parallelism=1

✅ **JWT токены** с TTL 1 час (частично NFR-02)
  - Хранятся in-memory с автоматической очисткой

✅ **Owner-only авторизация** (NFR-03)
  - Пользователи могут изменять только свои предложения

✅ **Rate limiting** (NFR-05)
  - По username: 5 попыток / 60 секунд
  - По IP: 10 попыток / 60 секунд

✅ **SQL Injection защита**
  - Параметризованные запросы через SQLAlchemy
  - Input validation с Pydantic
  - Enum для ограниченных значений

✅ **Безопасное хранение credentials**
  - .env файл для secrets (не в Git)
  - Нет hardcoded паролей

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest -v

# Запустить с покрытием
pytest --cov=app --cov-report=html

# Запустить конкретный тест
pytest tests/test_suggestions.py -v
```

## 📝 Разработка

### Ритуал перед commit

```bash
# Форматирование и линтинг
ruff check --fix
black .
isort .

# Тесты
pytest -q

# Pre-commit hooks (автоматически)
pre-commit run --all-files
```

### Структура проекта

```
.
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI приложение, endpoints
│   ├── database.py       # БД модели и CRUD операции
│   └── entities.py       # Pydantic models
├── tests/
│   ├── conftest.py
│   ├── test_suggestions.py
│   └── test_rate_limit.py
├── docs/
│   └── security-nfr/     # Документация по безопасности
├── compose.yaml          # Docker Compose конфигурация
├── Dockerfile           # Образ приложения
├── requirements.txt      # Production зависимости
├── requirements-dev.txt  # Dev зависимости
├── .env.example         # Шаблон переменных окружения
└── README.md
```

## 🐳 Docker команды

```bash
# Пересобрать только app контейнер
docker-compose --profile dev up -d --build app

# Перезапустить контейнеры
docker-compose --profile dev restart

# Посмотреть логи
docker-compose --profile dev logs -f

# Подключиться к БД
docker-compose --profile dev exec db psql -U postgres -d supikashi

# Войти в контейнер приложения
docker-compose --profile dev exec app sh

# Очистить все (включая volumes)
docker-compose --profile dev down -v
docker system prune -a
```

## 🌐 Переменные окружения

Обязательные переменные в `.env`:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=supikashi

# Default users (для начальной инициализации)
DEFAULT_USER_ALICE=alice
DEFAULT_PASSWORD_ALICE=your_alice_password
DEFAULT_USER_BOB=bob
DEFAULT_PASSWORD_BOB=your_bob_password

# Application (опционально)
APP_ENV=dev
LOG_LEVEL=info
```

## 📊 CI/CD

В репозитории настроен GitHub Actions workflow для:
- Линтинга (ruff, black, isort)
- Тестирования (pytest)
- Security checks

## 📄 Лицензия

Учебный проект для курса SecDev HSE 2025

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
