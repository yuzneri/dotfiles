# MCP 利用方針（詳細）

CLAUDE.md の原則に加え、各MCPの詳細な使い分けをまとめる。

## Serena

- プロジェクトが未アクティベートでエラーになった場合、`activate_project` でアクティベートしてからやり直す。
- **ファイル全体を読まない**: `get_symbols_overview` → `find_symbol`（`include_body=True`）でシンボル単位で必要な箇所だけ読む。
- **シンボル編集を優先**: 関数・クラス単位の変更は `replace_symbol_body` を使う。行単位の部分修正は標準の Edit ツールを使う。
- **参照の追跡**: シンボルを変更する際は `find_referencing_symbols` で影響範囲を確認し、後方互換性を保つか参照元も更新する。

## ドキュメント参照（Context7 / DeepWiki / MDN）

| 観点 | Context7 | DeepWiki | MDN |
|---|---|---|---|
| 対象 | 外部ライブラリ / API の仕様 | GitHub リポジトリの構造・実装 | Web標準プラットフォーム（JS言語機能・CSS・HTML・Web API） |
| 用途 | 実装方法、設定値、API名、バージョン差分 | ディレクトリ構成、モジュール役割、repo文脈QA | 標準APIの仕様・構文・挙動、ブラウザ互換性 |
| 使い方 | `resolve-library-id` → `query-docs` | まず構造確認 → 必要箇所を読む | `search` → `get-doc`、互換性は `get-compat` |

- **併用時の順序**: DeepWiki（repo把握）→ Context7（外部仕様）→ repo文脈に合わせて実装
- 外部ライブラリの実装・設定・コード生成時は Context7 を原則使う
- バージョン差がありそうな場合はバージョンを明示して確認する
- repo 固有の事情と外部仕様を区別して説明する。バージョン差・非推奨 API・破壊的変更は明示し、不明な点は断定しない

### MDN（Web標準プラットフォーム）

MDN Web Docs を参照する。Web標準の言語機能・API・ブラウザ互換性に特化し、訓練データより正確で新しい情報を返す。

- **対象**: JavaScript の言語機能、CSS プロパティ、HTML 要素、Web API（DOM・Fetch・WebGL 等）など、ブラウザ／ランタイムが実装する標準技術。
- **Context7 との使い分け**: フレームワーク／ライブラリ（React・Next.js 等）の仕様は **Context7**、Web プラットフォーム標準は **MDN**。どちらにも見えるとき（例: `fetch`・`Promise`）は標準技術なので **MDN** を優先。
- **ツールの流れ**: `search`（質問を `fetch`・`flexbox` 等の web 技術キーワードに言い換えて検索）→ 候補の `path` を `get-doc` で全文取得。詳細な構文・コード例・仕様が必要なときに `get-doc` まで進む。
- **ブラウザ互換性**: `search`／`get-doc` が返す `compat-key` を `get-compat` に渡して取得する。BCD キーは推測せず、必ず `search`／`get-doc` 経由で得たものを使う。互換性を調べたいときは検索クエリに「browser compatibility」を含めず、機能名そのもので検索する。

## Web情報収集（検索・フェッチ）

標準ツールを第一選択とし、不足があれば MCP に切り替える。

**検索:**

| ツール | 用途 | 使うとき |
|---|---|---|
| **WebSearch**（標準） | 汎用Web検索 | 第一選択。一般的な技術情報・最新ニュース・ドキュメント検索 |
| **Exa**: `web_search_exa` | セマンティック検索（AI最適化） | WebSearch では情報が浅い／キーワード一致では拾えない場合。技術的・学術的に質の高い結果が必要なとき |
| RivalSearch: `web_search` | DuckDuckGo + Yahoo | WebSearch/Exa の両方で目的の情報が取れなかったときの最終フォールバック |
| RivalSearch: `social_search` | Reddit・HN・Dev.to | コミュニティの声・実体験 |
| RivalSearch: `github_search` | OSSリポジトリ検索 | ライブラリ選定・実装例の調査 |
| RivalSearch: `news_aggregation` | ニュース集約 | 最新動向・リリース情報 |
| RivalSearch: `scientific_research` | 学術論文・データセット | 学術的裏付け（arXiv・PubMed等） |
| RivalSearch: `research_topic` / `research_agent` | 包括調査 | 複数ソースの横断的リサーチ |

**判断順（検索）**:
1. まず **WebSearch**（標準）。一般的なクエリはこれで足りる
2. 結果が浅い／意味的に近い情報を引きたい／技術ドキュメントや論文の質を上げたい → **Exa: `web_search_exa`**
3. SNS・OSS・学術など領域特化が必要 → **RivalSearch** の該当ツール（`social_search`/`github_search`/`news_aggregation`/`scientific_research`/`research_topic`）
4. WebSearch・Exa の両方で目的の情報が取れなかった → **RivalSearch: `web_search`**（別インデックスでの最終フォールバック）

**フェッチ:**

| ツール | 用途 | 使うとき |
|---|---|---|
| **WebFetch**（標準） | URL→Markdown変換 | 第一選択。静的ページのコンテンツ取得 |
| **Exa**: `web_fetch_exa` | 複数URLを一括でクリーンMarkdown化 | Exa検索の結果を深掘り、または複数URLをまとめて取得したいとき |
| RivalSearch: `content_operations` / `map_website` | 取得+分析・サイト探索 | 検索→取得→分析の一連の流れ |
| **Playwright** | ブラウザ実行 | JSレンダリング必要（SPA等）、ブラウザ操作、スクリーンショット |
| **ScrapingAnt**: `get_web_page_markdown` 等 | プロキシ経由のページ取得 | CAPTCHA・403・Cloudflareチャレンジ等でブロックされた場合のフォールバック |

**判断順（フェッチ）**:
1. まず **WebFetch**（標準）
2. Exa検索からの直接の深掘り、または複数URLを一括取得したい → **Exa: `web_fetch_exa`**
3. 取得＋分析を一気に行いたい／サイト構造を辿りたい（リンクマップ・クロール） → **RivalSearch: `content_operations` / `map_website`**
4. コンテンツが空・不完全（SPA等で JSレンダリングが必要） → **Playwright**
5. ブロック（CAPTCHA・403・アンチボット）される → **ScrapingAnt**

- 回答にはソースURLを必ず付記する
- Exa は APIキー課金のため、軽い用件で安易に呼ばない。標準ツールで足りるならそちらを優先する

## ドキュメント変換（MarkItDown）

ローカルファイルをMarkdownに変換する。構造（見出し・テーブル・リンク等）を保持する。

- **対応形式**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), 画像（OCR）, HTML, CSV, JSON, XML, ZIP, EPub
- **標準の Read との使い分け**:
  - PDF 20ページ以内で十分 → **Read**（標準）
  - PDF が大きい / 構造保持が重要 → **MarkItDown**
  - Word・PowerPoint・Excel → **MarkItDown**（Read では非対応）
  - 画像の内容を見る（視覚的理解） → **Read**（マルチモーダル）
  - 画像からテキスト抽出（OCR） → **MarkItDown**
