#!/bin/sh
set -eu

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew не найден. Сначала установите Homebrew: https://brew.sh" >&2
    exit 1
fi

env HOMEBREW_NO_AUTO_UPDATE=1 brew install --cask mactex-no-gui
