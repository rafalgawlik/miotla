#!/bin/zsh
# Uruchom apkę Miotła (pasek menu).
# Przy pierwszym starcie tworzy wirtualne środowisko i instaluje zależności.
set -e
SCRIPT_DIR="${0:A:h}"
VENV="$SCRIPT_DIR/.venv"
PY="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
[[ -x "$PY" ]] || PY="$(command -v python3)"

if [[ ! -d "$VENV" ]]; then
  echo "Tworzę środowisko w $VENV …"
  "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip >/dev/null
  "$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

export PYTHONPATH="$SCRIPT_DIR"
exec "$VENV/bin/python" -m miotla_app
