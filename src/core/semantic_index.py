from pathlib import Path

import chromadb
from chromadb.config import Settings

from src.config.semantic_config import SemanticConfig


class SemanticIndex:
    """Manages the Chroma vector DB for semantic search."""

    def __init__(self, vault_path: Path, config_class=None):
        self.vault_path = vault_path

        if config_class is None:
            config_class = SemanticConfig

        self.config = config_class()
        self.chroma_path = self.config.get_chroma_path(vault_path)
        self.chroma_path.mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self.collection = self.client.get_or_create_collection(
            name=self.config.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self._indexed_notes: set[str] | None = None

    @property
    def indexed_notes(self) -> set[str]:
        """Get set of all note names that are indexed."""
        if self._indexed_notes is None:
            # Load from Chroma metadata
            try:
                metadata = self.collection.get(include=[])
                self._indexed_notes = {
                    doc_id.replace("note_", "") for doc_id in metadata["ids"]
                }
            except Exception:
                self._indexed_notes = set()

        return self._indexed_notes

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Add documents to the Chroma collection.

        Args:
            documents (list[str]): List of document texts to add.
            metadatas (list[dict]): List of metadata dictionaries for each document.
            ids (list[str]): List of unique identifiers for each document.
            embeddings (list[list[float]]): List of embeddings corresponding
            to each document.
        """

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )

        # Update cached indexed notes
        for doc_id in ids:
            note_name = doc_id.split("_chunk_")[0].replace("note_", "")
            self.indexed_notes.add(note_name)

    def upsert_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Update or insert documents (for re-indexing)."""
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )

        for doc_id in ids:
            note_name = doc_id.split("_chunk_")[0].replace("note_", "")
            self.indexed_notes.add(note_name)

    def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        where_filter: dict | None = None,
    ) -> dict:
        """Perform a similarity search in the Chroma collection.

        Args:
            query_embedding (list[float]): The embedding vector for the query.
            top_k (int | None): The number of top results to return.
            where_filter (dict | None): Optional filter criteria for the search.

        Returns:
            dict: The search results from the Chroma collection.
        """

        if top_k is None:
            top_k = self.config.TOP_K_RESULTS

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances", "embeddings"],
        )

        # Convert distances to similarity scores
        if results["distances"] and len(results["distances"]) > 0:
            similarities = [
                [1 - (d / 2) for d in dists] for dists in results["distances"]
            ]

            results["similarities"] = similarities

        return results

    def search_by_text(
        self,
        query_text: str,
        embedder,
        top_k: int | None = None,
        where_filter: dict | None = None,
    ) -> dict:
        """Search by text (embeds query first).

        Args:
            query_text (str): Text query.
            embedder: Function that makes embeddings from text.
            top_k (int | None): The number of top results to return.
            where_filter (dict | None): Optional filter criteria for the search.

        Returns:
            dict: The search results from the Chroma collection.
        """

        embedding = embedder(query_text)
        return self.search(embedding, top_k=top_k, where_filter=where_filter)

    def delete_note(self, note_name: str) -> None:
        """Delete all chunks for a note from the index."""

        self.collection.delete(where={"note_name": note_name})
        self.indexed_notes.discard(note_name)

    def clear(self) -> None:
        """Clear all documents from the collection."""

        self.client.delete_collection(self.config.CHROMA_COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.config.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self._indexed_notes = set()

    def get_stats(self) -> dict:
        """Get indexing statistics."""

        return {
            "total_chunks": self.collection.count(),
            "indexed_notes": len(self.indexed_notes),
            "notes": sorted(list(self.indexed_notes)),
        }

    def get_note_embeddings(self, note_name: str) -> list[list[float]]:
        """Get all embeddings for a specific note."""
        results = self.collection.get(
            where={"note_name": note_name}, include=["embeddings"]
        )
        return results["embeddings"] if results and results["embeddings"] else []
