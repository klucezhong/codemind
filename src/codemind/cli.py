"""
CodeMind CLI entry point.
"""
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from codemind.indexer import CodeIndexer
from codemind.search import CodeSearchEngine
from codemind.output import print_results, print_index_summary

console = Console()
app = typer.Typer(
    name="codemind",
    help="CodeMind — Semantic code search engine",
    add_completion=False,
)


@app.command()
def index(
    path: Annotated[str, typer.Argument(help="Path to index (file or directory)")],
    name: Annotated[str, typer.Option("--name", "-n", help="Project name")] = "default",
    verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
):
    """Index a codebase for semantic search."""
    target = Path(path).resolve()
    if not target.exists():
        console.print(f"[red]Error: Path not found: {path}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold blue]Indexing:[/bold blue] {target}")
    indexer = CodeIndexer(project_name=name)
    stats = indexer.index_directory(target)

    console.print(f"[green]✓ Indexed {stats['files']} files, {stats['chunks']} chunks[/green]")
    if verbose:
        print_index_summary(stats)


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    project: Annotated[str, typer.Option("--project", "-p")] = "default",
    limit: Annotated[int, typer.Option("--limit", "-n")] = 10,
    verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
):
    """Search indexed code with a semantic query."""
    engine = CodeSearchEngine(project_name=project)
    results = engine.search(query, limit=limit)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    print_results(results, verbose=verbose)
    console.print(f"\n[dim]Found {len(results)} result(s)[/dim]")


@app.command()
def ask(
    query: Annotated[str, typer.Argument(help="Question about your code")],
    project: Annotated[str, typer.Option("--project", "-p")] = "default",
    model: Annotated[str, typer.Option("--model", "-m")] = "gpt-4o",
):
    """Ask a natural language question about your code (requires API key)."""
    import os

    api_key = os.environ.get("CODEMIND_API_KEY")
    if not api_key:
        console.print("[red]Error: CODEMIND_API_KEY not set[/red]")
        console.print("  Set it with: export CODEMIND_API_KEY=your-key")
        raise typer.Exit(1)

    engine = CodeSearchEngine(project_name=project)
    results = engine.search(query, limit=5)

    if not results:
        console.print("[yellow]No relevant code found for your question.[/yellow]")
        return

    console.print(f"[bold blue]Searching for:[/bold blue] {query}")
    console.print(f"[dim]Found {len(results)} relevant chunks, preparing answer...[/dim]\n")

    context = "\n\n".join(
        f"[{r['file']}:{r['line_start']}]\n{r['text']}" for r in results
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful code assistant. Answer the question based ONLY "
                        "on the provided code context. Be concise and specific."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Code context:\n{context}\n\nQuestion: {query}",
                },
            ],
            temperature=0.3,
        )
        console.print(response.choices[0].message.content)
    except Exception as e:
        console.print(f"[red]Error calling LLM: {e}[/red]")
        console.print("\n[yellow]Falling back to raw search results:[/yellow]\n")
        print_results(results, verbose=True)


@app.command()
def version():
    """Show version."""
    from codemind import __version__
    console.print(f"CodeMind v{__version__}")


def main():
    app()


if __name__ == "__main__":
    main()
