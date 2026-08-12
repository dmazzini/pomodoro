#!/usr/bin/env bash
#
# Puerta de tests determinista, invocada por orq-lite (`test_argv`) y por
# cualquier persona desde la raíz del repositorio.
#
# Dos suites:
#   1. pytest  — invariantes del envoltorio de escritorio y de las fronteras
#                arquitectónicas (leen ficheros como texto).
#   2. node --test — la convención fijada por el issue #11 para la lógica de
#                dominio: runner de Node, sin dependencias, sin build.
#
# No usa `set -e` para poder ejecutar ambas y reportar los dos resultados en
# una sola pasada.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1

status=0

echo "── pytest (invariantes del envoltorio y fronteras) ──"
if uv run pytest -q; then
  echo "pytest: OK"
else
  echo "pytest: FALLÓ"
  status=1
fi

echo
echo "── node --test (lógica de dominio) ──"
# `node --test` sobre un directorio sin ficheros de test sale con 0: un verde
# falso. Se cuenta primero para no confundir "no hay tests" con "los tests
# pasan".
node_tests=$(find tests -name '*.test.js' -type f 2>/dev/null | wc -l)

if [ "$node_tests" -eq 0 ]; then
  echo "node --test: SUITE VACÍA (0 ficheros *.test.js) — sin cobertura de dominio."
  echo "             La trae la extracción del módulo Historial (issue #11)."
  echo "             Esto NO es un verde: la puerta se apoya hoy sólo en pytest."
else
  if node --test tests/; then
    echo "node --test: OK ($node_tests fichero(s))"
  else
    echo "node --test: FALLÓ"
    status=1
  fi
fi

echo
if [ "$status" -eq 0 ]; then
  echo "puerta de tests: VERDE"
else
  echo "puerta de tests: ROJA"
fi
exit "$status"
