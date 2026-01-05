import re

from src.config.semantic_config import SemanticConfig


class ContentChunker:
    """Handles intelligent chunking of markdown notes."""

    def __init__(self, config_class=None):
        if config_class is None:
            config_class = SemanticConfig

        self.config = config_class()

    def chunk_content(
        self,
        content: str,
        note_name: str,
        metadata: dict | None = None,
    ) -> list[dict]:
        """
        Intelligently chunk note content.

        Strategy:
        1. If CHUNK_BY_HEADERS: Split by ## headers first.
        2. Then split by CHUNK_SIZE with CHUNK_OVERLAP.
        3. Preserve metadata for each chunk.

        Args:
            content (str): The full text content of the note.
            note_name (str): The name of the note.
            metadata (dict | None, optional): Additional metadata for the note.

        Returns:
            list[dict]: List of dicts with  'text', 'chunk_id', 'metadata'
        """
        if metadata is None:
            metadata = {}

        chunks = []

        # Step 1: Split by headers if enabled
        if self.config.CHUNK_BY_HEADERS:
            sections = self._split_by_headers(content)
        else:
            sections = [content]

        # Step 2: Further chunk by size
        for section_idx, section in enumerate(sections):
            text_chunks = self._chunk_by_size(section)

            for chunk_idx, text in enumerate(text_chunks):
                if not text.strip():
                    continue  # Skip empty chunks

                chunk_metadata = {
                    **metadata,
                    "note_name": note_name,
                    "chunk_idx": chunk_idx,
                    "section_idx": section_idx,
                    "chunk_size": len(text),
                }

                chunks.append(
                    {
                        "text": text,
                        "chunk_id": f"note_{note_name}_chunk_{chunk_idx}",
                        "metadata": chunk_metadata,
                    }
                )

        return (
            chunks
            if chunks
            else [
                {
                    "text": content,
                    "chunk_id": f"note_{note_name}_chunk_0",
                    "metadata": {**metadata, "note_name": note_name},
                }
            ]
        )

    def _split_by_headers(self, content: str) -> list[str]:
        """Split content by ## headers."""

        sections = re.split(r"\n(?=##\s+)", content)
        return [s for s in sections if s.strip()]

    def _chunk_by_size(self, text: str) -> list[str]:
        """Split text into chunks of CHUNK_SIZE with CHUNK_OVERLAP."""
        chunk_size = self.config.CHUNK_SIZE
        overlap = self.config.CHUNK_OVERLAP

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap

        return chunks
