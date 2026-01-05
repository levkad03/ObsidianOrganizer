from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_ollama.embeddings import OllamaEmbeddings

from src.config.semantic_config import SemanticConfig
from src.core.content_chunker import ContentChunker
from src.core.semantic_index import SemanticIndex


class SemanticService:
    """Main service for semantic indexing and search."""

    def __init__(
        self, vault_path: Path, embedding_model: str | None = None, config_class=None
    ):
        self.vault_path = vault_path

        if config_class is None:
            config_class = SemanticConfig

        self.config = config_class()

        self.embedding_model = embedding_model or self.config.EMBEDDING_MODEL

        self.embedder = self._create_embedder()
        self.semantic_index = SemanticIndex(vault_path, config_class=config_class)
        self.chunker = ContentChunker(config_class=config_class)

    def _create_embedder(self) -> Embeddings:
        """Create embedding model instance."""
        return OllamaEmbeddings(
            model=self.embedding_model,
            base_url=self.config.OLLAMA_BASE_URL,
        )

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embedder.embed_query(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        return self.embedder.embed_documents(texts)

    def _sanitize_metadata(self, metadata: dict) -> dict:
        """
        Ensure metadata values are compatible with ChromaDB (str, int, float, bool).
        """
        sanitized = {}
        for k, v in metadata.items():
            if isinstance(v, str | int | float | bool):
                sanitized[k] = v
            elif isinstance(v, list):
                # Convert lists to comma-separated strings
                sanitized[k] = ", ".join(str(item) for item in v)
            elif v is None:
                continue
            else:
                # Convert other types to string
                sanitized[k] = str(v)
        return sanitized

    def index_note(
        self, note_name: str, content: str, metadata: dict | None = None
    ) -> int:
        """Index a single note's content.

        Args:
            note_name (str): Name of the note
            content (str): Content of the note
            metadata (dict | None, optional): Additional metadata for the note.

        Returns:
            int: Number of chunks indexed
        """
        if metadata:
            metadata = self._sanitize_metadata(metadata)

        # Remove existing if already indexed
        if note_name in self.semantic_index.indexed_notes:
            self.semantic_index.delete_note(note_name)

        # Chunk the content
        chunks = self.chunker.chunk_content(content, note_name, metadata)

        # Embed chunks
        texts = [c["text"] for c in chunks]
        embeddings = self.embed_batch(texts)

        # Store in index
        self.semantic_index.add_documents(
            documents=texts,
            metadatas=[c["metadata"] for c in chunks],
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
        )

        return len(chunks)

    def index_vault(
        self,
        notes: list[tuple[str, str, dict]],
        progress_callback: callable[[int, int], None] | None = None,
    ) -> dict:
        """
        Index entire vault.

        Args:
            notes: List of (note_name, content, metadata) tuples
            progress_callback: Optional callback(current, total) for progress

        Returns:
            Dict with statistics
        """

        total_notes = len(notes)
        total_chunks = 0

        # Process in batches
        batch_size = self.config.BATCH_SIZE

        for batch_idx in range(0, total_notes, batch_size):
            batch = notes[batch_idx : batch_idx + batch_size]

            for note_name, content, metadata in batch:
                chunks = self.index_note(note_name, content, metadata)
                total_chunks += chunks

            if progress_callback:
                progress_callback(min(batch_idx + batch_size, total_notes), total_notes)

        return {
            "status": "indexed",
            "total_notes": total_notes,
            "total_chunks": total_chunks,
            "indexed_notes": list(self.semantic_index.indexed_notes),
        }

    def search_by_text(
        self,
        query: str,
        top_k: int | None = None,
        filter_tags: list[str] | None = None,
    ) -> dict:
        """Semantic search by text query.

        Args:
            query (str): Text query to search for
            top_k (int | None): Number of top results to return.
            filter_tags (list[str] | None): Tags to filter results by.

        Returns:
            dict: Search results with metadata and similarity scores
        """
        final_k = top_k or self.config.TOP_K_RESULTS

        # If filtering by tags, we fetch more candidates first (post-filtering)
        # because ChromaDB stores tags as a single string "tag1, tag2"
        fetch_k = final_k * 4 if filter_tags else final_k

        results = self.semantic_index.search_by_text(
            query, embedder=self.embed_text, top_k=fetch_k, where_filter=None
        )

        if not filter_tags:
            return results

        # Post-filter results in Python
        # Chroma results are column-oriented: {'ids': [[]], 'metadatas': [[]], ...}
        # We assume single query, so we look at index 0

        if not results["ids"] or not results["ids"][0]:
            return results

        filtered_indices = []

        # Iterate through the first query's results
        for idx, metadata in enumerate(results["metadatas"][0]):
            if not metadata or "tags" not in metadata:
                continue

            # Tags are stored as "tag1, tag2, tag3"
            stored_tags_str = str(metadata["tags"])
            stored_tags = [t.strip() for t in stored_tags_str.split(",")]

            # Check if ANY of the filter tags are present
            if any(tag in stored_tags for tag in filter_tags):
                filtered_indices.append(idx)

            if len(filtered_indices) >= final_k:
                break

        # Reconstruct the results dictionary with only filtered items
        new_results = {
            "ids": [[results["ids"][0][i] for i in filtered_indices]],
            "distances": [[results["distances"][0][i] for i in filtered_indices]]
            if results.get("distances")
            else None,
            "metadatas": [[results["metadatas"][0][i] for i in filtered_indices]],
            "documents": [[results["documents"][0][i] for i in filtered_indices]]
            if results.get("documents")
            else None,
            "embeddings": [[results["embeddings"][0][i] for i in filtered_indices]]
            if results.get("embeddings")
            else None,
        }

        if "similarities" in results:
            new_results["similarities"] = [
                [results["similarities"][0][i] for i in filtered_indices]
            ]

        return new_results

    def find_similar_notes(
        self,
        note_name: str,
        top_k: int | None = None,
        include_self: bool = False,
    ) -> dict:
        """Find notes similar to a given note by name.

        Args:
            note_name (str): Name of the note to find similarities for
            top_k (int | None): Number of top similar notes to return.
            include_self (bool): Whether to include the note itself in the results.

        Returns:
            dict: Search results with metadata and similarity scores
        """
        # Try to get existing embeddings for the note
        embeddings = self.semantic_index.get_note_embeddings(note_name)

        if not embeddings:
            # Fallback to name if not indexed (poor results expected)
            query_embedding = self.embed_text(note_name)
        else:
            # Average the embeddings
            # embeddings is list[list[float]]
            dim = len(embeddings[0])
            num_chunks = len(embeddings)
            avg_embedding = [0.0] * dim
            for emb in embeddings:
                for i in range(dim):
                    avg_embedding[i] += emb[i]

            query_embedding = [x / num_chunks for x in avg_embedding]

        # Apply where filter to exclude self
        where_filter = None
        if not include_self:
            where_filter = {"note_name": {"$ne": note_name}}

        return self.semantic_index.search(
            query_embedding, top_k=top_k, where_filter=where_filter
        )

    def get_index_stats(self) -> dict:
        """Get indexing statistics."""
        return self.semantic_index.get_stats()

    def clear_index(self) -> None:
        """Clear all embeddings."""
        self.semantic_index.clear()
