# Быстрый старт - TL;DR

Для нетерпеливых :)

## Запустить за 3 команды

```bash
# 1. Скопировать и настроить .env
cp .env.example .env
# Отредактируй .env - поменяй пароли!

# 2. Запустить
docker-compose --profile dev up -d

# 3. Проверить
curl http://localhost:8000/health
```

## Swagger UI

Открой в браузере: http://localhost:8000/docs

## Первый тест API

```bash
# Регистрация
curl -X POST "http://localhost:8000/auth/register?username=testuser&password=test12345"

# Логин (получить токен)
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login?username=testuser&password=test12345" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

# Создать suggestion
curl -X POST "http://localhost:8000/suggestions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My idea","text":"Add dark mode","status":"new"}'

# Получить все suggestions
curl -X GET "http://localhost:8000/suggestions" \
  -H "Authorization: Bearer $TOKEN"
```

## Дефолтные пользователи

Если не менял .env, доступны:
- Username: `alice`, Password: `secure_alice_pass_456`
- Username: `bob`, Password: `secure_bob_pass_789`

## Остановить

```bash
# Остановить (данные сохранятся)
docker-compose --profile dev down

# Остановить и удалить данные
docker-compose --profile dev down -v
```

## Проблемы?

```bash
# Посмотреть логи
docker-compose --profile dev logs -f app

# Пересобрать
docker-compose --profile dev up -d --build

# Полная очистка
docker-compose --profile dev down -v
docker system prune -a
```

## Подробнее

См. [README.md](README.md)
