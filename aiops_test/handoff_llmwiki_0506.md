# LLMWiki 引き継ぎメモ

作成日: 2026-05-06  
作業ディレクトリ: `/Users/kuroda/Public/code/aiops_test`

このファイルは、別端末の Codex で LLMWiki の続きの処理と環境構築を矛盾なく実行するための引き継ぎ情報である。

## 次の Codex への最短指示

```text
作業ディレクトリ `/Users/kuroda/Public/code/aiops_test` で、
`handoff_llmwiki_0506.md` と `plan_llmwiko_0504.md` を読んでください。

まだ `llmwiki/` 本体は未作成です。
まず Phase 0 として、設計書に沿って `llmwiki/` のディレクトリ、`AGENTS.md`、初期 wiki ファイル、prompts、scripts の雛形を作成してください。

既存の Lubuntu/Zabbix 系レポートファイルは今回の LLMWiki 作業とは無関係なので編集しないでください。
```

## 現在の状態

- カレントディレクトリは `/Users/kuroda/Public/code/aiops_test`。
- Git リポジトリではない。`git status --short` は `fatal: not a git repository` で終了する。
- 前回作成済みの設計書は `plan_llmwiko_0504.md`。
- `llmwiki/` ディレクトリはまだ存在しない。
- 環境構築、Ollama モデル導入、Obsidian Vault 作成はまだ未実施。

既存ファイル:

```text
-
host-lubunt-access.dat
host-lubunt-access.txt
log_report_lubuntu_0502.md
plan_llmwiko_0504.md
report_lubuntu_0502_2.md
report_lubuntu_zabbix_0502.md
report_lubuntu_zabbix_0502_2.md
```

注意: `plan_llmwiko_0504.md` は `llmwiki` ではなく `llmwiko` という綴りだが、ユーザー指定どおりのファイル名である。勝手にリネームしない。

## ここまでの依頼内容

ユーザーは、Karpathy 氏が提唱した LLMWiki を Codex または Ollama で構築したい。Claude Code + Obsidian の事例はあるが、継続運用時のトークン消費とコストが大きいため、Claude Code 常用ではなく Codex または Ollama を使いたい、という前提。

参照されたURL:

- Karpathy 氏の LLMWiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Claude Code + Obsidian 事例: https://qiita.com/TaichiEndoh/items/eddc358e42d6c575fded

前回の対応では、これらを確認したうえで `plan_llmwiko_0504.md` を作成した。

## 設計上の決定事項

LLMWiki は RAG のように毎回 raw source を検索して回答する仕組みではなく、LLM が継続的に Markdown Wiki を編集・保守する知識ベースとして扱う。

基本方針:

- `raw/` は不変の一次資料置き場。
- `wiki/` は LLM が編集する派生知識ベース。
- `AGENTS.md` を schema / 作業規約として使う。
- `wiki/index.md` は内容カタログとして必ず更新する。
- `wiki/log.md` は時系列ログとして必ず追記する。
- 回答や調査結果も価値があれば wiki に保存する。
- Obsidian は閲覧、リンク確認、グラフ確認用の IDE として使う。

役割分担:

- Ollama: 日常の ingest、要約、リンク候補抽出、軽量 lint、日次サマリ。
- Codex: 初期構築、構造設計、`AGENTS.md` 改善、大規模整理、矛盾解消、スクリプト作成、重要ページのレビュー。

## 次に作る構成

Phase 0 で以下を作成する。

```text
llmwiki/
  AGENTS.md
  README.md
  raw/
    inbox/
    processed/
    assets/
  wiki/
    index.md
    log.md
    overview.md
    entities/
    concepts/
    sources/
    syntheses/
    questions/
  prompts/
    ingest.md
    query.md
    lint.md
    daily.md
  scripts/
    wiki_search.sh
    ingest_one.sh
    lint_links.sh
  exports/
```

Obsidian を使う場合は、`/Users/kuroda/Public/code/aiops_test/llmwiki` を Vault として開く。

## 初期ファイルの要件

### `llmwiki/AGENTS.md`

最低限、以下を含める。

- `wiki/` 以下を LLM が保守対象にする。
- `raw/` は読んでよいが、原則として編集しない。
- ingest 後は `wiki/index.md` と `wiki/log.md` を必ず更新する。
- factual claim は source を持たせる。
- Obsidian wikilink を使う。
- 不確実性と矛盾を消さずに記録する。
- 推測で事実を作らない。

### `llmwiki/wiki/index.md`

初期見出し:

```markdown
# Index

## Overview

- [[overview]] - Wiki全体の地図

## Sources

| Page | Raw Source | Summary | Updated |
|---|---|---|---|

## Entities

| Page | Type | Summary | Sources |
|---|---|---|---|

## Concepts

| Page | Summary | Sources |
|---|---|---|

## Syntheses

| Page | Question | Summary | Updated |
|---|---|---|---|
```

