# MCP 利用方針（詳細）

CLAUDE.md の原則に加え、各MCPの詳細な使い分けをまとめる。

## Serena

- プロジェクトが未アクティベートでエラーになった場合、`activate_project` でアクティベートしてからやり直す。
- **ファイル全体を読まない**: `get_symbols_overview` → `find_symbol`（`include_body=True`）でシンボル単位で必要な箇所だけ読む。
- **シンボル編集を優先**: 関数・クラス単位の変更は `replace_symbol_body` を使う。行単位の部分修正は標準の Edit ツールを使う。
- **参照の追跡**: シンボルを変更する際は `find_referencing_symbols` で影響範囲を確認し、後方互換性を保つか参照元も更新する。

## ドキュメント参照（Context7 / DeepWiki）

| 観点 | Context7 | DeepWiki |
|---|---|---|
| 対象 | 外部ライブラリ / API の仕様 | GitHub リポジトリの構造・実装 |
| 用途 | 実装方法、設定値、API名、バージョン差分 | ディレクトリ構成、モジュール役割、repo文脈QA |
| 使い方 | `resolve-library-id` → `query-docs` | まず構造確認 → 必要箇所を読む |

- **併用時の順序**: DeepWiki（repo把握）→ Context7（外部仕様）→ repo文脈に合わせて実装
- 外部ライブラリの実装・設定・コード生成時は Context7 を原則使う
- バージョン差がありそうな場合はバージョンを明示して確認する
- repo 固有の事情と外部仕様を区別して説明する。バージョン差・非推奨 API・破壊的変更は明示し、不明な点は断定しない

## Web情報収集（検索・フェッチ）

標準ツールを第一選択とし、不足があれば MCP に切り替える。

**検索:**

| ツール | 用途 | 使うとき |
|---|---|---|
| **WebSearch**（標準） | 汎用Web検索 | 第一選択。技術情報・ドキュメント検索 |
| RivalSearch: `web_search` | DuckDuckGo + Yahoo | WebSearch で不十分な場合の補完 |
| RivalSearch: `social_search` | Reddit・HN・Dev.to | コミュニティの声・実体験 |
| RivalSearch: `github_search` | OSSリポジトリ検索 | ライブラリ選定・実装例の調査 |
| RivalSearch: `news_aggregation` | ニュース集約 | 最新動向・リリース情報 |
| RivalSearch: `scientific_research` | 学術論文・データセット | 学術的裏付け（arXiv・PubMed等） |
| RivalSearch: `research_topic` / `research_agent` | 包括調査 | 複数ソースの横断的リサーチ |

**フェッチ:**

| ツール | 用途 | 使うとき |
|---|---|---|
| **WebFetch**（標準） | URL→Markdown変換 | 第一選択。静的ページのコンテンツ取得 |
| RivalSearch: `content_operations` / `map_website` | 取得+分析・サイト探索 | 検索→取得→分析の一連の流れ |
| **Playwright** | ブラウザ実行 | JSレンダリング必要（SPA等）、ブラウザ操作、スクリーンショット |

- WebFetch でコンテンツが空・不完全 → JSレンダリングが必要 → Playwright
- 回答にはソースURLを必ず付記する

## ドキュメント変換（MarkItDown）

ローカルファイルをMarkdownに変換する。構造（見出し・テーブル・リンク等）を保持する。

- **対応形式**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), 画像（OCR）, HTML, CSV, JSON, XML, ZIP, EPub
- **標準の Read との使い分け**:
  - PDF 20ページ以内で十分 → **Read**（標準）
  - PDF が大きい / 構造保持が重要 → **MarkItDown**
  - Word・PowerPoint・Excel → **MarkItDown**（Read では非対応）
  - 画像の内容を見る（視覚的理解） → **Read**（マルチモーダル）
  - 画像からテキスト抽出（OCR） → **MarkItDown**
