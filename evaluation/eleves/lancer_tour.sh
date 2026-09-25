#!/usr/bin/env bash
# Lance un tour du banc pour Haiku et Sonnet en parallele (4 fils chacun) et attend la fin des deux.
# Usage : bash evaluation/eleves/lancer_tour.sh r1 [options banc.py supplementaires]
set -u
cd "$(dirname "$0")/../.."
RUN="$1"; shift
export PYTHONIOENCODING=utf-8
PY=${JULES_PY:-C:/BSTEG/venv_tests/Scripts/python.exe}
"$PY" evaluation/eleves/banc.py --jules haiku --run "$RUN" --fils 4 "$@" > "evaluation/eleves/${RUN}_haiku.log" 2>&1 &
P1=$!
"$PY" evaluation/eleves/banc.py --jules sonnet --run "$RUN" --fils 4 "$@" > "evaluation/eleves/${RUN}_sonnet.log" 2>&1 &
P2=$!
wait $P1 $P2
echo "== haiku"; tail -3 "evaluation/eleves/${RUN}_haiku.log"
echo "== sonnet"; tail -3 "evaluation/eleves/${RUN}_sonnet.log"
