import os

from fastapi import APIRouter, HTTPException

from src.agent.vault_registry import get_vault_path
from src.core.vault_manager import ObsidianVault
from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(thread_id: str):
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
        dashboard_service = DashboardService(vault)
        summary = dashboard_service.summary()

        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process vault dashboard: {str(e)}"
        )


@router.get("/orphaned")
async def get_orphaned_notes(thread_id: str):
    try:
        vault_path = get_vault_path(thread_id)
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Vault path not set for this thread."
        )

    vault = ObsidianVault(vault_path)
    return {"orphaned_notes": vault.find_orphaned_notes()}


@router.get("/broken-links")
async def get_broken_links(thread_id: str):
    try:
        vault_path = get_vault_path(thread_id)
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Vault path not set for this thread."
        )

    vault = ObsidianVault(vault_path)
    return vault.find_broken_links()


@router.get("/untagged")
async def get_untagged_notes(thread_id: str):
    try:
        vault_path = get_vault_path(thread_id)
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Vault path not set for this thread."
        )

    vault = ObsidianVault(vault_path)
    index = vault.build_index()

    untagged = [name for name, info in index.items() if not info.get("has_tags", False)]

    return {"untagged_notes": untagged}
