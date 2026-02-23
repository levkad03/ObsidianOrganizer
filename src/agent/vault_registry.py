from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from src.core import database
from src.core.models import Vault

_CACHE: dict[str, Path] = {}
database.init_db()


def set_vault(thread_id: str, path: str) -> None:
    p = Path(path).expanduser().resolve()

    if not p.exists():
        raise ValueError(f"Vault path does not exist: {p}")

    if not p.is_dir():
        raise ValueError(f"Vault path is not a directory: {p}")

    _CACHE[thread_id] = p
    session = database.SessionLocal()
    try:
        obj = session.get(Vault, thread_id)
        if obj is None:
            obj = Vault(thread_id=thread_id, vault_path=str(p))
            session.add(obj)
        else:
            obj.vault_path = str(p)

    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.commit()
        session.close()


def get_vault_path(thread_id: str) -> Path | None:
    if thread_id in _CACHE:
        return _CACHE[thread_id]

    session = database.SessionLocal()
    try:
        obj = session.get(Vault, thread_id)
        if obj:
            p = Path(obj.vault_path)
            _CACHE[thread_id] = p
            return p

    finally:
        session.close()

    return None
