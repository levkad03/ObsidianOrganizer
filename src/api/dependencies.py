import os

from fastapi import HTTPException

from src.agent.vault_registry import get_vault_path
from src.core.vault_manager import ObsidianVault


def get_valid_vault(thread_id: str) -> ObsidianVault:
    try:
        vault_path = get_vault_path(thread_id)
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Vault path not set for this thread."
        )

    if not os.path.exists(vault_path):
        raise HTTPException(status_code=404, detail="Vault path does not exist.")

    try:
        vault = ObsidianVault(vault_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize vault: {str(e)}"
        )

    return vault
