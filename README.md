# CodeMind

> Your local code semantic search engine. Find code by meaning, not just keywords.

[![PyPI Version](https://img.shields.io/pypi/v/codemind)](https://pypi.org/project/codemind/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**CodeMind** is a fast, local-first semantic search engine for codebases.  
Stop grep-ing blindly. Ask questions about your code.

---

## Features

- 🔍 **Semantic search** — Find code by describing what it does, not just variable names
- 📂 **Multi-language support** — Python, JavaScript, TypeScript, Go, Rust, and more
- 💨 **Lightning fast** — SQLite-backed BM25 index, instant results
- 🔒 **100% local** — Your code never leaves your machine
- 🤖 **AI-ready** — Hook in any LLM API for natural-language code Q&A

---

## Quick Start

### Installation

```bash
pip install codemind
```

### Index your project

```bash
cd your-project
codemind index ./src
```

### Search

```bash
codemind search "user authentication logic"
```

### Ask a question (with AI)

```bash
CODEMIND_API_KEY=your-key codemind ask "What does the login flow look like?"
```

---

## Why CodeMind?

| | Grep/IDE | CodeMind |
|---|---|---|
| Search by keyword | ✅ | ✅ |
| Search by meaning | ❌ | ✅ |
| Understand code context | ❌ | ✅ |
| Works offline | ✅ | ✅ |
| Privacy-friendly | ✅ | ✅ |

---

## Roadmap

- [ ] v0.1 — Core CLI + BM25 search
- [ ] v0.2 — Tree-sitter AST indexing for better accuracy
- [ ] v0.3 — Web dashboard (local)
- [ ] v1.0 — Pro tier: multi-project, team sync, AI Q&A

---

## License

MIT © 2026
