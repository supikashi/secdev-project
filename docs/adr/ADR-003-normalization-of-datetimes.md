# ADR-003: Normalization of datetimes
Дата: 2025-10-21
Статус: Accepted

## Context
Неразнормированные даты приводят к ошибкам в логике, экспортах и несовпадению данных между сервисами/бэкапами.

## Decision
- Datetime:
  - Приём: принимать ISO8601 с/без timezone. На входе парсить, конвертировать в UTC.
  - Хранение: все datetime в БД в UTC (тип timestamptz / UTC-aware).
  - Отдача API: выдавать ISO8601 с `Z` (UTC) или с явно указанным timezone по запросу.

- Локаль/форматирование: presentation (локализация) — исключительно на UI/consumer-side; backend хранит нейтральные значения.
- Tests: фиксировать и проверять поточность в `tests/test_normalization.py`.

## Alternatives
- **Хранить в локальном времени** — проще, но возникают ошибки при смене TZ или DST.
- **Хранить строками** — гибко, но сложно для сравнения/агрегации.
 Выбран UTC-хаб как единая точка истины, безопасная для бэкапов и интеграций.

## Rollout plan
- Пилот: включить UTC-нормализацию на новых таблицах (`suggestions`, `tasks`).
- Миграции: добавить SQL-скрипт `migrations/003_normalize_datetime.sql` для конверсии старых данных.
- Feature-flag: `enable_utc_storage` для безопасного отката.

## Consequences
+ Уменьшает ошибки несогласованности времён.
- Требует миграций/проверок существующих данных при внедрении.
- Небольшая дополнительная валидация на входе.

## Links
- NFR-04 (performance / stability), NFR-10 (export privacy/consistency)
- F2, F3 (create/list suggestions)
- R5, R12
- Tests: `tests/test_normalization.py::test_datetime_stored_as_utc`, `tests/test_normalization.py::test_decimal_precision`
- Критерий закрытия: тесты на нормализацию проходят; экспорт/backup показывает ожидаемые UTC и Decimal представления (spot-check).
