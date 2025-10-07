# Acceptance (BDD) — Security & Reliability


Feature: Session management and token expiry
Scenario: Access token expires after configured TTL
Given сервис запущен на stage с конфигурацией access_ttl = 15 minutes
And пользователь получает access + refresh токен после успешного логина
When прошёл 16 minutes после выдачи access токена
Then запрос к GET /suggestions с этим access токеном возвращает 401 Unauthorized


Feature: Owner-only modification
Scenario: Владелец может изменить своё предложение
Given пользователь A создал suggestion S
When пользователь A делает PUT /suggestions/{S.id} с валидными данными
Then ответ 200 OK и suggestion обновлён


Scenario: Другой пользователь не может изменить чужое предложение (негатив)
Given пользователь A создал suggestion S
And пользователь B получил валидный access токен
When пользователь B делает PUT /suggestions/{S.id}
Then ответ 403 Forbidden и тело с кодом ошибки


Feature: Performance of creating suggestions
Scenario: p95 latency при 20 RPS для POST /suggestions держится в пределах
Given сервис развернут на stage с конфигурацией и DB заполненной типовыми данными
When запускается 5-минутный нагрузочный тест 20 RPS для POST /suggestions
Then p95 времени отклика для POST /suggestions ≤ 250 ms


Feature: Vulnerability remediation workflow
Scenario: High/Critical dependency пофиксена в регламентированный срок
Given CI SCA-отчёт обнаружил vulnerability level=High для package X
When issue создано в трекере и назначено на مالک команды
Then исправление/мердж PR с фиксом или временным мердж-исправлением происходит ≤ 7 дней


Feature: Rate limiting (негативный)
Scenario: При превышении лимита запросов возвращается 429
Given rate limit настроен: 10 RPS per user
When пользователь выполняет 12 запросов в течение 1 секунды
Then сервис возвращает 429 Too Many Requests для избыточных запросов
