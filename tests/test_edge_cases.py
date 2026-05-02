"""
Edge case tests for CodeMind CLI.
"""
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, "src")

from codemind.indexer import CodeIndexer
from codemind.search import CodeSearchEngine


def test_index_empty_directory():
    """Test indexing an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        indexer = CodeIndexer(project_name="test_empty_dir")
        stats = indexer.index_directory(Path(tmpdir))
        assert stats["files"] == 0
        assert stats["chunks"] == 0
        print("✓ Empty directory OK")


def test_index_nonexistent_directory():
    """Test indexing a nonexistent directory."""
    indexer = CodeIndexer(project_name="test_nonexistent_dir")
    stats = indexer.index_directory(Path("/nonexistent/dir"))
    assert stats["files"] == 0
    assert stats["chunks"] == 0
    print("✓ Nonexistent directory OK")


def test_search_with_special_chars():
    """Test search with special characters."""
    engine = CodeSearchEngine(project_name="test_special")
    results = engine.search("def @#$%^&*()", limit=5)
    assert isinstance(results, list)
    print("✓ Special char search OK")


def test_search_empty_query():
    """Test search with empty query."""
    engine = CodeSearchEngine(project_name="test_empty_query")
    results = engine.search("", limit=5)
    assert isinstance(results, list)
    print("✓ Empty query search OK")


def test_search_unicode():
    """Test search with unicode content."""
    engine = CodeSearchEngine(project_name="test_unicode")
    results = engine.search("中文测试", limit=5)
    assert isinstance(results, list)
    print("✓ Unicode search OK")


def test_large_limit():
    """Test search with very large limit."""
    engine = CodeSearchEngine(project_name="test_large_limit")
    results = engine.search("def", limit=10000)
    assert isinstance(results, list)
    print("✓ Large limit search OK")


if __name__ == "__main__":
    print("=" * 50)
    print("CodeMind Edge Case Tests")
    print("=" * 50)
    test_index_empty_directory()
    test_index_nonexistent_directory()
    test_search_with_special_chars()
    test_search_empty_query()
    test_search_unicode()
    test_large_limit()
    print("=" * 50)
    print("All edge case tests passed!")
