# ADR-001: Errors in RFC 7807 — mask PII & add correlation_id
Дата: 2025-10-21
Статус: Accepted

## Context
Ошибки в API возвращаются в произвольном формате и иногда раскрывают PII / внутренние детали. Нужен единый контракт ошибок, correlation_id для трассировки и гарантии маскировки PII.

## Decision
- Принять RFC 7807 (Problem Details) как единый формат ошибок для всех HTTP-эндпоинтов.
- Включать поля: `type`, `title`, `status`, `detail` (masked), `instance` (URI), `correlation_id`.
- Реализовать middleware/exception handler, который:
  - Всегда возвращает Problem JSON.
  - Маскирует/редактирует `detail` при обнаружении PII (фильтр по ключам: `email`, `user_id`, `password`, `ssn`, `token`).
  - Логирует исходный detail + correlation_id в защищённый audit-log (не в ошибку клиенту).
- Конфиг: список sensitive_fields в конфиге (можно расширять).
- Поведение по умолчанию: не выдавать стек-трейсы в production.

## Alternatives
- **Возврат произвольных JSON-ошибок** — быстро, но нет единого формата и защиты от PII.
- **Использование собственного формата ошибок** — больше гибкости, но не совместимо с RFC 7807.
- Выбрано RFC 7807 для совместимости с внешними API и стандартными библиотеками (FastAPI).

## Rollout plan
- Пилотное включение в dev-окружении через feature-flag `enable_rfc7807_errors`.
- Проверка тестами совместимости клиентов.

## Consequences
+ Единый контракт ошибок — проще клиентам и тестам.
+ PII не попадает в клиентский ответ; доступна трассировка по correlation_id.
- Требует обновления exception handlers и небольшого рефактора логирования.
- Небольшой оверхед при сериализации/маскировании.

## Links
- NFR-08, NFR-10
- F1, F3 (пример: login / get suggestions)
- Tests: `tests/test_errors.py::test_rfc7807_no_pii`, `tests/test_errors.py::test_correlation_id_present`
- Критерий закрытия (если закрывает риск): закрывает R8 — проверка: `tests/test_errors.py::test_rfc7807_no_pii` проходит, а оригинальные детали есть в audit-log (корреляция).
