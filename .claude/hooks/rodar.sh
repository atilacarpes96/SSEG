#!/bin/sh
# Lança sseg_hooks.py com o Python de verdade e UTF-8 (ganchos do .claude/settings.json).
# No Windows, "python3" pode ser o atalho da Microsoft Store (WindowsApps): pula e testa se roda.
# Sem Python: o commit é barrado (exit 2, a trava fecha); os outros ganchos só avisam.
PY=
for c in python3 python py; do
  p=$(command -v "$c") || continue
  case "$p" in *WindowsApps*) continue ;; esac
  "$p" -c "" >/dev/null 2>&1 && { PY=$p; break; }
done
if [ -z "$PY" ]; then
  echo "SSEG: Python não encontrado; o gancho \"$1\" não rodou (instale pelo SSEG.exe)." >&2
  [ "$1" = "commit" ] && exit 2
  exit 1
fi
PYTHONUTF8=1
export PYTHONUTF8
exec "$PY" "$(dirname "$0")/sseg_hooks.py" "$@"
