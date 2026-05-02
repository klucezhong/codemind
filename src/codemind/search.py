"""
BM25-backed semantic search engine for indexed code chunks.
"""
import sqlite3
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from codemind.indexer import get_db_path


class CodeSearchEngine:
    """Search indexed code using BM25 ranking."""

    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.db_path = get_db_path(project_name)
        self._ensure_fresh_fts()

    def _ensure_fresh_fts(self):
        """Rebuild FTS index if needed."""
        if not self.db_path.exists():
            return
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM chunks")
            count = c.fetchone()[0]
            conn.close()
            if count > 0:
                self.rebuild_fts()
        except Exception:
            pass

    def rebuild_fts(self):
        """Rebuild the BM25 FTS index from stored chunks."""
        # For BM25 in-memory search, we just need to ensure
        # the DB is ready; the actual FTS is built on-the-fly in search()
        pass

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search code chunks using BM25.
        Returns list of dicts with file, line_start, line_end, text, score.
        """
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get all chunks
        c.execute("SELECT id, file, line_start, line_end, chunk_text FROM chunks")
        rows = c.fetchall()
        conn.close()

        if not rows:
            return []

        if not BM25_AVAILABLE:
            # Fallback: simple substring match
            results = []
            for row in rows:
                chunk_id, file, line_start, line_end, chunk_text = row
                if query.lower() in chunk_text.lower():
                    results.append(
                        {
                            "file": file,
                            "line_start": line_start,
                            "line_end": line_end,
                            "text": chunk_text,
                            "score": 1.0,
                        }
                    )
            results.sort(key=lambda r: len(r["text"]))
            return results[:limit]

        # Tokenize chunks for BM25
        tokenized_corpus = [self._tokenize(chunk_text) for _, _, _, _, chunk_text in rows]
        bm25 = BM25Okapi(tokenized_corpus)

        query_tokens = self._tokenize(query)
        scores = bm25.get_scores(query_tokens)

        # Sort by score, return top N
        scored = sorted(zip(rows, scores), key=lambda x: x[1], reverse=True)

        results = []
        for (chunk_id, file, line_start, line_end, chunk_text), score in scored[:limit]:
            results.append(
                {
                    "file": file,
                    "line_start": line_start,
                    "line_end": line_end,
                    "text": chunk_text,
                    "score": round(float(score), 4),
                }
            )
        return results

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenizer: lowercase, split on non-alphanumeric."""
        import re
        tokens = re.split(r"[^a-zA-Z0-9_]+", text.lower())
        return [t for t in tokens if len(t) > 1]
