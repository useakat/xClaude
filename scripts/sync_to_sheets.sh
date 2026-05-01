#!/bin/bash
# database/ CSV → Google Sheets への一方向同期（gws CLI使用）
# 各シートをクリアしてCSVの内容で上書き

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_DIR="$REPO_ROOT/database"

sync_sheet() {
  local SS_ID="$1"
  local CSV_FILE="$2"
  local SHEET_NAME="$3"
  local CSV_PATH="$DB_DIR/$CSV_FILE"

  if [ ! -f "$CSV_PATH" ]; then
    echo "スキップ: $CSV_FILE が見つかりません"
    return
  fi

  local JSON_VALUES
  JSON_VALUES=$(python3 -c "
import csv, json, sys
with open('$CSV_PATH', newline='', encoding='utf-8') as f:
    rows = list(csv.reader(f))
print(json.dumps(rows))
")

  gws sheets spreadsheets values clear \
    --params "{\"spreadsheetId\": \"$SS_ID\", \"range\": \"$SHEET_NAME\"}" \
    --json '{}' 2>/dev/null > /dev/null

  gws sheets spreadsheets values update \
    --params "{\"spreadsheetId\": \"$SS_ID\", \"range\": \"$SHEET_NAME\", \"valueInputOption\": \"RAW\"}" \
    --json "{\"values\": $JSON_VALUES}" 2>/dev/null > /dev/null

  local ROW_COUNT
  ROW_COUNT=$(python3 -c "import json,sys; rows=json.loads('''$JSON_VALUES'''); print(len(rows)-1)" 2>/dev/null || echo "?")
  echo "  ✓ $SHEET_NAME: ${ROW_COUNT}件 同期完了"
}

SS1="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM"
echo "スプレッドシート①"
sync_sheet "$SS1" "onePointNeta.csv" "onePointNeta"
sync_sheet "$SS1" "noteNeta.csv" "noteNeta"
sync_sheet "$SS1" "newsTopics.csv" "newsTopics"

SS2="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc"
echo "スプレッドシート②"
sync_sheet "$SS2" "persona.csv" "persona"
sync_sheet "$SS2" "pain.csv" "pain"
sync_sheet "$SS2" "what.csv" "what"

echo ""
echo "同期完了"
