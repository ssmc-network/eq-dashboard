# CLAUDE.md

このファイルは、このリポジトリで作業する Claude Code (claude.ai/code) へのガイダンスを提供します。

## これは何か

工場設備の稼働状態をフロアマップ風のキャンバス上に可視化する、FastAPI + HTMX 製のダッシュボードです(装置の稼働状態可視化)。装置の図形は固定された白いキャンバス上に直接描画され、稼働状態(稼働中 / 停止中 / アラーム)に応じて色分けされます。レイアウトはドラッグ&リサイズで編集可能です。名前付きの複数キャンバス(「キャンバス」、例: 階層ごと・部屋ごと)に対応しており、ダッシュボードから切り替えられます。

**絶対的な制約: このアプリはDBに直接アクセスしてはいけません。** データはローカルのJSONファイル(現在の「オフライン/スタンドアロン」モード)、または将来的には外部バックエンドのREST API(「オンライン」モード)から取得します。DBドライバやORMを追加したくなったら、それは間違いです — それは必ず、このリポジトリが呼び出すREST APIの向こう側に置くべきものです。

## コマンド

Pythonのコマンドはすべて `app/` から実行します(`app/` はPoetryプロジェクトのルートそのものであり、内部にネストしたパッケージではありません — 内部importは `from routes import api, ui` のように `app.` プレフィックスなしのベタ指定です)。

```bash
cd app
poetry install                 # 依存関係をインストール(lint/型チェック/テストツールも入れる場合は --with dev を追加)
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000   # 開発サーバー起動
poetry run ruff check .        # lint
poetry run ruff format .       # フォーマット
poetry run mypy .              # 型チェック
poetry run pytest              # テスト(現時点で tests/ ディレクトリは存在しません)
```

Docker(UBI9ベースのマルチステージビルド: `base` → `dependencies` → `dev`/`prd`):

```bash
docker compose up -d                                            # devターゲット。compose.override.yaml を使用
docker compose -f compose.yaml -f compose.production.yaml up -d --build   # prdターゲット。ポート8888
```

composeファイルは意図的にCompose Specificationの命名(`compose.yaml` / `compose.override.yaml` / `compose.production.yaml`)に従っています — `docker-` プレフィックスなし、拡張子も統一(`.yaml`のみ)。overrideファイルを追加する場合もこの命名規則を維持してください。

## ブランチ運用とCI/CD

**ブランチモデル**: `main`(保護ブランチ、直pushは不可) / `release/<バージョン>`(例: `release/1.0.0`) / 開発ブランチ(`feature/...`、`claude/...`など)の3層。

1. リリースするバージョンの `release/<バージョン>` ブランチを先に切る
2. 開発ブランチを `release/<バージョン>` から切って作業し、完了したらPRで `release/<バージョン>` にマージする(これを繰り返す)
3. `release/<バージョン>` が完成したらPRで `main` にマージする

`release/*` へのPRと `main` へのPRとでCIの役割を分けている(後述)。

**CI(`.github/workflows/`)**:

- `test.yaml` — `release/*` へのPRで実行。`dev` ターゲットのDockerイメージをビルドし、その中で `ruff check` / `ruff format --check` / `pytest`(`tests/` が無ければスキップ)を実行する。ここでは本番用イメージのビルドやpushは行わない。
- `build.yaml` — `main` へのPRが**マージされたとき**にのみ実行(`pull_request: types: [closed]` + `if: github.event.pull_request.merged == true`)。`main` は直pushできない保護ブランチなので、`push` イベントではなくPRマージイベントで発火させている。バージョン番号はマージ元ブランチ名(`github.event.pull_request.head.ref`、例: `release/1.0.0`)から `release/` を取り除いて取得し、`prd` ターゲットのイメージを `latest` とそのバージョンタグの両方でDocker Hubへpushしたあと、Trivyで脆弱性スキャンする(現状はレポートのみで、CIを失敗させる設定にはしていない)。チェックアウトは `github.event.pull_request.merge_commit_sha` を明示指定している(`pull_request` イベントのデフォルトrefは一時的なテストマージ用refのため)。
- Docker Hubへのpushには `secrets.DOCKER_TOKEN` を使用し、ユーザー名はGitHubのユーザー名(`github.actor`)と共通の前提(Docker HubとGitHubで同じユーザー名運用)。

## アーキテクチャ

**レイヤー構成**: `routes/` → `services/` → `providers/` → `schemas/`。

- `routes/ui.py` — HTMX/ページ用ルート。`Jinja2Templates` の `HTMLResponse` を返す(HTMXスワップ用の全体ページと `partials/*` の部分テンプレートの両方)。
- `routes/api.py` — `/api` プレフィックス配下のJSON API。エクスポート用エンドポイント(`GET /api/standalone/layout/export`、`GET /api/standalone/status/export`)と `POST /api/layouts/save`(レイアウト編集画面の直接保存ボタンから使用)。
- `services/` — ビジネスロジック(`layout_service`、`status_service`、`import_export_service`)。自身ではI/Oを行わず、`providers/` を呼び出す。
- `providers/json_status_provider.py` — レイアウト/ステータスデータに関してファイルシステムに触れる唯一の場所。`JsonStatusProvider` が `data/sample/layouts/<id>/layout.json` と、単一グローバルな `data/sample/status.json` を読み書きする。
- `schemas/` — Pydantic v2 モデル群。ディスク/通信上のJSONはcamelCase、Python側はsnake_caseで、`Field(alias=...)` + `ConfigDict(populate_by_name=True)` で橋渡ししている(例: `tag_id: str = Field(alias="tagId")`)。

