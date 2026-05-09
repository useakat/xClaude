#!/usr/bin/env python3
"""
説明の完全性チェックスクリプト
stdin からテキストを受け取り、gpt-5.4-mini で完全性をチェックして stdout に出力する。
環境変数 OPENAI_API_KEY が必要。
"""

import sys
import os
import json
import subprocess

SYSTEM_PROMPT = """あなたは科学・宇宙・物理分野の背景知識を持つ専門家です。
与えられた文章について、説明の完全性をチェックしてください：

1. テーマの科学的説明として、必須の概念や要素が過不足なく含まれているか
2. 読者が完全に理解するために不足している重要な説明がないか
3. 特に、科学的に正確でありながら一般に知られていない概念が抜けていないか

背景知識とウェブの最新情報を活用してチェックしてください。

以下の形式で日本語で報告してください。

## スコア: XX/100

（XX は説明の完全性評価。必須要素がすべて含まれていれば 95 以上とする）

## 不足要素あり  ← スコアが 95 未満の場合のみ記載
各不足要素を以下の形式で列挙：
- **[要素名]**: なぜ必要か（科学的背景）

## 追加文案  ← スコアが 95 未満の場合のみ記載
（元の文体・構成を最大限保持しつつ、不足要素を統合したテキスト）

## 完全です  ← スコアが 95 以上の場合のみ記載
説明は完全です。

注意事項：
- 説明の不足を重点的にチェックする。文体や表現は対象外
- 追加文案では、既存の文体・構成・言い回しを最大限保持する
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
