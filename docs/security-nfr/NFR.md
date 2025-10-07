# Non-Functional Requirements (Security & Reliability) — Suggestion Box


Проект: 35 – Suggestion Box (анонимные предложения через user-id). Технологии: Python/FastAPI, SQLite/Postgres, Pytest.


| ID | Название | Описание кратко | Метрика / Порог | Проверка (чем / где) | Компонент | Приоритет |
|--------|-----------------------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------|-------------------|-----------|
| NFR-01 | Хранение паролей | Пароли пользователей хранятся только в виде безопасного хэша Argon2id | Argon2id: t=3, m=256MB, p=1 (пример; параметры в конфиге) | Юнит-тесты, ревью конфигурации, код (auth) | auth | High |
| NFR-02 | JWT/Session TTL | Access токены короткоживущие, refresh — ограничены | access_ttl ≤ 15 min; refresh_ttl ≤ 7 days | Конфиг + интеграционные тесты + e2e с симуляцией таймаутов | auth/session | High |
| NFR-03 | Owner-only Authorization | Только владелец предложения может изменить/удалить его | 100% endpoints защищены (PUT/DELETE /suggestions/{id} проверяют owner)| Автотесты авторизации (pytest), контракт-тесты, ревью кода | api / business | High |
| NFR-04 | Производительность / latency | API отвечает в приемлемое время при типичной нагрузке | p95 POST /suggestions ≤ 250 ms @ 20 RPS; p95 GET /suggestions ≤ 200 ms @ 50 RPS | Нагрузочные тесты на stage (k6/jmeter), метрики APM | api / infra | Medium |
| NFR-05 | Rate limiting / Abuse protection | Защита от всплесков и brute-force | 100 RPS на сервис в целом; 10 RPS/uid; 60 RPS/ip; 429 при превышении | E2E тесты, интеграция с rate-limiter, мониторинг | api / infra | High |
| NFR-06 | Уязвимости зависимостей | Время реакции на High/Critical уязвимости в зависимостях | исправление/замена ≤ 7 дней после обнаружения | CI SCA-отчёт (dependabot/snyk/oss-review) + issue tracker | build / ci | High |
| NFR-07 | Ротация секретов | Автоматизированная ротация секртов и ключей | SLA ротации ≤ 30 дней; ручная ротация в ≤ 24 ч при компрометации | Политика Vault/KMS, журнал операций, тесты восстановления | platform / infra | Medium |
| NFR-08 | Аудит и логирование | Все изменения статусов и удаления логируются с correlation_id | 100% мутабельных операций с записью в audit-log, retention ≥ 90 дней | Проверка логов, e2e сценарии, SIEM/ELK/CloudWatch | logging / audit | High |
| NFR-09 | Резервное копирование (DB) | База данных должна восстанавливаться в приемлемые сроки | RPO ≤ 1 час; RTO ≤ 4 часа | Drill restore (restore test), runbook | db / infra | High |
| NFR-10 | Экспорт данных — приватность | Экспорт (CSV/JSON) не раскрывает PII; опция анонимизации | по умолчанию PII замаскировано; manual export требует audit approval | Автотесты экспорта, ревью, e2e | export / api | Medium |
