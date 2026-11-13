"""Tests for the parameterized repository layer and the enforced privacy/XSS
persistence boundary (Task 2.4, Req 19.6, 19.7, 21).

These tests inspect ACTUAL persisted database values (they do not mock the
privacy/sanitize services and assert they were called). They open a real
in-memory SQLite database, write through the repository, then re-read the row
to confirm what is actually stored.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.scan_history import ScanHistory
from app.models.user import User
from app.repositories.base import BaseRepository
from app.repositories.scan_history import ScanHistoryRepository, harden_content
from app.services.privacy import contains_plaintext_secret
from app.services.sanitize import is_neutralized


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


@pytest.fixture
def user(db) -> User:
    u = User(username="local")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# --- base repository: parameterized CRUD -----------------------------------


def test_base_repository_crud_roundtrip(db, user):
    repo = ScanHistoryRepository(db)
    rec = repo.create_scan(user_id=user.id, scan_type="text", raw_content="hello")
    assert rec.id is not None
    # get() by PK
    fetched = repo.get(rec.id)
    assert fetched is not None and fetched.id == rec.id
    # count()
    assert repo.count() == 1
    # delete()
    repo.delete(fetched)
    assert repo.get(rec.id) is None
    assert repo.count() == 0


def test_list_is_user_scoped_and_parameterized(db):
    u1 = User(username="u1")
    u2 = User(username="u2")
    db.add_all([u1, u2])
    db.commit()
    repo = ScanHistoryRepository(db)
    repo.create_scan(user_id=u1.id, scan_type="text", raw_content="a")
    repo.create_scan(user_id=u1.id, scan_type="text", raw_content="b")
    repo.create_scan(user_id=u2.id, scan_type="text", raw_content="c")
    u1_rows = repo.list_for_user(u1.id)
    u2_rows = repo.list_for_user(u2.id)
    assert len(u1_rows) == 2
    assert len(u2_rows) == 1
    assert all(r.user_id == u1.id for r in u1_rows)


def test_user_id_filter_binds_injection_string_literally(db, user):
    """A SQLi-style user_id is treated as a literal bound value, not SQL.

    If the value were interpolated into SQL, this crafted string could alter
    the query. With parameterized ORM access it simply matches no rows.
    """
    repo = ScanHistoryRepository(db)
    repo.create_scan(user_id=user.id, scan_type="text", raw_content="safe")
    injection = "' OR '1'='1"
    rows = repo.list_for_user(injection)
    # No row has that literal user_id, so nothing matches (query not subverted).
    assert rows == []
    # The legitimate row is still present and intact.
    assert repo.count() == 1


# --- privacy enforced at the persistence boundary (Req 21) -----------------


SECRET_SCANS = [
    "Your OTP is 918273, do not share it",
    "login password: SuperSecret99 now",
    "Authorization: Bearer abc123def456ghi789",
    "token=eyJhbGciOiJIUzI1Ni9.payloadpart.signaturepart",
    "CNIC 35202-1234567-8 verify now",
    "pay to account 1234567890123456 immediately",
    "call +92 300 1234567 for your prize",
    "email victim@example.com to claim",
]


@pytest.mark.parametrize("raw", SECRET_SCANS)
def test_sensitive_content_not_stored_in_plaintext(db, user, raw):
    repo = ScanHistoryRepository(db)
    rec = repo.create_scan(user_id=user.id, scan_type="text", raw_content=raw)

    # Re-read the ACTUAL stored value from the DB (fresh query, not the object
    # we just built in memory).
    stored = db.scalar(
        select(ScanHistory.masked_content).where(ScanHistory.id == rec.id)
    )
    assert stored is not None
    assert not contains_plaintext_secret(stored, raw), (
        f"plaintext secret persisted: {raw!r} -> {stored!r}"
    )


def test_raw_content_not_persisted_in_any_column(db, user):
    raw = "Your OTP is 918273 and password: SuperSecret99"
    repo = ScanHistoryRepository(db)
    rec = repo.create_scan(
        user_id=user.id,
        scan_type="text",
        raw_content=raw,
        explanation_en="analysis",
        explanation_ur="تجزیہ",
    )
    # Dump every column value for the row and assert the raw secret substrings
    # do not appear ANYWHERE (not just masked_content).
    row = db.get(ScanHistory, rec.id)
    blob = " ".join(
        str(getattr(row, col))
        for col in (
            "masked_content",
            "explanation_en",
            "explanation_ur",
            "category",
            "classification",
        )
    )
    assert "918273" not in blob
    assert "SuperSecret99" not in blob


def test_stored_content_is_neutralized_of_markup(db, user):
    raw = "WIN NOW <script>steal()</script> click <a href='javascript:x'>here</a>"
    repo = ScanHistoryRepository(db)
    rec = repo.create_scan(user_id=user.id, scan_type="text", raw_content=raw)
    stored = db.scalar(
        select(ScanHistory.masked_content).where(ScanHistory.id == rec.id)
    )
    assert "<script" not in stored.lower()
    assert "javascript:" not in stored.lower()
    assert "steal()" not in stored
    assert "<" not in stored and ">" not in stored
    assert is_neutralized(stored)


def test_combined_secret_and_xss_both_neutralized(db, user):
    raw = "<script>x()</script> your OTP is 445566 password: topsecretvalue"
    repo = ScanHistoryRepository(db)
    rec = repo.create_scan(user_id=user.id, scan_type="text", raw_content=raw)
    stored = db.scalar(
        select(ScanHistory.masked_content).where(ScanHistory.id == rec.id)
    )
    assert is_neutralized(stored)
    assert not contains_plaintext_secret(stored, raw)
    assert "topsecretvalue" not in stored


def test_harden_content_boundary_is_single_source():
    # The transform used by the repository is exactly harden_content, which is
    # mask-then-neutralize. Verify the composition directly.
    raw = "OTP 123456 <script>evil()</script>"
    out = harden_content(raw)
    assert out is not None
    assert is_neutralized(out)
    assert "123456" not in out  # 6-char code: hidden prefix masked
    assert "evil()" not in out
    assert harden_content(None) is None


# --- rollback / failed-write behavior (Req 20.4) ---------------------------


def test_failed_write_rolls_back_no_partial_row(db):
    """A write that violates a constraint rolls back; no partial row remains."""
    repo = ScanHistoryRepository(db)
    # user_id has a NOT NULL + FK constraint; force a failure by passing None.
    from sqlalchemy.exc import IntegrityError

    with pytest.raises((IntegrityError, Exception)):
        repo.create_scan(user_id=None, scan_type="text", raw_content="x")

    # The session was rolled back by BaseRepository.add; it is usable and no
    # scan row was persisted.
    assert repo.count() == 0
    # A subsequent valid write still works (session not poisoned).
    u = User(username="recovered")
    db.add(u)
    db.commit()
    rec = repo.create_scan(user_id=u.id, scan_type="text", raw_content="ok")
    assert repo.get(rec.id) is not None


def test_no_raw_sql_text_construct_used_in_repository_modules():
    """Guard: repository source contains no raw text() SQL (Req 19.7).

    Parameterized ORM is used exclusively; this asserts the modules do not
    import/invoke SQLAlchemy's raw text() for query construction. We match the
    `text(` call form but allow the `Text` column TYPE (capital T).
    """
    import inspect

    import app.repositories.base as base_mod
    import app.repositories.scan_history as sh_mod

    raw_text_call = re.compile(r"\btext\s*\(")
    for mod in (base_mod, sh_mod):
        src = inspect.getsource(mod)
        assert not raw_text_call.search(src), (
            f"raw text() SQL found in {mod.__name__}"
        )


# --- boundary regression guards: no ScanHistory write bypasses the repo -----

_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
_REPO_FILE = _APP_DIR / "repositories" / "scan_history.py"
_MODEL_FILE = _APP_DIR / "models" / "scan_history.py"
# Files permitted to construct ScanHistory or write masked_content:
#  - the repository (the enforced boundary itself),
#  - the model definition (declares the column).
_ALLOWED_BOUNDARY_FILES = {_REPO_FILE.resolve(), _MODEL_FILE.resolve()}


def _app_python_files():
    return [
        p
        for p in _APP_DIR.rglob("*.py")
        if "__pycache__" not in p.parts
    ]


def test_scan_history_construction_only_in_repository_or_model():
    """Repository-enforced boundary regression guard.

    This is NOT language-level enforcement: Python cannot prevent a future
    developer from constructing ``ScanHistory(...)`` directly. Instead this
    test fails CI if any app source OUTSIDE the repository (or the model file)
    constructs a ScanHistory or assigns ``masked_content=``, which would
    bypass the mask+neutralize boundary in ``harden_content``.
    """
    construct = re.compile(r"\bScanHistory\s*\(")
    masked_write = re.compile(r"\bmasked_content\s*=")

    offenders = []
    for path in _app_python_files():
        if path.resolve() in _ALLOWED_BOUNDARY_FILES:
            continue
        src = path.read_text(encoding="utf-8")
        if construct.search(src) or masked_write.search(src):
            offenders.append(str(path))

    assert not offenders, (
        "ScanHistory is written outside the repository boundary in: "
        + ", ".join(offenders)
        + ". Route all scan writes through ScanHistoryRepository.create_scan "
        "so content is masked + neutralized (Req 19.6, 21)."
    )


def test_boundary_guard_is_not_vacuous(tmp_path):
    """Prove the boundary guard actually detects a bypass.

    We synthesize a fake module source that constructs ScanHistory directly and
    confirm the same regexes used by the guard flag it -- so the guard above is
    meaningful, not vacuous.
    """
    bypass_src = (
        "from app.models.scan_history import ScanHistory\n"
        "rec = ScanHistory(masked_content=raw_input)\n"
    )
    construct = re.compile(r"\bScanHistory\s*\(")
    masked_write = re.compile(r"\bmasked_content\s*=")
    assert construct.search(bypass_src)
    assert masked_write.search(bypass_src)
