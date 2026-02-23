from pathlib import Path

import pytest

from src.agent import vault_registry
from src.core import database
from src.core.models import Vault

# The database and vault_registry imports are deferred until after the
# VAULT_DB_PATH environment variable is configured by the fixture below.


@pytest.fixture(autouse=True)
def use_tmp_db(tmp_path, monkeypatch):
    """Force the database layer to use a fresh sqlite file per test.

    We must set the environment variable **before** the modules are imported,
    otherwise the SQLAlchemy engine will already be initialized with the
    default path.  To accomplish that we import (and reload) the modules
    inside the fixture after patching the env var.
    """

    dbfile = tmp_path / "test.db"
    monkeypatch.setenv("VAULT_DB_PATH", str(dbfile))

    database.init_db()

    vault_registry._CACHE.clear()
    yield


def test_set_and_get_persists(tmp_path):
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    tid = "abc-123"

    # Store the mapping
    vault_registry.set_vault(tid, str(vault_dir))

    # Confirm in-memory cache works
    assert vault_registry.get_vault_path(tid) == vault_dir

    # Simulate restart by clearing cache
    vault_registry._CACHE.clear()

    # Now retrieval must hit the database
    assert vault_registry.get_vault_path(tid) == vault_dir

    # The underlying database should contain the row (use SQLAlchemy session)
    session = database.SessionLocal()
    try:
        obj = session.get(Vault, tid)
        assert obj is not None
        assert Path(obj.vault_path) == vault_dir
    finally:
        session.close()


def test_invalid_vault_path_errors():
    with pytest.raises(ValueError):
        vault_registry.set_vault("x", "does/not/exist")


def test_overwrite_existing_mapping(tmp_path):
    first = tmp_path / "vault1"
    first.mkdir()
    second = tmp_path / "vault2"
    second.mkdir()
    tid = "xyz"

    vault_registry.set_vault(tid, str(first))
    vault_registry.set_vault(tid, str(second))

    vault_registry._CACHE.clear()
    assert vault_registry.get_vault_path(tid) == second
