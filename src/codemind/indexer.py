"""
Code indexer using tree-sitter for AST parsing and BM25 for chunk indexing.
Stores everything in a local SQLite database.
"""
import re
import hashlib
from pathlib import Path
from typing import Optional
import sqlite3

try:
    import tree_sitter_languages
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".vue": "javascript",
    ".svelte": "javascript",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
}

MAX_FILE_SIZE = 100_000  # 100KB max per file
CHUNK_SIZE = 200        # lines per chunk


def get_db_path(project_name: str) -> Path:
    cache = Path.home() / ".cache" / "codemind"
    cache.mkdir(parents=True, exist_ok=True)
    return cache / f"{project_name}.db"


def split_into_chunks(content: str, max_lines: int = CHUNK_SIZE) -> list[str]:
    """Split file content into overlapping chunks."""
    lines = content.split("\n")
    chunks = []
    for i in range(0, len(lines), max_lines // 2):  # 50% overlap
        chunk = "\n".join(lines[i : i + max_lines])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def extract_text_from_tree_sitter(content: bytes, language: str) -> str:
    """Extract plain text from source using tree-sitter if available."""
    if not TREE_SITTER_AVAILABLE:
        return content.decode("utf-8", errors="replace")

    try:
        lang = tree_sitter_languages.get_language(language)
        parser = Parser(language=lang)
        tree = parser.parse(content)
        return _extract_docstrings(tree.root_node, language)
    except Exception:
        return content.decode("utf-8", errors="replace")


def _extract_docstrings(node, language: str, depth: int = 0) -> str:
    """Recursively extract function/class names + docstrings for semantic context."""
    if depth > 10:
        return ""

    texts = []

    def_node_types = ["function_definition", "class_definition", "method_definition"]
    if language == "python":
        def_node_types = ["function_definition", "class_definition"]
    elif language in ("javascript", "typescript"):
        def_node_types = ["function_declaration", "class_declaration", "method_definition"]

    if node.type in def_node_types:
        name = None
        docstring = None
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else ""
            elif child.type in ("string", "comment"):
                txt = child.text.decode() if hasattr(child, "text") else ""
                if name and not docstring and len(txt) > 10:
                    docstring = txt

        if name:
            parts = [f"function: {name}"]
            if docstring:
                parts.append(f"doc: {docstring}")
            texts.append(" | ".join(parts))

    for child in node.children:
        result = _extract_docstrings(child, language, depth + 1)
        if result:
            texts.append(result)

    return " ".join(texts)


class CodeIndexer:
    """Index a codebase and store chunks in SQLite + BM25."""

    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.db_path = get_db_path(project_name)
        self._init_db()
        self._init_parsers()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_file ON chunks(file)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_hash ON chunks(chunk_hash)
        """)
        conn.commit()
        conn.close()

    def _init_parsers(self):
        self.parsers: dict[str, Parser] = {}
        if not TREE_SITTER_AVAILABLE:
            return
        for ext, lang in {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
        }.items():
            try:
                language = tree_sitter_languages.get_language(lang)
                parser = Parser(language=language)
                self.parsers[lang] = parser
            except Exception:
                pass

    def _index_file(self, file_path: Path) -> list[dict]:
        try:
            size = file_path.stat().st_size
            if size > MAX_FILE_SIZE:
                return []
            content = file_path.read_bytes()
        except Exception:
            return []

        ext = file_path.suffix.lower()
        language = SUPPORTED_EXTENSIONS.get(ext, "plaintext")

        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            return []

        chunks = split_into_chunks(text)
        results = []
        for i, chunk in enumerate(chunks):
            chunk_hash = hashlib.md5(f"{file_path}:{i}:{chunk}".encode()).hexdigest()
            line_start = i * (CHUNK_SIZE // 2) + 1
            line_end = line_start + chunk.count("\n")

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO chunks (file, line_start, line_end, chunk_text, chunk_hash) VALUES (?, ?, ?, ?, ?)",
                (str(file_path), line_start, line_end, chunk, chunk_hash),
            )
            conn.commit()
            conn.close()

            results.append(
                {
                    "file": str(file_path),
                    "line_start": line_start,
                    "line_end": line_end,
                    "text": chunk,
                }
            )
        return results

    def index_directory(self, directory: Path) -> dict:
        """Recursively index all supported files in a directory."""
        all_files = []
        for ext in SUPPORTED_EXTENSIONS:
            all_files.extend(directory.rglob(f"*{ext}"))

        # Filter out common ignored dirs
        ignored = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", ".tox"}
        files = [f for f in all_files if not any(part in f.parts for part in ignored)]

        total_chunks = 0
        for f in files:
            chunks = self._index_file(f)
            total_chunks += len(chunks)

        return {"files": len(files), "chunks": total_chunks}

    def rebuild_fts(self):
        """Rebuild the BM25 FTS index from stored chunks.
        
        With in-memory BM25, this is a no-op since the index
        is rebuilt on-the-fly in search(). Kept for API compatibility.
        """
        pass
