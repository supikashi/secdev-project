# Отчет по проекту

### 1. Стабильный CI

- Создан CI pipeline в `.github/workflows/ci.yml` с триггерами на `pull_request` и `push`
- Настроен concurrency group с автоматической отменой дублирующихся запусков
- Установлены минимальные permissions (`contents: read`)
- Добавлены timeouts на все jobs
- Успешно пройдены проверки в PR P07 и PR P08

---

### 2. Сборка/тесты/артефакты

**Lint Job:** Python 3.12 с pip кэшем, три линтера (ruff, black, isort), параллельно с test

**Test Job:** pytest с coverage отчетами, артефакты `test-reports`

**Build Package Job:** сборка wheel пакета, артефакты `python-package`, запуск после успешных lint/test

**Docker Job:** Hadolint и Trivy сканирование, проверки безопасности (non-root, healthcheck), генерация SBOM (permanent retention), BuildKit cache

**Конфигурация:** настроен `pyproject.toml` с pytest coverage для модуля `app`

---

### 3. Секреты вынесены

- Вынесены `DATABASE_URL` и `JWT_SECRET` в GitHub Secrets с fallback значениями для CI
- Установлены минимальные permissions (`contents: read`), расширенные только для deploy (`contents: write`)
- Секреты передаются через `env` section, логирование исключено
- В `compose.yaml` настроен `env_file` с переменными окружения

---

### 4. PR-политика

- Все jobs должны успешно завершиться перед merge
- Созданы и смержены PR P07: Container hardening и PR P08: CI/CD

---

### 5. Docker/compose

**Dockerfile:** multi-stage сборка, Python 3.11-slim с SHA256 pinning, non-root user, минимальные зависимости. Build time ~1 мин, размер ~300MB

**Compose App Service:** healthcheck на `/health`, security опции (`no-new-privileges`, `cap_drop: ALL`, `read_only: true`, `tmpfs`, `user: 1000:1000`), зависимость от db с `service_healthy`

**Compose DB Service:** PostgreSQL 16-alpine, healthcheck с `pg_isready`, persistent volume, `no-new-privileges`

**Network:** bridge сеть `app-network`, `dev` profile для development
