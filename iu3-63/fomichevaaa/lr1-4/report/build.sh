#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PATH="/Library/TeX/texbin:$PATH"
export PATH
export TEXINPUTS="$SCRIPT_DIR:$SCRIPT_DIR/bmstu//:"

cd "$SCRIPT_DIR"

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Не найдена команда '$1'. Установите LaTeX и повторите сборку." >&2
        exit 1
    fi
}

require_command pdflatex
require_command biber

pdflatex -interaction=nonstopmode -halt-on-error report.tex
biber report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
