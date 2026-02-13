# Database Migrations

This directory contains Alembic database migrations for the AI Receptionist backend.

## Setup

Alembic is already configured. The migration scripts are located in `alembic/versions/`.

## Environment Variables

Make sure your `.env` file contains a valid `DATABASE_URL`:

```
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname
```

## Running Migrations

### Upgrade (Apply migrations)

```bash
# From the backend directory
alembic upgrade head
```

This will apply all pending migrations in order.

### Downgrade (Rollback migrations)

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific migration
alembic downgrade <revision_id>

# Rollback to base (remove all migrations)
alembic downgrade base
```

### Create a New Migration

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration for custom SQL
alembic revision -m "description of changes"
```

## Current Migrations

### 001_initial_schema.py
Creates the initial database schema with the following tables:
- `users` - User accounts and authentication
- `businesses` - Business profiles
- `call_sessions` - Active call tracking
- `conversation_messages` - Chat/message logs
- `system_logs` - Application logging
- `audit_logs` - Audit trail for operations
- `integrations` - Third-party integrations
- `ai_training_scenarios` - AI training data
- `appointments` - Appointment scheduling
- `call_logs` - Call history

Also creates:
- Indexes for performance optimization
- Check constraints for data integrity
- Foreign key relationships
- `updated_at` trigger function and triggers
- Default admin user (email: admin@ai-receptionist.com, password: admin123456)

## Troubleshooting

### Migration conflicts
If you encounter conflicts, check the current revision:
```bash
alembic current
```

### View migration history
```bash
alembic history
```

### View SQL without executing
```bash
alembic upgrade head --sql
```

## Notes

- The initial migration creates a default admin user. **Change the password immediately after first deployment.**
- All tables have `created_at` and `updated_at` timestamps
- The `updated_at` field is automatically updated via database triggers
- Sensitive data like passwords are hashed before storage