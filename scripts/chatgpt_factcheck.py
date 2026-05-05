#!/usr/bin/env python3
"""
ファクトチェックスクリプト
stdin からテキストを受け取り、gpt-5.4-mini でファクトチェックして stdout に出力する。
環境変数 OPENAI_API_KEY が必要。
"""

import sys
import os
from openai import OpenAI

SYSTEM_PROMPT = """あなたは科学・宇宙・物理分野の厳格なファクトチェッカーです。
与えられた文章の事実関係を検証し、以下の形式で日本語で報告してください。

## ファクトチェック結果

### 問題あり
各問題点を以下の形式で列挙：
- **[箇所]**: 問題の説明 → 修正案

### 問題なし
問題がない場合はその旨を記載。

### 総評
全体的な事実精度の評価（1〜2文）。

注意事項：
- 断言できる事実誤りのみ指摘する。不確実な場合は「要確認」と添える
- 科学的な数値・年号・固有名詞・発見者・理論名を重点的にチェックする
- 文体や表現の修正は行わない（事実のみ対象）
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

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
