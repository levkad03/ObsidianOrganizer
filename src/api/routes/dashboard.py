from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_valid_vault
from src.core.vault_manager import ObsidianVault
from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(vault: ObsidianVault = Depends(get_valid_vault)):
    try:
        dashboard_service = DashboardService(vault)
        summary = dashboard_service.summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate dashboard summary: {str(e)}"
        )


@router.get("/orphaned")
async def get_orphaned_notes(vault: ObsidianVault = Depends(get_valid_vault)):
    return {"orphaned_notes": vault.find_orphaned_notes()}


@router.get("/broken-links")
async def get_broken_links(vault: ObsidianVault = Depends(get_valid_vault)):
    return vault.find_broken_links()


@router.get("/untagged")
async def get_untagged_notes(vault: ObsidianVault = Depends(get_valid_vault)):
    dashboard_service = DashboardService(vault)
    return {"untagged_notes": dashboard_service.get_untagged_notes()}
