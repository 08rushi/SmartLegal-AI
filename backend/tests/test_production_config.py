"""AUTO_CREATE_SCHEMA flag, Alembic head check and production config validation (SQLite only)."""
import asyncio

import pytest

import config
import database
from config import Settings, validate_production_config

GOOD = dict(
    ENVIRONMENT="production",
    SECRET_KEY="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f6",
    DATABASE_URL="postgresql://u:p@db.example.com:5432/postgres",
    ALLOWED_ORIGINS="https://app.example.com",
    CLOUDINARY_CLOUD_NAME="c", CLOUDINARY_API_KEY="k", CLOUDINARY_API_SECRET="s",
)


def mk(**kw):
    d = {**GOOD, **kw}
    noalias = ("ALLOWED_ORIGINS", "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
    return Settings(_env_file=None, **{(k.lower() if k in noalias else k): v for k, v in d.items()})


def test_auto_create_defaults():
    assert mk(ENVIRONMENT="development", DATABASE_URL="sqlite:///x.db").effective_auto_create_schema is True
    assert mk(ENVIRONMENT="development").effective_auto_create_schema is True
    assert mk(ENVIRONMENT="production", DATABASE_URL="sqlite:///x.db").effective_auto_create_schema is True
    assert mk().effective_auto_create_schema is False  # production + postgres


def test_auto_create_explicit_override():
    assert mk(AUTO_CREATE_SCHEMA="true").effective_auto_create_schema is True
    assert mk(ENVIRONMENT="development", AUTO_CREATE_SCHEMA="false").effective_auto_create_schema is False
    assert mk(AUTO_CREATE_SCHEMA="").effective_auto_create_schema is False  # blank = auto


def test_prepare_schema_flag_states(monkeypatch):
    calls = []

    async def fake_create():
        calls.append("create")

    async def fake_verify():
        calls.append("verify")

    monkeypatch.setattr(database, "create_tables", fake_create)
    monkeypatch.setattr(database, "verify_schema_at_head", fake_verify)

    monkeypatch.setattr(database.settings, "auto_create_schema", True)
    asyncio.run(database.prepare_schema())
    monkeypatch.setattr(database.settings, "auto_create_schema", False)
    asyncio.run(database.prepare_schema())
    assert calls == ["create", "verify"]


def test_verify_head_ok_and_mismatch(monkeypatch):
    head = database.get_alembic_head()
    assert head

    async def at_head():
        return head

    monkeypatch.setattr(database, "get_db_revision", at_head)
    asyncio.run(database.verify_schema_at_head())

    async def behind():
        return "0001"

    monkeypatch.setattr(database, "get_db_revision", behind)
    with pytest.raises(database.SchemaNotAtHeadError, match="alembic upgrade head"):
        asyncio.run(database.verify_schema_at_head())

    async def none():
        return None

    monkeypatch.setattr(database, "get_db_revision", none)
    with pytest.raises(database.SchemaNotAtHeadError):
        asyncio.run(database.verify_schema_at_head())


def test_production_valid_config_has_no_errors():
    errors, _ = validate_production_config(mk())
    assert errors == []


@pytest.mark.parametrize("override,fragment", [
    (dict(SECRET_KEY="short"), "SECRET_KEY"),
    (dict(SECRET_KEY="changeme" * 5), "placeholder"),
    (dict(DATABASE_URL="sqlite:///x.db"), "DATABASE_URL"),
    (dict(ALLOWED_ORIGINS=""), "ALLOWED_ORIGINS"),
    (dict(ALLOWED_ORIGINS="*"), "ALLOWED_ORIGINS"),
    (dict(ALLOWED_ORIGINS="http://localhost:5173"), "localhost"),
    (dict(CLOUDINARY_API_SECRET=""), "Cloudinary"),
])
def test_production_errors(override, fragment):
    errors, _ = validate_production_config(mk(**override))
    assert any(fragment in e for e in errors), errors


def test_production_warnings_and_no_secret_leak():
    s = mk()
    errors, warnings = validate_production_config(s)
    joined = " ".join(warnings)
    for name in ("SENTRY_DSN", "RESEND_API_KEY", "REDIS_URL"):
        assert name in joined
    bad = mk(SECRET_KEY="changeme" * 5)
    errs, _ = validate_production_config(bad)
    assert "changeme" not in " ".join(errs)


def test_non_production_skips_validation():
    assert validate_production_config(mk(ENVIRONMENT="development", SECRET_KEY="x")) == ([], [])


def test_get_settings_raises_in_production(monkeypatch):
    monkeypatch.setattr(config, "Settings", lambda: mk(ALLOWED_ORIGINS=""))
    with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
        config.get_settings.__wrapped__()  # type: ignore[attr-defined]
