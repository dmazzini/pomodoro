#!/usr/bin/env bash
#
# Puerta de tests determinista, invocada por orq-lite (`test_argv`) y por
# cualquier persona desde la raíz del repositorio.
#
# Corre las dos suites y falla si cualquiera falla. No usa `set -e` para poder
# ejecutar ambas y reportar los dos resultados en una sola pasada.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1

status=0

echo "── pytest (invariantes del envoltorio de escritorio) ──"
if uv run pytest -q; then
  echo "pytest: OK"
else
  echo "pytest: FALLÓ"
  status=1
fi

echo
echo "── playwright (comportamiento de index.html) ──"
if npx --no-install playwright test; then
  echo "playwright: OK"
else
  echo "playwright: FALLÓ"
  status=1
fi

echo
if [ "$status" -eq 0 ]; then
  echo "puerta de tests: VERDE"
else
  echo "puerta de tests: ROJA"
fi
exit "$status"
