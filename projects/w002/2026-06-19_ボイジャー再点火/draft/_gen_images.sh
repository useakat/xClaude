#!/usr/bin/env bash
set -u
ROOT=$(git rev-parse --show-toplevel)
NOTEBOOK_ID="f686847f-2328-47d5-bc6e-b3c16ef4767a"
PROJ="/root/xClaude/projects/w002/2026-06-19_ボイジャー再点火"
IMG="$PROJ/draft/images"
mkdir -p "$IMG"

DIAGRAM_SUFFIX="これは図解（インフォグラフィック）として作成してください。"
IMAGE_SUFFIX="図解ではなく、情景を描いたイメージ画像として作成してください。画像内には説明文・キャプション・ラベル・タイトルなどの文字を一切入れないでください。"

gen_one() {  # 引数: 出力PNGパス, instructionsファイルパス
  local out="$1" instr="$2" try
  for try in 1 2 3; do
    python3 "$ROOT/scripts/notebooklm_manager.py" infographic "$NOTEBOOK_ID" \
      --instructions "$(cat "$instr")" \
      --language ja --orientation landscape --detail standard --style auto \
      --output "$out" && [ -f "$out" ] && { echo "OK: $(basename "$out")"; return 0; }
    echo "retry $try failed: $(basename "$out")"; sleep 5
  done
  echo "FAILED: $(basename "$out")"; return 1
}

run_section() {  # 引数: safe, type(図解/イメージ), 説明本文
  local safe="$1" type="$2" desc="$3" suffix instr png n
  if [ "$type" = "図解" ]; then suffix="$DIAGRAM_SUFFIX"; else suffix="$IMAGE_SUFFIX"; fi
  for n in 01 02 03; do
    instr="$IMG/${safe}_${type}_${n}.md"
    png="$IMG/${safe}_${type}_${n}.png"
    printf '%s\n' "${desc}${suffix}" > "$instr"
    echo "=== generating ${safe}_${type}_${n} ==="
    gen_one "$png" "$instr"
  done
}

run_section "声が_届かなくなる" "図解" "地球と、200億kmかなたのボイジャーを結ぶ通信の構図。機体のアンテナが地球を向き、姿勢制御スラスタの小さな噴射で「向き」を保っていることを矢印で示す図解。"
run_section "眠っていた_もう一つのエンジン" "図解" "ボイジャーのスラスタ配置の図解。弱ってきた「姿勢制御スラスタ」と、37年眠っていた予備の「TCMスラスタ」の位置と役割を対比して示す。"
run_section "機体を守る仕組みが_最大の敵だった" "図解" "噴射命令の宛先を、姿勢制御スラスタからTCMスラスタへ振り向ける修正の図。安全のしきい値に触れずに通す「綱渡り」を、矢印と分岐で示す。"
run_section "古さは_弱点ではなかった" "図解" "「現代の複雑な機械（何層も重なるソフトウェア）」と「ボイジャーのむき出しの単純な仕組み」を左右で対比する図解。古いほうが、人の手を根っこまで直接入れられることを示す。"
run_section "片道19時間半の祈り" "イメージ" "ゴールドストーンの巨大アンテナが、深宇宙からの極限まで微弱な信号を受け取る瞬間の情景。夜明けの空と、緊張から安堵へ変わる雰囲気。"

echo "=== ALL DONE ==="
ls -1 "$IMG"/*.png 2>/dev/null | wc -l
