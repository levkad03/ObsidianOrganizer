import hashlib
from pathlib import Path


class SemanticConfig:
    """Configuration for semantic search and embeddings."""

    # Embedding model settings (Ollama)
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSION: int = 768  # nomic-embed-text uses 768 dims
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ChromaDB settings - stored in project root, not in vault
    CHROMA_DATA_DIR: str = ".semantic_data"  # Relative to project root
    CHROMA_COLLECTION_NAME: str = "obsidian_notes"

    # Chunking strategy
    CHUNK_SIZE: int = 500  # Characters per chunk
    CHUNK_OVERLAP: int = 100  # Overlap between chunks
    CHUNK_BY_HEADERS: bool = True  # Split by markdown headers first

    # Search settings
    TOP_K_RESULTS: int = 5  # Default number of similar notes
    SIMILARITY_THRESHOLD: float = 0.4  # Minimum similarity score (0-1)

    # Indexing settings
    BATCH_SIZE: int = 32  # Notes to embed in one batch
    AUTO_UPDATE_ON_VAULT_CHANGE: bool = True  # Re-embed when notes change

    @classmethod
    def get_chroma_path(cls, vault_path: Path | str) -> Path:
        """Get the full path to the ChromaDB data directory.

        Args:
            vault_path (Path | str): Path to the vault directory

        Returns:
            Path: Full path to the ChromaDB data directory
        """

        vault_path = Path(vault_path)

        # Create a hash of vault path to uniquely identify it
        vault_hash = hashlib.md5(str(vault_path.resolve()).encode()).hexdigest()[:8]

        from pathlib import Path as PathlibPath

        project_root = PathlibPath(__file__).parent.parent.parent
        data_dir = project_root / cls.CHROMA_DATA_DIR / vault_hash
        data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir
