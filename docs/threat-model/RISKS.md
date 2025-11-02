# P04 — Risk Register (реестр рисков) для Suggestion Box
| RiskID | Описание риска | Потоки / NFR | L (1-5) | I (1-5) | Risk (L×I) | Стратегия | Владелец | Срок (deadline) | Критерий закрытия |
|-------:|----------------|--------------|--------:|-------:|-----------:|----------|---------|-----------------|-------------------|
| R1 | Brute-force логина — компрометация паролей | F1 / NFR-01, NFR-05 | 3 | 4 | 12 | Снизить | owner | 2025-10-28 | Rate limiter deployed + тесты (429), Argon2 in code + unit tests |
| R2 | Кража/перехват access token | F1 / NFR-02, NFR-05 | 3 | 5 | 15 | Снизить | owner | 2025-10-28 | Short TTL (access ≤15m) configured + e2e: expired token → 401 |
| R3 | Неавторизованное изменение чужого suggestion | F4/F5 / NFR-03 | 2 | 5 | 10 | Снизить | owner | 2025-10-28 | Автотесты: другой пользователь → 403; ревью контролей |
| R4 | Утечка PII при экспорте | F3 / NFR-10, NFR-08 | 2 | 5 | 10 | Снизить | owner | 2025-11-04 | Экспорт с anonymize=true по умолчанию; e2e проверка экспортов |
| R5 | Низкая производительность под нагрузкой | F2/F3 / NFR-04 | 3 | 3 | 9 | Снизить | owner | 2025-11-11 | k6 отчёт: p95 ≤ порог; ошибки <1% |
| R6 | Уязвимость в зависимостях (High/Critical) | F9 / NFR-06 | 4 | 4 | 16 | Снизить / Перенести (страховка) | owner | 2025-10-21 | CI SCA включён; все High закрываются ≤7d (issue created) |
| R7 | Утечка или потеря бэкапов | F7 / NFR-09, NFR-07 | 2 | 5 | 10 | Снизить | owner | 2025-11-04 | Restore drill: RPO ≤1h, RTO ≤4h; зашифрованные бэкапы |
| R8 | Логи с PII или подмена логов | F6 / NFR-08, NFR-10 | 2 | 4 | 8 | Снизить | owner | 2025-10-31 | Audit log append-only, retention ≥90d, PII redaction тесты |
| R9 | Превышение лимитов (DDoS / abuse) | F2/F3 / NFR-05 | 3 | 3 | 9 | Снизить | owner | 2025-10-28 | Rate limiting + alerting; flood test results |
| R10 | Компрометация секретов (Vault/KMS) | F5/F7 / NFR-07 | 2 | 5 | 10 | Снизить / Избежать | owner | 2025-11-11 | Vault интегрирован, ротация ≤30d, ручная ротация ≤24h |
| R11 | Доступ к метрикам с PII | F8 / NFR-08 | 1 | 3 | 3 | Снизить | owner | 2025-11-04 | Метрики без PII; RBAC на Grafana/monitoring |
| R12 | SQL injection / DB tampering | F5 / NFR-04, NFR-09 | 2 | 5 | 10 | Снизить | owner | 2025-10-31 | SAST/DAST scan clean; parametrized queries; integration tests |
