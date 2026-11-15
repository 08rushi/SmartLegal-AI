"""Schema parity: database.create_tables() vs `alembic upgrade head` (SQLite, temp files only)."""
import os
import sqlite3
import subprocess
import sys

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CREATE_TABLES_SCRIPT = (
    "import asyncio, database;"
    "database._db_pool = database.SQLitePoolWrapper(r'{path}');"
    "asyncio.run(database.create_tables())"
)


def _env(db_path):
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["ENVIRONMENT"] = "development"
    return env


def _run(args, db_path):
    res = subprocess.run(args, cwd=BACKEND, env=_env(db_path), capture_output=True, text=True, timeout=180)
    assert res.returncode == 0, f"{args}\nSTDOUT:{res.stdout}\nSTDERR:{res.stderr}"


def _snapshot(path):
    con = sqlite3.connect(path)
    try:
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'")]
        snap = {"tables": sorted(tables), "columns": {}, "indexes": {}, "fks": {}, "uniques": {}}
        for t in tables:
            snap["columns"][t] = sorted(
                (r[1], (r[2] or "").upper(), r[3], (r[4] or "").strip("'"), r[5])
                for r in con.execute(f"PRAGMA table_info({t})"))
            snap["fks"][t] = sorted(
                (r[2], r[3], r[4], r[6]) for r in con.execute(f"PRAGMA foreign_key_list({t})"))
            idx, uniq = set(), set()
            for r in con.execute(f"PRAGMA index_list({t})"):
                name, is_unique, origin = r[1], r[2], r[3]
                cols = tuple(c[2] for c in con.execute(f"PRAGMA index_info({name})"))
                if origin == "c":
                    idx.add((name, cols, bool(is_unique)))
                elif is_unique:
                    uniq.add(cols)  # UNIQUE constraints / PK autoindexes, name-agnostic
            snap["indexes"][t] = sorted(idx)
            snap["uniques"][t] = sorted(uniq)
        return snap
    finally:
        con.close()


@pytest.fixture(scope="module")
def snapshots(tmp_path_factory):
    d = tmp_path_factory.mktemp("schema_parity")
    ct_db, al_db = str(d / "create_tables.db"), str(d / "alembic.db")
    _run([sys.executable, "-c", _CREATE_TABLES_SCRIPT.format(path=ct_db)], ct_db)
    _run([sys.executable, "-m", "alembic", "upgrade", "head"], al_db)
    return _snapshot(ct_db), _snapshot(al_db), ct_db, al_db


def test_tables_match(snapshots):
    ct, al, *_ = snapshots
    assert ct["tables"] == al["tables"]


def test_columns_match(snapshots):
    ct, al, *_ = snapshots
    for t in ct["tables"]:
        assert ct["columns"][t] == al["columns"][t], f"column drift in {t}"


def test_indexes_match(snapshots):
    ct, al, *_ = snapshots
    for t in ct["tables"]:
        assert ct["indexes"][t] == al["indexes"][t], f"index drift in {t}"
        assert ct["uniques"][t] == al["uniques"][t], f"unique constraint drift in {t}"


def test_foreign_keys_match(snapshots):
    ct, al, *_ = snapshots
    for t in ct["tables"]:
        assert ct["fks"][t] == al["fks"][t], f"FK drift in {t}"


def test_alembic_upgrade_idempotent_on_create_tables_db(snapshots, tmp_path):
    """Migrations must be safe on a DB already built by create_tables()."""
    ct_db = str(tmp_path / "pre_existing.db")
    _run([sys.executable, "-c", _CREATE_TABLES_SCRIPT.format(path=ct_db)], ct_db)
    before = _snapshot(ct_db)
    _run([sys.executable, "-m", "alembic", "upgrade", "head"], ct_db)
    after = _snapshot(ct_db)
    assert before == after
