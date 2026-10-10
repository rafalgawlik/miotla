#!/bin/bash
# Uruchamia wszystkie testy Miotły (tests/test_*.sh). Zwraca !=0, gdy coś padło.
set -u
cd "$(dirname "$0")" || exit 1

total_fail=0
for t in test_*.sh; do
    [ -f "$t" ] || continue
    echo "▶ $t"
    if bash "$t"; then :; else total_fail=$((total_fail + 1)); fi
    echo ""
done

if [ "$total_fail" -eq 0 ]; then
    echo "WSZYSTKIE TESTY PRZESZŁY"
else
    echo "PLIKÓW TESTOWYCH Z BŁĘDAMI: $total_fail"
fi
exit "$total_fail"
