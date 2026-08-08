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
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-config log_config.yaml   # 開発サーバー起動
poetry run ruff check .        # lint
poetry run ruff format .       # フォーマット
poetry run mypy .              # 型チェック
poetry run pytest              # テスト
```

Docker(UBI9ベースのマルチステージビルド: `base` → `dependencies` → `dev`/`prd`):

```bash
docker compose up -d                                            # devターゲット。compose.override.yaml を使用
docker compose -f compose.yaml -f compose.production.yaml up -d --build   # prdターゲット。ポート8888
```

composeファイルは意図的にCompose Specificationの命名(`compose.yaml` / `compose.override.yaml` / `compose.production.yaml`)に従っています — `docker-` プレフィックスなし、拡張子も統一(`.yaml`のみ)。overrideファイルを追加する場合もこの命名規則を維持してください。

**OpenShift上での書き込み権限**: `dev`/`prd`いずれの最終COPY直後にも `RUN chmod -R g+rwX .../app/data` を入れている。イメージは `COPY --chown=1001:0` でUID 1001・GID 0所有にしているが、OpenShiftの既定SCC(`restricted`)はコンテナを**ランダムなUID・GID 0**で起動するため、実行時のUIDはビルド時の1001と一致しない。ファイルのグループ書き込み権限(`g+rwX`)が無いと、`data/`配下へのファイル保存(レイアウト保存・タグマッピング編集など)が`PermissionError`で失敗する(読み取り専用の操作は権限不要なので気づきにくい)。docker-compose(通常のDocker)ではコンテナがイメージ通りのUID 1001で動くためこの問題は再現しない — OpenShift固有の制約。

## ブランチ運用とCI/CD

**ブランチモデル**: `main`(保護ブランチ、直pushは不可) / `release/<バージョン>`(例: `release/1.0.0`) / 開発ブランチ(`feature/...`、`claude/...`など)の3層。

1. リリースするバージョンの `release/<バージョン>` ブランチを先に切る
2. 開発ブランチを `release/<バージョン>` から切って作業し、完了したらPRで `release/<バージョン>` にマージする(これを繰り返す)
3. `release/<バージョン>` が完成したらPRで `main` にマージする

`release/*` へのPRと `main` へのPRとでCIの役割を分けている(後述)。

**CI(`.github/workflows/`)**:

- `test.yaml` — `release/*` へのPRで実行。`dev` ターゲットのDockerイメージをビルドし、その中で `ruff check` / `ruff format --check` / `pytest`(`tests/` ディレクトリが無い場合のみスキップするガードが入っている)を実行する。ここでは本番用イメージのビルドやpushは行わない。
- `build.yaml` — `main` への **`push`** イベントで実行する(`on: push: branches: [main]`)。`main` は直pushできない保護ブランチだが、PRをGitHubのマージボタンでマージするとGitHub自身が `main` へマージコミットをpushする形になるため、`push` イベントは通常どおり発火する(保護ブランチが防いでいるのは「人間/CIによる直接push」だけで、マージに伴う内部的なpushは防いでいない)。以前は `pull_request: types: [closed]` + `if: github.event.pull_request.merged == true` を使っていたが、`pull_request` イベントで発行されるトークンは `permissions` やリポジトリのWorkflow permissions設定を`Read and write`にしても `actions/cache` の書き込み(`cache write denied: token has no writable scopes`)ができないことが判明し、`push` トリガーに変更した。バージョン番号はマージコミットのメッセージ(GitHubが自動生成する `Merge pull request #N from <owner>/release/<version>` という文言、`github.event.head_commit.message`)から正規表現で抽出する(マージ戦略を「Create a merge commit」以外に変更した場合はこの抽出が壊れる点に注意)。`prd` ターゲットのイメージを `latest` とそのバージョンタグの両方でDocker Hubへpushしたあと、Trivyで脆弱性スキャンする(現状はレポートのみで、CIを失敗させる設定にはしていない)。
- Docker Hubへのpushには `secrets.DOCKER_TOKEN` を使用し、ユーザー名はGitHubのユーザー名(`github.actor`)と共通の前提(Docker HubとGitHubで同じユーザー名運用)。

## アーキテクチャ

**レイヤー構成**: `routes/` → `services/` → `providers/` → `schemas/`。

- `routes/ui.py` — HTMX/ページ用ルート。`Jinja2Templates` の `HTMLResponse` を返す(HTMXスワップ用の全体ページと `partials/*` の部分テンプレートの両方)。
- `routes/api.py` — `/api` プレフィックス配下のJSON API。エクスポート用エンドポイント(`GET /api/standalone/layout/export`、`GET /api/standalone/status/export`)と `POST /api/layouts/save`(レイアウト編集画面の直接保存ボタンから使用)。
- `services/` — ビジネスロジック(`layout_service`、`status_service`、`import_export_service`)。自身ではI/Oを行わず、`providers/` を呼び出す。
- `providers/json_status_provider.py` — レイアウト/ステータスデータに関してファイルシステムに触れる唯一の場所。`JsonStatusProvider` が `data/sample/layouts/<id>/layout.json` と、単一グローバルな `data/sample/status.json` を読み書きする。
- `schemas/` — Pydantic v2 モデル群。ディスク/通信上のJSONはcamelCase、Python側はsnake_caseで、`Field(alias=...)` + `ConfigDict(populate_by_name=True)` で橋渡ししている(例: `tag_id: str = Field(alias="tagId")`)。
- `core/settings.py` / `core/log_modules.py` — ログ出力とその設定。`Settings`(`pydantic-settings`、`service`/`tz`/`loglevel`/`debug` を環境変数から読む。`tz`/`debug` は既存の compose の `TZ`/`DEBUG` 環境変数とそのまま対応)と、JSON形式のアプリケーションログを出すための `log_application(name)`。

**ログ出力**: アプリケーションログは `core.log_modules.log_application(__name__)` で取得したロガーを使い、必ずJSON形式(`timestamp`/`level`/`message`/`service`/`tag`/`details`)で出力する。認証や複数アプリ構成、リクエスト単位のトレースIDといった概念は今のところ無いため、`user_id`/`app_name`/`trace_id` のようなフィールドは持たせていない(必要になったら追加すること)。追加のコンテキスト情報を残したい場合は `logger.info(msg, extra={"argument": {...}})` の `argument` に辞書で渡す(`layout_service.save_layout` などを参照)。**意図的にHTTPリクエスト/レスポンスの全件ログ出力ミドルウェアは実装していない** — Online設定のAPIキー/Bearerトークンのような機密情報がリクエストボディに含まれる可能性があり、ログへの機密情報混入を避けるため。`services/api_test_service.py` の接続テストのログも、`credential` は出力せず `base_url`/`auth_type`/結果のみを記録している。uvicorn自身のログ(起動メッセージ・アクセスログ)は `log_config.yaml` を `--log-config` に渡すことで同じJSON形式に揃えている。`HealthCheckFilter` が `/health` へのアクセスログを除外する。

**データモデル**: レイアウトはキャンバスごと(`layouts/<layout_id>/layout.json`: 図形、位置/サイズ、各アイテムの `tagId`)。ステータスはキャンバスごとではなく、`tagId` をキーとした*単一のグローバルファイル*(`status.json`)— `status_service.get_dashboard(layout_id)` がレイアウトを読み込み、ステータススナップショット全体を読み込んで、メモリ上で `tag_id` により結合する。これは将来の実バックエンドが持つ単一の `status_cache` 設計を踏襲したものなので、拡張する際もステータスはグローバルのまま維持すること。

**永続化モデル(オフライン/スタンドアロンモード)**: 書き込みはローカルディスク上のこれらのJSONファイルへ直接行われる — 外部ボリュームもDBも使わない。これは意図的な設計: コンテナは使い捨て(再ビルドするとサンプルデータに戻る)であり、永続的なストレージは将来のオンラインバックエンド側に持たせる想定で、このアプリ自体には持たせない。これを「直す」ためにボリュームマウントやDBを追加しないこと — それが意図されたライフサイクル。Offline設定(スタンドアロン)画面のレイアウト・ステータスどちらのインポートにも、**検証 → 確認保存**の2段階パターン(`POST .../import` がプレビューと確認フォームを返し、`POST .../import/confirm` が実際に永続化する)を使用している — インポート可能なリソースを追加する場合もこのパターンに従うこと。レイアウトは(新規か上書きかの判定に)`id` で照合する。ステータスにはレコード単位のidが無いため、常に上書きとなる。レイアウトのExportは1キャンバスずつ(`GET /api/standalone/layout/export?layout_id=...`)に加え、全キャンバスをまとめてzip化する `GET /api/standalone/layout/export/all` がある(`zipfile` は標準ライブラリのみで実装、新規依存なし)— zip内の各ファイルは単一キャンバスExportと同じ形式なので、展開すれば既存のImport画面にそのまま読み込める。

**キャンバスの保存・リネーム・削除(`POST /api/layouts/save` / `layout_service`)**: レイアウト編集画面の「サーバーへ保存」ボタンは、Offline設定のインポートと同じく無警告上書きを避けるため確認フローを持つ — クライアントは編集開始時の元id(`originalId`、新規作成時は空文字)を毎回 `original_id` クエリパラメータとして送り、サーバー側は「送信されたidが元idと異なり、かつ既に別のキャンバスとして存在する」場合にのみ `409` + `needsConfirmation: true` を返す(元idのまま再保存する通常の編集操作では確認不要)。クライアントはこれを受けて `window.confirm()` を出し、承諾されたら `overwrite=true` を付けて再送する。id を変更して保存した場合は `layout_service.rename_layout()` が新idで保存した後に古いidのディレクトリを削除する(単純な新規作成ではなく、リネームとして扱う — 古いディレクトリが孤立して残ることを防ぐ)。キャンバス一覧(`/ui/layouts`)からの削除は `DELETE /ui/layouts/{layout_id}` で、`partials/layouts_grid.html` を再描画する(タグマッピングの削除と同じ hx-delete + hx-confirm パターン)。

**入力値の検証(`schemas/layout.py` / `schemas/tag_mapping.py`)**: `LayoutMeta.id`/`name` と `TagMapping.tag_id`/`api_field` は空文字(および空白のみ)を拒否する — 特にタグマッピングは `field_validator` で strip 後に空なら `ValueError` を送出する。`LayoutMeta.width`/`height` と `LayoutItem.w`/`h` は正の値のみ、`x`/`y` は0以上のみ許可する。`LayoutDefinition` には `model_validator(mode="after")` があり、同一キャンバス内で空でない `tagId` が複数の装置に重複していないかを検証する(空の `tagId` は複数あってもよい — 未設定のまま複数配置する編集途中の状態を壊さないため)。一方 `LayoutItem.tag_id`/`label` 自体は意図的に制約していない — キャンバス編集中にタグを後から割り当てる/ラベル未入力のまま置くという正当な中間状態があるため。この非対称性を「漏れ」と誤解してtag_idにも制約を追加しないこと。**新規キャンバス作成画面(`GET /ui/layouts/new`)の空プレースホルダーは `LayoutMeta.model_construct(id="", name="", ...)` で作る**(通常の `LayoutMeta(...)` ではバリデーションに引っかかって500になる) — 空文字を許すプレースホルダーが必要な箇所ではこのパターンを使うこと。

**タグマッピング**: `/ui/tag-mappings` は、外部APIのレスポンス項目名(将来のオンラインモード用)と内部 `tagId`、稼働中/停止中/アラームそれぞれに対応する生値を紐づけるCRUD画面。データは `data/sample/tag_mappings.json`(グローバル1ファイル、`tagId` で一意)。`services/tag_mapping_service.py` が `JsonStatusProvider` の `load_tag_mappings`/`save_tag_mappings` を呼ぶ。一覧・編集・削除は素のHTMX(クライアントJSなし)で実装している点に注意 — 編集ボタンは `hx-get` でフォームへ読み込み、作成/更新は「フォームをリセットした状態」を主レスポンス、テーブル全体の再描画を `hx-swap-oob` によるout-of-band swapとして同じレスポンスに同梱し1往復で両方を同期している。削除は `hx-delete` + `hx-confirm`。このマッピング自体は現時点でどこからも読み取られていない(オンラインモードの実データ取得が未実装のため) — 将来の `ApiStatusProvider` が生値→内部ステータスの変換に使う想定。一覧テーブルの「使用箇所」列は `tag_mapping_service.get_tag_usage()` が全キャンバスを走査して `tagId → ["キャンバス名 / 装置ラベル", ...]` を構築したもの(逆引き。マッピングの管理と実際の使用箇所を目視で突き合わせるための表示専用機能で、保存データにはこの結果を含めない)。

**Online設定 / 疎通確認**: `/ui/api-sources` は、将来のオンラインモード用マスターAPIの接続先URL・認証方式(なし/APIキー/Bearerトークン)を登録する画面。データは `data/sample/api_config.json`(`repositories/api_config_repository.py` 経由、`ApiConfigRepository`)。「接続テスト」ボタン(`POST /ui/api-sources/test`)は保存前のフォーム値に対して `services/api_test_service.py` が httpx で実際にHTTP GETを送り、成功/認証エラー(401/403)/エラー応答/タイムアウト/接続失敗を判定する — **成否の判定はHTTPステータスコードのみで行い、レスポンスボディの内容は見ない**(下記の理由による)。このスコープは意図的に「接続設定+疎通確認」までに限定しており、`operation_mode=online` にしてもダッシュボードのデータソースはまだ切り替わらない(常に `JsonStatusProvider` が使われる)。

**将来バックエンドAPIのレスポンス形式(重要・記録用)**: 実際にバックエンドAPIを呼ぶ段になったとき、レスポンスは `{"metadata": {...}, "response": [...]}` という envelope 形式で返ってくる想定。実データは常に `response` フィールドの中に入っている — `ApiStatusProvider` を実装する際は、HTTPレスポンスボディを受け取ったら `response` の中身を取り出してからPydanticモデルにマッピングすること。**`metadata` は見ない/判定に使わない** — 本プロジェクトの方針として、成功/失敗の判定はHTTPステータスコード(業界標準)だけで行う。上記の `api_test_service.py` の接続テストが `metadata` を無視してHTTPステータスのみで判定しているのはこの方針に合わせたもの。

**オンラインモード(データ取得自体は未実装)**: `repositories/layout_repository.py`、`repositories/status_repository.py`、`providers/api_status_provider.py`、`templates/partials/api_source_detail.html` は、将来のREST APIバックエンドからのレイアウト/ステータス取得用に予約された空のスキャフォールドファイル(`repositories/api_config_repository.py` は接続設定の永続化用として実装済み、上記参照)。`operation_mode`(`online`/`offline`、Cookie)はUIのトグルとしてすでに存在するが、まだプロバイダの挙動をこれで切り替える実装はない — 現状は常に `JsonStatusProvider` が使われる。オンラインモードのデータ取得を実装する際は、`JsonStatusProvider` と同じインターフェース(`list_layouts`、`load_layout`、`save_layout`、`load_status`、`save_status`)を持つAPIベースのプロバイダを追加し、サービス層で `operation_mode` により切り替えること — ルートやテンプレートが `services/` を飛び越えてプロバイダに直接触れることは絶対にしないこと。レスポンスの `response` envelope展開は上記の通り。

**設定**: `theme`、`operation_mode`、`default_layout_id`、`default_refresh_interval` はCookieとして永続化される(DBではない)— `routes/ui.py` でサーバー側検証を行い、値が不正/未設定の場合はデフォルトにフォールバックする。`operation_mode` はCookie未設定時のフォールバック先が`offline`(`_get_operation_mode`)であり、これは意図的なデフォルト — オンラインモードのデータ取得自体が未実装のため、初回アクセス時からオフラインの動作をそのまま体験できるようにしている。

**サンプルデータの規模(`data/sample/`)**: 意図的に最小限に絞っている — キャンバスは`line-a`(Line A)の1つだけで、装置は3台。このうち`tagId`が実際に設定されている(=稼働状態が表示される)のは1台(`run_state_a`/搬送機A、`status.json`・`tag_mappings.json`ともにこの1件のみ)、残り2台はあえて`tagId`を空にしてある — レイアウト編集でタグ未割り当てのまま装置を置いた状態(ダッシュボード上は`eq-box--unknown`のグレー表示)がどう見えるかを、サンプルデータの時点で示すため。装置やキャンバスを追加する目的でこのデータを増やすのは想定外の使い方ではないが、逆に「サンプルとして何を提示するか」を絞る目的でこの3点構成にしていることを踏まえ、意味なく数を増やして戻さないこと。

**エラーハンドリング(`main.py`)**: `StarletteHTTPException` と汎用 `Exception` の両方にハンドラを登録している。`/api/*` はJSON API なので常にJSON(`{"detail": ...}`)のまま維持し、`/ui/*` はHTMXリクエスト(`HX-Request` ヘッダーの有無で判定)かどうかで分岐する — フルページ遷移なら `pages/error.html`(実際のステータスコードで返す)、HTMX経由(部分スワップ)なら `partials/inline_error.html` を**ステータス200で**返す(htmxは既定で非2xxレスポンスをスワップしないため、意図的に200にしている。tag-mappingの重複エラーなど、既存のエラー表現パターンと合わせた形)。エラーメッセージはステータスコードのみから生成しており(`_error_message`)、`HTTPException(detail=...)` の文字列(英語・デバッグ用)をそのままユーザーに見せることはしない。汎用 `Exception` ハンドラは `core.log_modules.log_application` でスタックトレース付きログを出してから同じ分岐に乗せる。`TestClient` は既定で未処理例外を再送出してしまうため、この経路をテストする際は `TestClient(app, raise_server_exceptions=False)` を使うこと(`tests/test_error_handling.py` 参照)。

**フロントエンド**: サーバーレンダリングのJinja2 + HTMX、ビルドステップなし。`static/js/htmx.min.js` は(CDNではなく)意図的にベンダリングされている — 工場フロアのオフラインネットワーク環境という利用実態にも、このサンドボックスでCDNアクセスがブロックされている事情にも合致するため。ダッシュボードの自動更新(`static/js/dashboard.js`)は、宣言的な `hx-trigger` ではなく `setInterval` から `htmx.ajax()` を直接呼び出す形でHTMXを手動駆動している — 実行時に再設定可能なポーリング間隔を `hx-trigger` で実現しようとしたところ、実ブラウザでの検証で不安定だったため。レイアウト編集画面(`static/js/layout_editor.js`)のドラッグ/リサイズは生のポインターイベントで実装しており、ドラッグ用ライブラリは使用していない。

**ナビゲーション**: サイドバー(`templates/base.html`)にはトップレベルの項目が3つ — ダッシュボード、レイアウト編集、システム設定(設定ハブ)。設定ハブからは Online設定(`/ui/api-sources`)、タグマッピング(`/ui/tag-mappings`)、Offline設定(`/ui/standalone`)へリンクしている — これらは設定のサブページであり独立したナビ項目ではないため、アクティブ状態のハイライト判定は各ナビ項目の `also: [...]` リストで管理している(`{% set %}` が `{% for %}` ループ内で値を保持しないため、Jinjaの `namespace()` を使って実装)。

CSS(`static/css/main.css`)は `@media (prefers-color-scheme: dark)` と `:root[data-theme="dark"/"light"]` の両方でテーマを定義している(手動トグルがOS設定より優先)。加えて、装置キャンバス用に別途 `--diagram-*` トークン群を用意している — キャンバスはアプリのテーマに関わらず常に固定の白い「紙」背景であるため、その配色はライト/ダークのトークン体系には含めていない。
