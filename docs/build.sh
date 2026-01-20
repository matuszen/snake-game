#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR/_build"

if [ -f "$ROOT_DIR/.venv/bin/activate" ]; then
    source "$ROOT_DIR/.venv/bin/activate"
fi

pip install -q --upgrade -r "$ROOT_DIR/requirements.txt"

cd "$SCRIPT_DIR"
doxygen "$SCRIPT_DIR/Doxyfile"

sphinx-build -b html -d "$BUILD_DIR/doctrees" "$SCRIPT_DIR" "$BUILD_DIR/html"
sphinx-build -b latex -d "$BUILD_DIR/doctrees" "$SCRIPT_DIR" "$BUILD_DIR/latex"

sed -i.bak '/^\\renewcommand{\\indexname}{Python Module Index}/,/^\\end{sphinxtheindex}/d' "$BUILD_DIR/latex/SnakeGame.tex"
rm "$BUILD_DIR/latex/SnakeGame.tex.bak"

cd "$BUILD_DIR/latex"

PDFLATEX_LOG="$BUILD_DIR/latex/pdflatex.log"

if command -v pdflatex &> /dev/null; then
    if ! pdflatex -interaction=nonstopmode SnakeGame.tex >"$PDFLATEX_LOG" 2>&1; then
        echo "pdflatex failed on first pass; see $PDFLATEX_LOG for details." >&2
    fi
    if ! pdflatex -interaction=nonstopmode SnakeGame.tex >>"$PDFLATEX_LOG" 2>&1; then
        echo "pdflatex failed on second pass; see $PDFLATEX_LOG for details." >&2
    fi
fi

cd "$SCRIPT_DIR"

if [ -f "$BUILD_DIR/latex/SnakeGame.pdf" ]; then
    echo "Documentation built:"
    echo "  HTML: $BUILD_DIR/html/index.html"
    echo "  PDF:  $BUILD_DIR/latex/SnakeGame.pdf"
else
    echo "Warning: PDF generation failed"
    echo "  HTML: $BUILD_DIR/html/index.html"
fi
