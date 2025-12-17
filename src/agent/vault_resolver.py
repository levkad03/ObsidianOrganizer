from langchain_core.runnables import RunnableConfig

from src.agent.vault_registry import get_vault_path
from src.core.vault_manager import ObsidianVault


def resolve_vault(config: RunnableConfig) -> ObsidianVault:
    thread_id = config["configurable"]["thread_id"]
    path = get_vault_path(thread_id)

    if path is None:
        raise RuntimeError(
            "Obsidian vault is not configured. Call the /chat/set-vault endpoint first."
        )

    return ObsidianVault(path)
