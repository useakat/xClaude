---
title: commit_and_sync.sh の permissions パターン修正
date: 2026-05-05
tags: [infra]
---

← [変更ログへ](../changelog.md)

## 背景・動機

スキルが `bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh "..."` を呼び出すたびにパーミッションプロンプトが表示されていた。

`settings.json` の `permissions.allow` には既に以下のパターンが登録されていたが、機能していなかった：

```
"Bash(bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh *)"
```

原因は、`Bash(...)` パターンのパーサーが `$(git ...)` 内の `)` をパターンの終端と誤認識し、`*` ワイルドカードが解釈される前にパースが終了していたため。

## 実施内容

- `settings.json` の壊れたパターンを `"Bash(*commit_and_sync.sh *)"` に置き換え
- `*` ワイルドカードでパス部分（`bash $(git ...)` 以降）をスキップし、スクリプト名だけでマッチさせる形式に変更

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | commit_and_sync.sh の permissions パターンを `Bash(*commit_and_sync.sh *)` に修正 |

## 設計判断

- スキル側のコマンド（`$(git rev-parse --show-toplevel)` 形式）は変えない — remote セッションでリポジトリパスが変わっても動作するよう柔軟性を維持するため
- hardcoded パス `bash /root/xClaude/scripts/commit_and_sync.sh *` への変更は見送り（remote セッション非対応になるため）
- `*commit_and_sync.sh *` は他のスクリプトをカバーしない程度には絞られており、セキュリティリスクは許容範囲内と判断

## 確認結果

次回 commit_and_sync.sh 呼び出し時にパーミッションプロンプトが表示されないことを確認予定。
