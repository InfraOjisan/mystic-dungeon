# LLMWiki 構築計画: Codex / Ollama 版

作成日: 2026-05-04

## 目的

Karpathy 氏の LLM Wiki パターンを、Claude Code 常用ではなく Codex と Ollama を中心に構築する。日常運用で大量のトークンを使う前提のため、通常処理はローカル LLM で完結させ、品質が必要な設計変更・難しい統合・大規模整理だけ Codex を使う。

参考:

- Karpathy, "LLM Wiki": https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Claude Code + Obsidian 事例: https://qiita.com/TaichiEndoh/items/eddc358e42d6c575fded

## 基本方針

LLMWiki は RAG の代替ではなく、知識を毎回検索時に再構成するのではなく、LLM が継続的に Markdown Wiki を編集・保守する方式とする。

採用する中核原則:

- raw sources は不変の一次資料として保存する。
- wiki は LLM が編集する派生知識ベースとして扱う。
- schema は LLM の作業規約として `AGENTS.md` に明文化する。
- `index.md` は内容カタログ、`log.md` は時系列ログとして必ず更新する。
- 回答や調査結果も価値があれば wiki に保存し、チャット履歴に閉じ込めない。
- Obsidian は閲覧・リンク確認・グラフ確認用の IDE として使う。

## 推奨アーキテクチャ

```text
llmwiki/
  AGENTS.md                 # Codex / LLM 向け作業規約
  README.md                 # 人間向けの運用説明
  raw/                      # 一次資料。原則としてLLMは編集しない
    inbox/                  # 未処理ソース
    processed/              # 処理済みソース
    assets/                 # 画像、PDF、添付ファイル
  wiki/                     # LLMが維持するMarkdown Wiki
    index.md                # 内容カタログ
    log.md                  # 追記専用の作業ログ
    overview.md             # 全体像
    entities/               # 人物、組織、製品、場所など
    concepts/               # 概念、技術、テーマ
    sources/                # ソース単位の要約
    syntheses/              # 横断分析、比較、論点整理
    questions/              # 問いと回答、調査結果
  prompts/                  # Ollama/Codexで再利用するプロンプト
    ingest.md
    query.md
    lint.md
    daily.md
  scripts/                  # 任意の補助スクリプト
    wiki_search.sh
    ingest_one.sh
    lint_links.sh
  exports/                  # 記事、スライド、レポート出力
```

このリポジトリ直下に作る場合は、`llmwiki/` をサブディレクトリとして置く。Obsidian では `llmwiki/` を Vault として開く。

## 役割分担

### Ollama

日常運用の主担当。コストを抑えるため、以下をローカルで処理する。

- 新規ソースの一次要約
- 既存 wiki への追記候補作成
- エンティティ・概念ページの差分更新案作成
- リンク候補の抽出
- 軽量 lint
- 日次サマリ

推奨モデル候補:

- 日本語・一般用途: `qwen3:14b` 以上、または同等の日本語に強いモデル
- 軽量運用: `qwen3:8b`、`llama3.1:8b`、`gemma3:12b` など
- 長文・精度重視: ローカル GPU/メモリに余裕があれば 30B クラス以上

モデル名は環境依存なので、初期設定では `OLLAMA_MODEL` 環境変数で差し替えられるようにする。

### Codex

常用の大量処理ではなく、構造化と品質管理の担当にする。

- `AGENTS.md` の設計・改善
- ディレクトリ構造やスクリプトの整備
- 大きな矛盾解消
- 複数ページにまたがるリファクタリング
- Lint ルールの追加
- 重要な synthesis ページの作成
- Ollama の出力品質が不足する場合のレビュー

Codex を使う場面を絞ることで、日々のトークン消費を Ollama 側へ逃がしつつ、破綻しやすい構造設計だけ高性能なエージェントに任せる。

## 初期ファイル設計

### `AGENTS.md`

