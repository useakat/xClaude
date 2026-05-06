#!/usr/bin/env python3
"""
ファクトチェックスクリプト
stdin からテキストを受け取り、gpt-5.4-mini でファクトチェックして stdout に出力する。
環境変数 OPENAI_API_KEY が必要。
"""

import sys
import os
import json
import subprocess

SYSTEM_PROMPT = """あなたは科学・宇宙・物理分野の厳格なファクトチェッカーです。
与えられた文章の事実関係を検証し、以下の形式で日本語で報告してください。

## スコア: XX/100

（XX は事実精度の点数。断言できる事実誤りがなければ 95 以上とする）

## 問題あり  ← スコアが 95 未満の場合のみ記載
各問題点を以下の形式で列挙：
- **[箇所]**: 問題の説明 → 修正案

## 修正文案  ← スコアが 95 未満の場合のみ記載
（元の文体・構成・言い回しを最大限保持しつつ、事実誤りのみを必要最小限修正したテキスト）

## 問題なし  ← スコアが 95 以上の場合のみ記載
事実関係に問題はありません。

注意事項：
- 断言できる事実誤りのみ指摘する。不確実な場合は「要確認」と添える
- 科学的な数値・年号・固有名詞・発見者・理論名を重点的にチェックする
- 文体・表現・構成は一切変えない（事実のみ対象）
- 修正文案の変更箇所は最小限にする
"""


def main():
    text = sys.stdin.read().strip()
    if not text:
        print("エラー: 入力テキストがありません", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({
        "model": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    })

    result = subprocess.run(
        [
            "curl", "-s", "-f",
            "https://api.openai.com/v1/chat/completions",
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {api_key}",
            "-d", payload,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"エラー: OpenAI API 呼び出しに失敗しました: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
        if "error" in data:
            print(f"エラー: {data['error'].get('message', data['error'])}", file=sys.stderr)
            sys.exit(1)
        print(data["choices"][0]["message"]["content"])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"エラー: レスポンスのパースに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
