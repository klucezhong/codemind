"""
Tests for CodeMind CLI.
"""
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, "src")

from codemind.indexer import CodeIndexer
from codemind.search import CodeSearchEngine


def test_indexer_basic():
    """Test that indexer can be created and initialized."""
    indexer = CodeIndexer(project_name="test_basic")
    assert indexer.project_name == "test_basic"
    assert indexer.db_path.name == "test_basic.db"
    print("✓ Indexer creation OK")


def test_index_directory():
    """Test indexing a real directory."""
    src_path = Path("src/codemind")
    indexer = CodeIndexer(project_name="test_index")
    stats = indexer.index_directory(src_path)
    assert stats["files"] > 0
    assert stats["chunks"] > 0
    print(f"✓ Indexed {stats['files']} files, {stats['chunks']} chunks OK")
    return stats


def test_search():
    """Test search returns results."""
    # First index something
    src_path = Path("src/codemind")
    indexer = CodeIndexer(project_name="test_search")
    indexer.index_directory(src_path)

    engine = CodeSearchEngine(project_name="test_search")
    results = engine.search("search", limit=5)
    print(f"✓ Search returned {len(results)} results")
    for r in results:
        assert "file" in r
        assert "text" in r
        assert "score" in r


def test_search_no_results():
    """Test search on empty index."""
    engine = CodeSearchEngine(project_name="test_empty")
    results = engine.search("xyzxyz_no_match", limit=5)
    assert isinstance(results, list)
    print("✓ Empty search OK")


def test_rebuild_fts():
    """Test rebuild_fts method exists and runs."""
    indexer = CodeIndexer(project_name="test_fts")
    indexer.rebuild_fts()  # Should not raise
    print("✓ rebuild_fts OK")


if __name__ == "__main__":
    print("=" * 50)
    print("CodeMind Tests")
    print("=" * 50)
    test_indexer_basic()
    test_rebuild_fts()
    test_search_no_results()
    test_index_directory()
    test_search()
    print("=" * 50)
    print("All tests passed!")