"""Knowledge base module — loads pet-care markdown files, chunks them, and provides
RAG-style vector search via ChromaDB."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import chromadb

logger = logging.getLogger("pawpal_agent")

_DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

# Approximate chunk size in characters.  Keeping chunks short improves
# retrieval precision without losing too much surrounding context.
_CHUNK_SIZE = 300
_CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split *text* into overlapping chunks of roughly *chunk_size* characters."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


class KnowledgeBase:
    """Thin wrapper around a ChromaDB ephemeral collection loaded from
    the ``knowledge/`` folder.  Call :meth:`query` to retrieve the most
    relevant chunks for a user question."""

    def __init__(self, knowledge_dir: str | Path | None = None) -> None:
        self._knowledge_dir = Path(knowledge_dir) if knowledge_dir else _DEFAULT_KNOWLEDGE_DIR
        self._client = chromadb.EphemeralClient()
        # Use a unique collection name based on the directory to avoid cross-instance
        # contamination when multiple KnowledgeBase instances share the same process.
        collection_name = f"pawpal_kb_{hash(str(self._knowledge_dir)) % 10**8}"
        self._collection = self._client.get_or_create_collection(name=collection_name)
        self._load_documents()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_documents(self) -> None:
        """Read every ``.md`` file in the knowledge directory, chunk, and upsert."""
        if not self._knowledge_dir.is_dir():
            logger.warning("Knowledge directory %s does not exist — KB will be empty.", self._knowledge_dir)
            return

        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, str]] = []

        for md_file in sorted(self._knowledge_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            chunks = _chunk_text(text)
            for idx, chunk in enumerate(chunks):
                doc_id = f"{md_file.stem}_{idx}"
                documents.append(chunk)
                ids.append(doc_id)
                metadatas.append({"source": md_file.name})

        if not documents:
            logger.warning("No documents found in %s", self._knowledge_dir)
            return

        self._collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info("Knowledge base loaded: %d chunks from %s", len(documents), self._knowledge_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(self, text: str, n_results: int = 3) -> list[str]:
        """Return the top-*n_results* most relevant text chunks for *text*."""
        if not text or not text.strip():
            return []
        try:
            results = self._collection.query(query_texts=[text], n_results=n_results)
            return results["documents"][0] if results["documents"] else []
        except Exception:
            logger.exception("Knowledge base query failed for: %s", text)
            return []

    @property
    def document_count(self) -> int:
        """Number of chunks currently stored."""
        return self._collection.count()
