# STRIDE для ключевых потоков

| № | Поток / Элемент | STRIDE категория | Угроза (кратко) | Контроль / Мера | Связь с NFR (ссылка) | Проверка / Артефакт |
|---:|-----------------|------------------|------------------|------------------|----------------------|---------------------|
| 1 | F1 — Login (POST /auth/login) | S / T (Spoofing / Tampering) | R1, R2 | HTTPS, Argon2id для паролей, rate-limit на логин, короткий access_ttl | NFR-01, NFR-02, NFR-05 | Unit tests (hash/verify), rate-limit e2e, k6 + traffic capture |
| 2 | F2 — Create Suggestion (POST /suggestions) | T / R (Tampering / Repudiation) | R5, R9 | AuthZ checks owner binding; audit-log (correlation_id) | NFR-03, NFR-08 | Автотесты авторизации, проверка audit-логов |
| 3 | F3 — GET /suggestions | I / D (Information disclosure / Denial) | R4, R5, R9 | Pagination, output sanitization, export anonymize, rate-limit | NFR-04, NFR-05, NFR-10 | Payload review, e2e export tests, perf tests |
| 4 | F4 — Update/Delete by owner | S / I (Spoofing / Information disclosure) | R3 | Owner-only checks, JWT validation, tests for 403 | NFR-03, NFR-02 | Pytest cases: owner→200, other→403 |
| 5 | F5 — Service ↔ Database (psql over TLS) | T / R (Tampering / Repudiation) | R3, R10, R12 | ORM/parametrized queries, DB TLS, least-privilege DB user | NFR-04, NFR-09 | SAST/DAST scans, integration tests, restore drill |
| 6 | F6 — Audit Log writes | R / I (Repudiation / Information disclosure) | R8, R10 | Append-only logs, retention policy, redact PII by default | NFR-08, NFR-10 | Проверка наличия correlation_id, retention настройка |
| 7 | F7 — Backups (DB snapshot → S3) | D / I (Disclosure / Denial) | R7, R10 | Encrypted backups, access policy, RPO/RTO runbook | NFR-09, NFR-07 | Restore drill, encryption-at-rest proof |
| 8 | F8 — Monitoring / Metrics | I / E (Information disclosure / Elevation) | R10, R11 | Метрики без PII, RBAC on monitoring, secure agents | NFR-08 | Grafana/Prometheus config review, alerts |
| 9 | F9 — Dependencies / CI pipeline | E / T (Elevation / Tampering) | R6 | SCA in CI, signed packages, fix SLA for vulnerabilities | NFR-06 | CI SCA report, dependabot PRs, audit of pipeline |
