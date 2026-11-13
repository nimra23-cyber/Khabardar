"""Tests for the idempotent single-local-user seed (Task 2.1 correction).

Covers:
- First-run seeding creates exactly one local user.
- Repeated startup does NOT create duplicates (idempotent).
- The seeded user carries no credential (password_hash/role are None).
- The fixed username is used; the UNIQUE(username) constraint holds.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.seed import LOCAL_USERNAME, get_or_create_local_user
from app.models import User


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def test_first_run_creates_single_local_user(db):
    user = get_or_create_local_user(db)
    assert user.username == LOCAL_USERNAME
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_seeded_user_has_no_credential(db):
    user = get_or_create_local_user(db)
    # MVP is auth-less: no password, no role (Scope B seam left null).
    assert user.password_hash is None
    assert user.role is None


def test_repeated_startup_is_idempotent(db):
    first = get_or_create_local_user(db)
    second = get_or_create_local_user(db)
    third = get_or_create_local_user(db)
    # Same row every time; never a duplicate.
    assert first.id == second.id == third.id
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_username_is_unique_constraint_backed(db):
    get_or_create_local_user(db)
    # A manual duplicate insert of the same username must fail at the DB level.
    from sqlalchemy.exc import IntegrityError

    db.add(User(username=LOCAL_USERNAME))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_seed_local_user_via_startup_hook_is_idempotent(tmp_path, monkeypatch):
    """Exercise the startup-hook entrypoint against a real temp SQLite DB,
    simulating two application starts; the user must exist exactly once."""
    db_file = tmp_path / "seed_startup.db"
    url = f"sqlite:///{db_file.as_posix()}"

    # Point the app's session factory at the temp DB BEFORE importing it.
    monkeypatch.setenv("KHABARDAR_DATABASE_URL", url)

    # Build a fresh engine/session bound to the temp DB and create the schema.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import seed as seed_module
    from app.db.base import Base

    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    TempSession = sessionmaker(bind=engine, future=True)

    # Redirect the seed's SessionLocal to our temp session factory.
    monkeypatch.setattr("app.db.session.SessionLocal", TempSession, raising=False)

    # Two "startups".
    seed_module.seed_local_user()
    seed_module.seed_local_user()

    from sqlalchemy import func, select

    with TempSession() as s:
        count = s.scalar(select(func.count()).select_from(User))
    assert count == 1


# --- Startup lifespan error-handling (narrowed, per Task 2.1 correction) ----


def test_missing_schema_error_is_classified_as_missing_schema():
    """A 'no such table' OperationalError (unmigrated DB) is tolerated."""
    from sqlalchemy.exc import OperationalError

    from app.main import _is_missing_schema_error

    # Simulate SQLite's missing-table error wrapped by SQLAlchemy.
    exc = OperationalError("SELECT ...", {}, Exception("no such table: users"))
    assert _is_missing_schema_error(exc) is True


def test_generic_db_error_is_not_classified_as_missing_schema():
    """A genuine DB error (e.g. disk/IO) must NOT be treated as missing schema,
    so the lifespan re-raises it instead of silently skipping the seed."""
    from sqlalchemy.exc import OperationalError

    from app.main import _is_missing_schema_error

    exc = OperationalError("SELECT ...", {}, Exception("database disk image is malformed"))
    assert _is_missing_schema_error(exc) is False


def test_non_db_error_is_not_classified_as_missing_schema():
    """Arbitrary non-DBAPI exceptions are never treated as missing schema."""
    from app.main import _is_missing_schema_error

    assert _is_missing_schema_error(ValueError("boom")) is False


def test_lifespan_reraises_genuine_seed_error(monkeypatch):
    """The startup lifespan re-raises a non-missing-schema seed error rather
    than swallowing it as a 'skipped' success."""
    import asyncio

    import app.main as main_module

    class _Boom(RuntimeError):
        pass

    def _boom_seed():
        raise _Boom("genuine failure")

    # Patch the imported-inside-lifespan symbol path.
    monkeypatch.setattr("app.db.seed.seed_local_user", _boom_seed, raising=True)

    async def _run():
        async with main_module.lifespan(object()):
            pass

    with pytest.raises(_Boom):
        asyncio.run(_run())


def test_lifespan_tolerates_missing_schema(monkeypatch):
    """The startup lifespan tolerates a missing-schema error (skips seeding)."""
    import asyncio

    from sqlalchemy.exc import OperationalError

    import app.main as main_module

    def _missing_schema_seed():
        raise OperationalError("SELECT ...", {}, Exception("no such table: users"))

    monkeypatch.setattr(
        "app.db.seed.seed_local_user", _missing_schema_seed, raising=True
    )

    async def _run():
        async with main_module.lifespan(object()):
            return True

    # Should NOT raise -- missing schema is tolerated.
    assert asyncio.run(_run()) is True
