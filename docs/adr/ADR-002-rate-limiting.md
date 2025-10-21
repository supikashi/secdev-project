# ADR-002: Rate limiting for /auth/login (anti-bruteforce)
Дата: 2025-10-21
Статус: Accepted

## Context
Брутфорс на /auth/login — высокий риск (компрометация учётных записей). Нужно простое, воспроизводимое решение, которое легко внедрить и тестировать.

## Decision
- Ввести rate-limiting для `/auth/login`:
  - Per-user: **5 attempts / 60 seconds** (based on username/email).
  - Per-IP: **60 requests / 60 seconds**.

- Dev/test: fallback на in-memory limiter (как feature-flag).
- При превышении возвращать HTTP `429` с Problem JSON (см. ADR-001) и correlation_id.
- Логи: генерировать alert при аномальном падении (спайк > 5× baseline) в monitoring.

## Alternatives
- **Без rate limit** — проще, но остаётся риск брутфорса.
- **Captcha / MFA** — повышает безопасность, но ухудшает UX и требует интеграции.
Выбран rate-limit как лёгкий, совместимый и мгновенно проверяемый механизм.

## Rollout plan
- Включить на `/auth/login` в dev → staging через feature-flag `enable_login_rate_limit`.
- Наблюдать метрики в monitoring; при стабильности — включить в production.

## Consequences
+ Быстрая защита от brute-force, минимальная ложноположительная блокировка при нормальном трафике.
- Не решает распределённые DDoS (требуются WAF/CDN в будущем).

## Links
- NFR-05 (rate limiting)
- F1 (Login)
- R1, R9
- Tests: `tests/test_rate_limit.py::test_login_rate_limit`, `tests/test_rate_limit.py::test_login_per_user_limit`
- Критерий закрытия: flood test для /auth/login возвращает 429 для превышения, тесты проходят; alerting rule создан.