Codex または他のエージェントが読む最重要設定ファイル。以下を必ず含める。

```markdown
# LLMWiki Agent Instructions

## Scope

You maintain the Markdown wiki under `wiki/`.
You may read files under `raw/`, but must not modify original raw sources.

## Required Files

- `wiki/index.md`: content-oriented catalog. Update after every ingest.
- `wiki/log.md`: append-only chronological log. Append after every ingest, query, and lint pass.
- `wiki/overview.md`: high-level map of the wiki.

## Ingest Workflow

1. Read one source from `raw/inbox/`.
2. Create or update one source summary under `wiki/sources/`.
3. Identify entities, concepts, claims, dates, and contradictions.
4. Update relevant pages under `wiki/entities/`, `wiki/concepts/`, and `wiki/syntheses/`.
5. Add Obsidian wikilinks.
6. Update `wiki/index.md`.
7. Append an entry to `wiki/log.md`.
8. Move no raw files unless explicitly instructed by the user.

## Citation Policy

Every factual claim that comes from a source must include a source reference.
Prefer links to `wiki/sources/...` and include the raw source filename when useful.

## Page Style

- Use YAML frontmatter.
- Use concise sections.
- Prefer Obsidian wikilinks for internal links.
- Preserve uncertainty and contradictions.
- Do not invent missing details.
```

### `wiki/index.md`

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

### `wiki/log.md`

ログは機械的に検索しやすい形式にする。

```markdown
# Log

## [2026-05-04] setup | Initial LLMWiki plan

- Created initial architecture plan.
- Next: create `llmwiki/` scaffold and `AGENTS.md`.
```

### Wiki ページ frontmatter

```yaml
---
type: concept
status: draft
created: 2026-05-04
updated: 2026-05-04
sources: []
tags: []
---
```

推奨 `type`:

- `source`
- `entity`
- `concept`
- `synthesis`
- `question`
- `project`

## 運用フロー

### 1. Ingest

新しい資料を `raw/inbox/` に置き、Ollama で一次処理する。

```text
User:
raw/inbox/article_001.md を ingest して。

Agent:
- source summary を作る
- 既存 index を読む
- 関係する entity/concept を更新する
- 新しいリンクを追加する
- log に記録する
```

Ollama 用プロンプトは `prompts/ingest.md` に保存する。最初は1資料ずつ処理し、品質が安定してからバッチ化する。

### 2. Query

質問に答えるときは raw ではなく wiki を先に読む。

```text
User:
このテーマの主要論点を比較表にして。

Agent:
- `wiki/index.md` を読む
- 関連ページを読む
- 回答を作る
- 価値がある場合は `wiki/questions/` または `wiki/syntheses/` に保存する
- log に記録する
```

### 3. Lint

週1回または大量 ingest 後に実施する。

確認項目:

- 孤立ページ
- 壊れた wikilink
- 同じ概念の重複ページ
- source がない事実主張
- 古い情報と新しい情報の矛盾
- `index.md` に載っていないページ
- 重要だがページ化されていない概念

軽量 lint は Ollama、構造変更を伴う lint は Codex に任せる。

### 4. Daily Review

日次で `wiki/log.md` の直近エントリを要約し、必要なら `wiki/syntheses/daily-YYYY-MM-DD.md` に保存する。

目的:

- 間違った要約の早期発見
- 重要テーマの浮上
- 次に読むべき資料の候補出し
- taxonomy の肥大化防止

## コスト最適化設計

トークン消費を抑えるため、毎回すべてを読ませない。

1. まず `wiki/index.md` を読む。
2. 関連しそうなページだけ読む。
3. raw sources は必要な場合だけ読む。
4. 大きな資料は source summary を先に作る。
5. 更新対象ページを明示してから編集する。
6. Codex は「全体設計」「品質レビュー」「スクリプト化」に限定する。

Ollama は推論時間がコストになるため、以下も意識する。

