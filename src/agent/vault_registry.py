from pathlib import Path

_VAULTS: dict[str, Path] = {}


def set_vault(thread_id: str, path: str) -> None:
    p = Path(path).expanduser().resolve()

    if not p.exists():
        raise ValueError(f"Vault apth does not exist: {p}")

    if not p.is_dir():
        raise ValueError(f"Vault path is not a directory: {p}")

    _VAULTS[thread_id] = p


def get_vault_path(thread_id: str) -> Path | None:
    return _VAULTS.get(thread_id)
