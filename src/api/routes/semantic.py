from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.api.dependencies import get_valid_vault
from src.core.vault_manager import ObsidianVault
from src.services.semantic_service_v2 import SemanticServiceV2 as SemanticService

router = APIRouter(prefix="/semantic", tags=["semantic"])


def run_indexing_task(vault: ObsidianVault) -> None:
    """Background task to index the vault."""

    try:
        service = SemanticService(vault.path)
        print(f"Starting indexing for vault: {vault.path}")
        stats = service.index_vault()
        print(f"Indexing complete: {stats}")

    except Exception as e:
        print(f"Indexing failed: {e}")
        import traceback

        traceback.print_exc()


@router.post("/index")
async def trigger_indexing(
    background_tasks: BackgroundTasks, vault: ObsidianVault = Depends(get_valid_vault)
):
    """Trigger a full re-indexing of the vault in the background."""
    background_tasks.add_task(run_indexing_task, vault)
    return {"status": "accepted", "message": "Indexing started in background"}


@router.post("/index/note")
async def index_single_note(
    note_path: str, vault: ObsidianVault = Depends(get_valid_vault)
):
    """Index or re-index single note."""

    service = SemanticService(vault.path)

    # Convert to absolute path
    full_path = vault.path / note_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Note not found: {note_path}")

    try:
        chunks = service.index_note(full_path)
        return {"status": "success", "note": note_path, "chunks_indexed": chunks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@router.get("/search")
async def search_notes(
    query: str,
    top_k: int = 5,
    tags: str | None = None,  # Comma-separated tags
    vault: ObsidianVault = Depends(get_valid_vault),
) -> dict:
    """Perform a semantic search."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    service = SemanticService(vault.path)

    # Parse tags if provided
    filter_tags = None
    if tags:
        filter_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    try:
        results = service.search_by_text(query, top_k=top_k, filter_tags=filter_tags)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/similar/{note_name}")
async def find_similar_notes(
    note_name: str,
    top_k: int = 5,
    vault: ObsidianVault = Depends(get_valid_vault),
) -> dict:
    """Find notes similar to a given note."""
    service = SemanticService(vault.path)

    try:
        results = service.find_similar_notes(note_name, top_k=top_k)

        if not results["documents"][0]:
            raise HTTPException(
                status_code=404, detail=f"Note '{note_name}' not found in index"
            )

        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def get_index_stats(
    vault: ObsidianVault = Depends(get_valid_vault),
) -> dict:
    """Get indexing statistics for the vault."""
    service = SemanticService(vault.path)

    try:
        stats = service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/index")
async def clear_index(
    vault: ObsidianVault = Depends(get_valid_vault),
) -> dict:
    """Clear all indexed data for the vault."""
    service = SemanticService(vault.path)

    try:
        service.clear_index()
        return {"status": "success", "message": "Index cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")
