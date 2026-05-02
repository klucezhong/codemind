"""
Rich-powered output formatting for search results.
"""
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel

console = Console()


def print_results(results: list[dict], verbose: bool = False):
    """Print search results with syntax highlighting."""
    for i, result in enumerate(results, 1):
        file_path = result["file"]
        line_start = result["line_start"]
        line_end = result["line_end"]
        text = result["text"]
        score = result.get("score", 0)

        ext = file_path.split(".")[-1] if "." in file_path else "txt"
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "javascript",
            "tsx": "typescript",
            "go": "go",
            "rs": "rust",
            "rb": "ruby",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "cs": "csharp",
            "swift": "swift",
            "kt": "kotlin",
            "sh": "bash",
            "yaml": "yaml",
            "yml": "yaml",
            "toml": "toml",
            "json": "json",
        }
        lexer = lang_map.get(ext, "text")

        header = f"  [{i}] {file_path} :{line_start}–{line_end}"
        if verbose:
            header += f"  [dim score: {score}][/dim]"

        console.print(f"\n[bold cyan]{header}[/bold cyan]")

        # Show first 30 lines of the chunk
        lines = text.split("\n")
        preview = "\n".join(lines[:30])
        if len(lines) > 30:
            preview += f"\n... [+{len(lines)-30} more lines]"

        try:
            syntax = Syntax(preview, lexer, theme="monokai", line_numbers=True)
            console.print(syntax)
        except Exception:
            console.print(Panel(preview, title=file_path))


def print_index_summary(stats: dict):
    """Print indexing statistics."""
    table = Table(title="Indexing Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in stats.items():
        table.add_row(key, str(value))

    console.print(table)