- 長い PDF は Markdown 化してから処理する。
- 画像は必要なものだけ個別に見る。
- 一度作った source summary を再利用する。
- `index.md` を厚くしすぎず、1行要約に留める。
- synthesis は定期更新にして、毎 ingest では更新しすぎない。

## 最小実装ステップ

### Phase 0: Vault 作成

- `llmwiki/` ディレクトリを作る。
- `AGENTS.md` を作る。
- `wiki/index.md`、`wiki/log.md`、`wiki/overview.md` を作る。
- Obsidian で `llmwiki/` を Vault として開く。

### Phase 1: 手動 ingest

- `raw/inbox/` に Markdown 化した資料を1つ置く。
- Ollama で `prompts/ingest.md` を使って処理する。
- 生成結果を人間が Obsidian で確認する。
- 問題が出たら `AGENTS.md` を更新する。

### Phase 2: 半自動 ingest

- `scripts/ingest_one.sh` を作る。
- モデル、入力ファイル、出力先を引数化する。
- 更新後に `index.md` と `log.md` の更新漏れをチェックする。

### Phase 3: Lint と検索

- `scripts/lint_links.sh` で壊れたリンクを検出する。
- `rg` ベースの検索を使う。
- 必要になったら `qmd` やローカル全文検索を追加する。

### Phase 4: Codex レビュー

- 週1回または月1回、Codex に wiki の構造レビューを依頼する。
- 重複概念、矛盾、taxonomy の乱れを整理する。
- Lint 結果をもとに `AGENTS.md` とプロンプトを改善する。

## コマンド例

Ollama の起動確認:

```bash
ollama list
ollama run "$OLLAMA_MODEL"
```

単一ファイルの ingest 例:

```bash
export OLLAMA_MODEL=qwen3:14b
ollama run "$OLLAMA_MODEL" < prompts/ingest.md
```

実運用では入力ファイル本文、`wiki/index.md`、関連ページをプロンプトに結合する `scripts/ingest_one.sh` を作る。

検索例:

```bash
rg "検索語" wiki/
rg "^## \\[" wiki/log.md
```

## 判断基準

Codex を使うべきケース:

- 複数ディレクトリにまたがる設計変更
- `AGENTS.md` の改善
- wiki の大規模再編
- 複雑な矛盾の解消
- 補助スクリプト作成
- Ollama が同じ失敗を繰り返す場合

Ollama で十分なケース:

- 1資料の要約
- 既存ページへの小さな追記
- リンク候補抽出
- 日次ログ要約
- 軽い質問応答
- source summary の初稿作成

## リスクと対策

| リスク | 対策 |
|---|---|
| 要約ミスが wiki 全体に伝播する | source summary に出典を明記し、Daily Review で早期確認する |
| ページが増えすぎて検索しづらい | `index.md` を必ず更新し、週次 lint で統合候補を出す |
| Ollama の品質が不安定 | 重要ページだけ Codex でレビューする |
| raw と wiki の境界が曖昧になる | `raw/` は不変、`wiki/` は派生物と AGENTS.md に明記する |
| Obsidian リンクが壊れる | 定期的に `[[...]]` を lint する |
| トークン消費が増える | index-first、関連ページ限定、raw 再読最小化を徹底する |

## 初期構築で次に作るもの

1. `llmwiki/AGENTS.md`
2. `llmwiki/wiki/index.md`
3. `llmwiki/wiki/log.md`
4. `llmwiki/wiki/overview.md`
5. `llmwiki/prompts/ingest.md`
6. `llmwiki/prompts/query.md`
7. `llmwiki/prompts/lint.md`
8. `llmwiki/scripts/ingest_one.sh`

まずは Phase 0 と Phase 1 だけを実装し、数件の資料で運用感を確認する。その後、Ollama の出力品質と処理時間を見て、モデル選定・プロンプト・Codex の介入頻度を調整する。
