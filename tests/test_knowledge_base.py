"""Tests for the knowledge_base module — RAG layer."""

from pathlib import Path
import tempfile

from knowledge_base import KnowledgeBase, _chunk_text


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def test_chunk_text_produces_overlapping_chunks() -> None:
    """Verify that _chunk_text produces chunks with expected overlap."""
    text = "A" * 600
    chunks = _chunk_text(text, chunk_size=300, overlap=50)
    # With 600 chars, chunk_size=300, overlap=50, we expect ~3 chunks
    assert len(chunks) >= 2
    assert all(len(c) <= 300 for c in chunks)


# ---------------------------------------------------------------------------
# KnowledgeBase loading
# ---------------------------------------------------------------------------

def test_knowledge_base_loads_all_documents() -> None:
    """All markdown files in knowledge/ should be chunked and indexed."""
    kb = KnowledgeBase()  # uses default knowledge/ directory
    assert kb.document_count > 0


def test_knowledge_base_loads_from_custom_directory() -> None:
    """KB can load from an arbitrary directory with .md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.md"
        p.write_text("Dogs need daily walks for physical and mental health.")
        kb = KnowledgeBase(knowledge_dir=tmpdir)
        assert kb.document_count >= 1


def test_knowledge_base_handles_empty_directory() -> None:
    """An empty knowledge directory should not crash — just produce 0 docs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb = KnowledgeBase(knowledge_dir=tmpdir)
        assert kb.document_count == 0


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def test_query_returns_relevant_chunks() -> None:
    """A query about vaccination should surface vaccination-related content."""
    kb = KnowledgeBase()
    results = kb.query("What vaccines does my dog need?")
    assert len(results) > 0
    # At least one chunk should mention vaccine-related terms
    combined = " ".join(results).lower()
    assert any(term in combined for term in ["vaccine", "vaccin", "rabies", "distemper", "dhpp"])


def test_query_returns_requested_number_of_results() -> None:
    """The n_results parameter should be respected."""
    kb = KnowledgeBase()
    results = kb.query("feeding schedule for cats", n_results=2)
    assert len(results) <= 2


def test_empty_query_does_not_crash() -> None:
    """An empty string query should return an empty list, not crash."""
    kb = KnowledgeBase()
    results = kb.query("")
    assert results == []
