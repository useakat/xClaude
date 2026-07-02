#!/usr/bin/env bash
ROOT="$(git rev-parse --show-toplevel)"
NOTEBOOK_ID="f686847f-2328-47d5-bc6e-b3c16ef4767a"
PROJ="$ROOT/projects/w002/2026-06-19_ボイジャー再点火"
IMG="$PROJ/draft/images"

gen_one() {  # 引数: 出力PNGパス, instructionsファイルパス
  local out="$1" instr="$2" try
  for try in 1 2 3; do
    python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
      --instructions "$(cat "$instr")" \
      --language ja --orientation landscape --detail standard --style auto \
      --output "$out" && [ -f "$out" ] && return 0
    echo "retry $try failed: $(basename "$out")"; sleep 5
  done
  echo "FAILED: $(basename "$out")"; return 1
}

for safe in "声が_届かなくなる" "眠っていた_もう一つのエンジン" "機体を守る仕組みが_最大の敵だった" "古さは_弱点ではなかった"; do
  instr="$IMG/${safe}_図解.md"
  echo "=== $safe ==="
  for n in 01 02 03; do
    gen_one "$IMG/${safe}_図解_${n}.png" "$instr"
  done
done
echo "=== DONE ==="
