#!/bin/zsh
# Policz sha256 tarballa release'u z GitHuba i wpisz go do formuły.
#
# Użycie:
#   ./packaging/homebrew/release-sha.sh 0.1.0
#
# Wymaga: utworzonego wcześniej tagu/release'u v<wersja> w repo.
set -e
VERSION="${1:?Podaj wersję, np. 0.1.0}"
USER="rafalgawlik"
REPO="miotla"
FORMULA="${0:A:h}/miotla.rb"

URL="https://github.com/$USER/$REPO/archive/refs/tags/v$VERSION.tar.gz"
echo "Pobieram: $URL"
SHA=$(curl -fsSL "$URL" | shasum -a 256 | awk '{print $1}')
echo "sha256 = $SHA"

sed -i '' -E "s|^  sha256 \"[^\"]*\"|  sha256 \"$SHA\"|" "$FORMULA"
echo "Zaktualizowano $FORMULA"
