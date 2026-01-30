import json
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_community.document_loaders import ObsidianLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.semantic_config import SemanticConfig


class SemanticService:
    """Semantic search service using LangChain for Obsidian vaults."""

    def __init__(self, vault_path: Path, config_class: type | None = None) -> None:
        """Initialize the semantic service.

        Args:
            vault_path: Path to the Obsidian vault
            config_class: Optional configuration class (defaults to SemanticConfig)
        """
        self.vault_path = vault_path
        self.config = config_class() if config_class else SemanticConfig()

        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=self.config.EMBEDDING_MODEL, base_url=self.config.OLLAMA_BASE_URL
        )

        # Initialize vector store
        self.vector_store = Chroma(
            collection_name=self.config.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(self.config.get_chroma_path(vault_path)),
        )

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""],
        )

    def _sanitize_metadata(
        self, metadata: dict[str, Any]
    ) -> dict[str, str | int | float | bool]:
        """
        Sanitize metadata to be compatible with ChromaDB.
        ChromaDB only accepts: str, int, float, bool

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Sanitized metadata dictionary with only valid types
        """
        sanitized = {}

        for key, value in metadata.items():
            # Skip None values or empty keys
            if value is None or not str(key).strip():
                continue

            clean_key = str(key).strip()

            # Handle each type explicitly
            if isinstance(value, bool):
                sanitized[clean_key] = value
            elif isinstance(value, int) and not isinstance(value, bool):
                sanitized[clean_key] = value
            elif isinstance(value, float):
                # Skip NaN and Inf values
                if value == value and abs(value) != float("inf"):
                    sanitized[clean_key] = value
            elif isinstance(value, str):
                # Only add non-empty strings
                if value.strip():
                    sanitized[clean_key] = value.strip()
            # Convert lists to comma-separated strings
            elif isinstance(value, list):
                if value:
                    try:
                        # Filter out None values
                        filtered = [str(v) for v in value if v is not None]
                        if filtered:
                            sanitized[clean_key] = ", ".join(filtered)
                    except Exception:
                        pass
            # Convert dicts to JSON strings
            elif isinstance(value, dict):
                if value:
                    try:
                        sanitized[clean_key] = json.dumps(value, ensure_ascii=False)
                    except Exception:
                        pass
            # Convert other types (Path, datetime, etc.) to string
            else:
                try:
                    str_val = str(value).strip()
                    if str_val:
                        sanitized[clean_key] = str_val
                except Exception:
                    pass

        return sanitized

    def _sanitize_documents(self, documents: list[Document]) -> list[Document]:
        """
        Sanitize all metadata in a list of documents.

        Args:
            documents: List of documents with potentially invalid metadata

        Returns:
            List of documents with sanitized metadata
        """
        sanitized_docs = []

        for doc in documents:
            sanitized_metadata = self._sanitize_metadata(doc.metadata)
            sanitized_doc = Document(
                page_content=doc.page_content, metadata=sanitized_metadata
            )
            sanitized_docs.append(sanitized_doc)

        return sanitized_docs

    def index_vault(self) -> dict[str, Any]:
        """Index entire vault using ObsidianLoader.

        Returns:
            Dictionary with indexing statistics
        """
        loader = ObsidianLoader(str(self.vault_path))
        documents = loader.load()

        # Split documents
        splits = self.text_splitter.split_documents(documents)

        # Sanitize metadata before adding to vector store
        sanitized_splits = self._sanitize_documents(splits)

        # Add to vector store
        self.vector_store.add_documents(sanitized_splits)

        return {
            "status": "indexed",
            "total_documents": len(documents),
            "total_chunks": len(sanitized_splits),
        }

    def index_note(self, note_path: Path) -> int:
        """Index or re-index a single note.

        Args:
            note_path: Path to the note file

        Returns:
            Number of chunks created from the note
        """
        loader = ObsidianLoader(str(self.vault_path), collect_metadata=True)
        documents = loader.load()

        # Filter to specific note
        note_docs = [d for d in documents if Path(d.metadata["source"]) == note_path]

        if not note_docs:
            return 0

        # Delete existing chunks for this note
        self.vector_store.delete(filter={"source": str(note_path)})

        # Split and add
        splits = self.text_splitter.split_documents(note_docs)
        sanitized_splits = self._sanitize_documents(splits)

        self.vector_store.add_documents(sanitized_splits)

        return len(sanitized_splits)

    def search_by_text(
        self,
        query: str,
        top_k: int | None = None,
        filter_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Perform semantic search by text query.

        Args:
            query: Text query to search for
            top_k: Number of top results to return (defaults to config value)
            filter_tags: Optional list of tags to filter results

        Returns:
            Dictionary with search results containing documents, scores, and metadata
        """
        k = top_k or self.config.TOP_K_RESULTS

        if filter_tags:
            # Fetch more results for post-filtering
            results = self.vector_store.similarity_search_with_score(query, k=k * 3)

            # Post-filter by tags (tags are stored as comma-separated strings)
            filtered_results = []
            for doc, score in results:
                doc_tags_str = doc.metadata.get("tags", "")
                if doc_tags_str:
                    doc_tags = [t.strip() for t in str(doc_tags_str).split(",")]
                    if any(tag in doc_tags for tag in filter_tags):
                        filtered_results.append((doc, score))
                        if len(filtered_results) >= k:
                            break

            results = filtered_results
        else:
            results = self.vector_store.similarity_search_with_score(query, k=k)

        return self._format_results(results)

    def find_similar_notes(
        self, note_name: str, top_k: int | None = None
    ) -> dict[str, Any]:
        """Find notes similar to a given note.

        Args:
            note_name: Name of the note to find similarities for
            top_k: Number of similar notes to return (defaults to config value)

        Returns:
            Dictionary with similar notes and their similarity scores
        """
        k = top_k or self.config.TOP_K_RESULTS

        # Get a sample chunk from the note to use as query
        results = self.vector_store.similarity_search(
            note_name, k=1, filter={"source": {"$regex": f".*{note_name}.*"}}
        )

        if not results:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]]}

        # Use the chunk's embedding to find similar
        similar = self.vector_store.similarity_search_with_score(
            results[0].page_content,
            k=k,
            filter={"source": {"$ne": results[0].metadata["source"]}},
        )

        return self._format_results(similar)

    def _format_results(self, results: list[tuple[Document, float]]) -> dict[str, Any]:
        """Format search results into a structured dictionary.

        Args:
            results: List of tuples containing (Document, similarity_score)

        Returns:
            Dictionary with formatted results in ChromaDB-like format
        """
        if not results:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "similarities": [[]],
            }

        documents = []
        metadatas = []
        distances = []
        similarities = []
        ids = []

        for doc, score in results:
            documents.append(doc.page_content)
            metadatas.append(doc.metadata)
            distances.append(score)

            # Convert distance to similarity score
            # Cosine distance range is [0, 2], so similarity = 1 - (distance / 2)
            similarity = 1 - (score / 2)
            similarities.append(similarity)

            # Generate consistent ID from source
            source = doc.metadata.get("source", "unknown")
            chunk_id = f"{Path(source).stem}_{hash(doc.page_content) % 10000}"
            ids.append(chunk_id)

        # Return in ChromaDB-compatible format
        return {
            "ids": [ids],
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
            "similarities": [similarities],
        }

    def get_stats(self) -> dict[str, Any]:
        """Get indexing statistics.

        Returns:
            Dictionary with statistics about indexed documents
        """
        collection = self.vector_store._collection
        count = collection.count()

        # Get unique sources (notes)
        all_docs = collection.get(include=["metadatas"])
        unique_sources = set()
        if all_docs and all_docs.get("metadatas"):
            unique_sources = {
                meta.get("source", "") for meta in all_docs["metadatas"] if meta
            }

        return {
            "total_chunks": count,
            "indexed_notes": len(unique_sources),
            "notes": sorted([Path(s).stem for s in unique_sources if s]),
        }

    def clear_index(self) -> None:
        """Clear all documents from the vector store."""
        collection_name = self.config.CHROMA_COLLECTION_NAME
        self.vector_store._client.delete_collection(collection_name)

        # Reinitialize the vector store
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.config.get_chroma_path(self.vault_path)),
        )
