from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.api.dependencies import get_valid_vault
from src.core.vault_manager import ObsidianVault
from src.services.semantic_service import SemanticService

router = APIRouter(prefix="/semantic", tags=["semantic"])


def run_indexing_task(vault: ObsidianVault):
    """Background task to index the vault."""

    try:
        service = SemanticService(vault.path)

        # 1. Gather all notes
        notes_to_index = []
        all_notes = vault.list_notes()

        for note_path in all_notes:
            try:
                # Get path relative to vault root
                relative_path = str(note_path.relative_to(vault.path))
                # Name without extension
                note_name = str(note_path.relative_to(vault.path).with_suffix(""))

                # Read content
                note_data = vault.read_note(relative_path)
                notes_to_index.append(
                    (note_name, note_data["content"], note_data["metadata"])
                )
            except Exception as e:
                print(f"Skipping note {note_path}: {e}")
                continue

        # 2. Run indexing
        print(f"Starting indexing for {len(notes_to_index)} notes...")
        stats = service.index_vault(notes_to_index)
        print(f"Indexing complete: {stats}")
    except Exception as e:
        print(f"Indexing failed: {e}")


@router.post("/index")
async def trigger_indexing(
    background_tasks: BackgroundTasks, vault: ObsidianVault = Depends(get_valid_vault)
):
    """Trigger a full re-indexing of the vault in the background."""
    background_tasks.add_task(run_indexing_task, vault)
    return {"status": "accepted", "message": "Indexing started in background"}


@router.get("/search")
async def search_notes(
    query: str,
    top_k: int = 5,
    vault: ObsidianVault = Depends(get_valid_vault),
):
    """Perform  a semantic search."""
    service = SemanticService(vault.path)
    return service.search_by_text(query, top_k=top_k)