### `llmwiki/wiki/log.md`

追記専用ログとして開始する。

```markdown
# Log

## [2026-05-06] setup | Initial scaffold

- Created initial LLMWiki scaffold.
- Based on `../plan_llmwiko_0504.md`.
```

### `llmwiki/wiki/overview.md`

Wiki 全体の目的、構造、現在の空状態を短く説明する。

### `llmwiki/prompts/*.md`

最初は雛形でよい。最低限、以下を作る。

- `ingest.md`: 1つの raw source から source summary と関連ページ更新案を作る指示。
- `query.md`: `index.md` を起点に関連ページを読んで回答し、価値があれば wiki に保存する指示。
- `lint.md`: 壊れたリンク、重複概念、出典不足、index 漏れを検出する指示。
- `daily.md`: `log.md` の直近エントリを要約し、必要なら synthesis を作る指示。

### `llmwiki/scripts/*.sh`

最初は安全な補助スクリプトでよい。

- `wiki_search.sh`: `rg` で `wiki/` を検索する。
- `lint_links.sh`: `[[...]]` のリンク候補を抽出し、存在確認の足場にする。
- `ingest_one.sh`: 最初は usage と環境変数チェックだけでもよい。Ollama 実行は後で実装してもよい。

スクリプトは destructive な動作を入れない。raw source の移動も自動化しない。

## 環境構築メモ

次の端末で確認すること:

```bash
cd /Users/kuroda/Public/code/aiops_test
pwd
ls -la
command -v ollama
ollama --version
ollama list
command -v rg
rg --version
```

Ollama が入っていない場合は、ユーザー環境に合わせて公式手順で導入する。Codex の sandbox 内からモデル取得やインストールが必要になり、ネットワーク制限で失敗した場合は、Codex の承認付き escalation を使う。

推奨モデル候補:

- 日本語・一般用途: `qwen3:14b`
- 軽量確認: `qwen3:8b`
- 代替: `llama3.1:8b`、`gemma3:12b`

モデル取得例:

```bash
ollama pull qwen3:14b
export OLLAMA_MODEL=qwen3:14b
ollama run "$OLLAMA_MODEL"
```

実際のモデルはローカルマシンのメモリ、GPU、応答速度で調整する。

## 実装順序

1. `plan_llmwiko_0504.md` を読む。
2. `llmwiki/` のディレクトリを作る。
3. `llmwiki/AGENTS.md` を作る。
4. `wiki/index.md`、`wiki/log.md`、`wiki/overview.md` を作る。
5. `prompts/ingest.md`、`query.md`、`lint.md`、`daily.md` を作る。
6. `scripts/wiki_search.sh`、`lint_links.sh`、`ingest_one.sh` を作る。
7. `chmod +x llmwiki/scripts/*.sh` を実行する。
8. `find llmwiki -maxdepth 3 -type f | sort` で作成結果を確認する。
9. 可能なら `llmwiki/scripts/wiki_search.sh LLMWiki` を実行して動作確認する。
10. Ollama がある場合だけ、モデル確認と簡単な疎通確認を行う。

## 次の Codex が避けるべきこと

- `plan_llmwiko_0504.md` をリネームしない。
- Lubuntu/Zabbix 系の既存レポートを編集しない。
- raw source を勝手に移動・削除しない。
- まだ存在しない資料を前提に entity/concept ページを大量生成しない。
- 最初から複雑な自動 ingest を作り込まない。
- Git リポジトリではないので、commit / branch 前提で進めない。

## 完了条件

次の作業の完了条件は以下。

- `llmwiki/` が作成されている。
- `AGENTS.md` が存在し、Codex/Ollama が迷わず作業できる規約になっている。
- `wiki/index.md`、`wiki/log.md`、`wiki/overview.md` が存在する。
- prompts 4件が存在する。
- scripts 3件が存在し、少なくとも検索スクリプトは実行できる。
- 既存の無関係ファイルは変更されていない。
- 最終報告で、作成ファイルと未実施の環境作業が明記されている。

## 追加で実施するとよい確認

作成後、以下を実行して結果を確認する。

```bash
find llmwiki -maxdepth 3 -type f | sort
find llmwiki -maxdepth 3 -type d | sort
llmwiki/scripts/wiki_search.sh Index
```

Ollama が使える場合:

```bash
ollama list
ollama run "$OLLAMA_MODEL" "日本語で1文だけ返答してください: LLMWiki準備完了"
```

ただし、Ollama の導入やモデル pull はネットワークとローカル環境に依存するため、ファイル作成とは分けて扱う。
