# Security Policy

## Credentials Management

### Environment Variables
- **NEVER** commit `.env` file to Git (already in `.gitignore`)
- Use `.env.example` as a template
- All sensitive credentials MUST be in `.env` file:
  - Database passwords
  - Default user passwords
  - API keys (if any)

### Production Deployment
For production, use:
- Docker secrets
- Kubernetes secrets
- AWS Secrets Manager / HashiCorp Vault
- **NEVER** use default passwords from `.env.example`

### Password Requirements
- Database password: minimum 16 characters
- User passwords: minimum 8 characters (enforced by registration)
- Use strong random passwords (not "password123")

## Security Best Practices

- Пожалуйста, **не** храните ключи/секреты в репозитории.
- Сообщайте об уязвимостях преподавателю/ТА через приватный канал.
- В коде используйте единый формат ошибок (см. README).
- Во время курса используйте **синтетические** данные (без ПДн/платежей).

## Current Security Features

✅ **Implemented:**
- Argon2id password hashing (NFR-01 compliant)
- Rate limiting by username and IP
- JWT token TTL (1 hour)
- Environment-based credentials
- Owner-only authorization for suggestions

⚠️ **Partially Implemented:**
- Tokens stored in-memory (not persistent)
- No refresh tokens mechanism

🔴 **TODO:**
- Move tokens to database or Redis
- Implement JWT signing with secret key
- Add audit logging
- Implement secrets rotation
