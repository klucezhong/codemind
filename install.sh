#!/bin/bash
# CodeMind quick install script

set -e

echo "🔧 Installing CodeMind..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python version: $python_version"

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
if command -v python3 -m pip &> /dev/null; then
    python3 -m pip install --upgrade pip 2>/dev/null || true
    python3 -m pip install typer rich tree-sitter tree-sitter-languages rank-bm25 openai 2>/dev/null || \
        python3 -m pip install typer rich rank-bm25 2>/dev/null || \
        echo "⚠️  Some optional deps may be missing"
else
    echo "⚠️  pip not available — some features may be limited"
fi

# Install codemind in editable mode
echo "🔨 Installing CodeMind in editable mode..."
python3 -m pip install -e . 2>/dev/null || python3 -m pip install -e . || \
    echo "⚠️  Could not install in editable mode (pip may be unavailable)"

# Verify installation
echo "✅ Verifying installation..."
python3 -c "import sys; sys.path.insert(0, 'src'); from codemind import __version__; print(f'CodeMind v{__version__} installed!')"

echo ""
echo "🎉 CodeMind is ready!"
echo ""
echo "Usage:"
echo "  python3 -m codemind.index ./src   # Index your project"
echo "  python3 -m codemind.search \"login\" # Search code"
echo ""