**データモデル**: レイアウトはキャンバスごと(`layouts/<layout_id>/layout.json`: 図形、位置/サイズ、各アイテムの `tagId`)。ステータスはキャンバスごとではなく、`tagId` をキーとした*単一のグローバルファイル*(`status.json`)— `status_service.get_dashboard(layout_id)` がレイアウトを読み込み、ステータススナップショット全体を読み込んで、メモリ上で `tag_id` により結合する。これは将来の実バックエンドが持つ単一の `status_cache` 設計を踏襲したものなので、拡張する際もステータスはグローバルのまま維持すること。

**永続化モデル(オフライン/スタンドアロンモード)**: 書き込みはローカルディスク上のこれらのJSONファイルへ直接行われる — 外部ボリュームもDBも使わない。これは意図的な設計: コンテナは使い捨て(再ビルドするとサンプルデータに戻る)であり、永続的なストレージは将来のオンラインバックエンド側に持たせる想定で、このアプリ自体には持たせない。これを「直す」ためにボリュームマウントやDBを追加しないこと — それが意図されたライフサイクル。Offline設定(スタンドアロン)画面のレイアウト・ステータスどちらのインポートにも、**検証 → 確認保存**の2段階パターン(`POST .../import` がプレビューと確認フォームを返し、`POST .../import/confirm` が実際に永続化する)を使用している — インポート可能なリソースを追加する場合もこのパターンに従うこと。レイアウトは(新規か上書きかの判定に)`id` で照合する。ステータスにはレコード単位のidが無いため、常に上書きとなる。

**オンラインモード(未実装)**: `repositories/*.py`、`providers/api_status_provider.py`、`schemas/api_config.py`、`templates/partials/api_source_detail.html` は、将来のREST APIバックエンドデータソース用に予約された空のスキャフォールドファイル。`operation_mode`(`online`/`offline`、Cookie)はUIのトグルとしてすでに存在するが、まだプロバイダの挙動をこれで切り替える実装はない — 現状は常に `JsonStatusProvider` が使われる。オンラインモードを実装する際は、`JsonStatusProvider` と同じインターフェース(`list_layouts`、`load_layout`、`save_layout`、`load_status`、`save_status`)を持つAPIベースのプロバイダを追加し、サービス層で `operation_mode` により切り替えること — ルートやテンプレートが `services/` を飛び越えてプロバイダに直接触れることは絶対にしないこと。

**設定**: `theme`、`operation_mode`、`default_layout_id`、`default_refresh_interval` はCookieとして永続化される(DBではない)— `routes/ui.py` でサーバー側検証を行い、値が不正/未設定の場合はデフォルトにフォールバックする。

**フロントエンド**: サーバーレンダリングのJinja2 + HTMX、ビルドステップなし。`static/js/htmx.min.js` は(CDNではなく)意図的にベンダリングされている — 工場フロアのオフラインネットワーク環境という利用実態にも、このサンドボックスでCDNアクセスがブロックされている事情にも合致するため。ダッシュボードの自動更新(`static/js/dashboard.js`)は、宣言的な `hx-trigger` ではなく `setInterval` から `htmx.ajax()` を直接呼び出す形でHTMXを手動駆動している — 実行時に再設定可能なポーリング間隔を `hx-trigger` で実現しようとしたところ、実ブラウザでの検証で不安定だったため。レイアウト編集画面(`static/js/layout_editor.js`)のドラッグ/リサイズは生のポインターイベントで実装しており、ドラッグ用ライブラリは使用していない。

**ナビゲーション**: サイドバー(`templates/base.html`)にはトップレベルの項目が3つ — ダッシュボード、レイアウト編集、システム設定(設定ハブ)。設定ハブからは Online設定(`/ui/api-sources`)、タグマッピング(`/ui/tag-mappings`)、Offline設定(`/ui/standalone`)へリンクしている — これらは設定のサブページであり独立したナビ項目ではないため、アクティブ状態のハイライト判定は各ナビ項目の `also: [...]` リストで管理している(`{% set %}` が `{% for %}` ループ内で値を保持しないため、Jinjaの `namespace()` を使って実装)。

CSS(`static/css/main.css`)は `@media (prefers-color-scheme: dark)` と `:root[data-theme="dark"/"light"]` の両方でテーマを定義している(手動トグルがOS設定より優先)。加えて、装置キャンバス用に別途 `--diagram-*` トークン群を用意している — キャンバスはアプリのテーマに関わらず常に固定の白い「紙」背景であるため、その配色はライト/ダークのトークン体系には含めていない。
