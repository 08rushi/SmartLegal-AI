# Database migrations (Alembic)

Migrations are the source of truth for schema changes going forward. The app also
runs an idempotent `create_tables()` on startup (safe `CREATE TABLE IF NOT EXISTS`)
so development works without migrations, but **production should apply migrations**:

```bash
cd backend
venv/Scripts/activate           # Linux/macOS: source venv/bin/activate
alembic upgrade head            # apply all migrations to DATABASE_URL (from .env)
```

Other useful commands:

```bash
alembic current                 # show the DB's current revision
alembic history                 # list revisions
alembic downgrade -1            # roll back one revision
alembic revision -m "add X"     # create a new (empty) migration to edit
alembic upgrade --sql head      # print SQL without touching the DB (review)
```

Notes:
- The DB URL is read from app settings (`DATABASE_URL` in `.env`) via `env.py`;
  SSL is added automatically for Supabase hosts.
- Baseline `0001` uses `CREATE TABLE IF NOT EXISTS`, so `alembic upgrade head` is
  safe to run on a database whose tables were already auto-created by the app.
- After deploying, run `alembic upgrade head` before starting the API. To stop the
  app from auto-creating tables in production, gate `create_tables()` on a non-prod
  environment once you've adopted migrations fully.
