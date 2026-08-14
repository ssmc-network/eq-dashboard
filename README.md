# EQ Dashboard

工場設備の稼働状態をフロアマップ風のキャンバス上に可視化する、FastAPI + HTMX 製のダッシュボードです。

装置の図形は固定された白いキャンバス上に直接描画され、稼働状態(稼働中 / 停止中 / アラーム)に応じて色分けされます。レイアウトはドラッグ&リサイズで編集可能で、名前付きの複数キャンバス(階層ごと・部屋ごとなど)にも対応しています。

データはローカルのJSONファイル(オフライン/スタンドアロンモード)、または将来的には外部バックエンドのREST API(オンラインモード)から取得する想定です。**本アプリはDBに直接アクセスしません** — DBへのアクセスは常に外部バックエンドAPIの向こう側に置く設計です。

## 主な機能

- **ダッシュボード** — フロアマップ上に装置を配置し、稼働状態を色で可視化。自動更新、複数キャンバスの切り替えに対応
- **レイアウト編集** — 装置図形のドラッグ&リサイズ、追加/削除、サーバーへの保存
- **タグマッピング** — 外部APIのレスポンス項目名と内部タグ(tagId)、稼働中/停止中/アラームの生値を紐づけるCRUD画面
- **Online設定** — オンラインモード用マスターAPIの接続先・認証方式の登録、接続テスト
- **Offline設定** — レイアウト/状態JSONのインポート・エクスポート(検証→確認保存の2段階)
- **システム設定** — テーマ(ライト/ダーク)、動作モード(オンライン/オフライン)、デフォルトキャンバス、自動更新間隔
- **JSON形式ログ出力** — アプリケーションログ・uvicornログを構造化JSON形式で出力

## 技術スタック

- **バックエンド**: FastAPI, Pydantic v2, httpx
- **フロントエンド**: Jinja2 (サーバーレンダリング) + HTMX(ビルドステップなし、CDNではなくローカルにベンダリング)
- **パッケージ管理**: Poetry
- **Lint / 型チェック / テスト**: Ruff, mypy, pytest
- **コンテナ**: Docker(UBI9ベースのマルチステージビルド)

## セットアップ

Pythonのコマンドはすべて `app/` ディレクトリから実行します。

```bash
cd app
poetry install --with dev   # 依存関係をインストール(lint/型チェック/テストツールも含む)
```

### 開発サーバーの起動

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-config log_config.yaml
```

`http://localhost:8000` でダッシュボードにアクセスできます。

### Lint / フォーマット / 型チェック / テスト

```bash
poetry run ruff check .        # lint
poetry run ruff format .       # フォーマット
poetry run mypy .              # 型チェック
poetry run pytest              # テスト
```

## Dockerでの起動

Compose Specification準拠のファイル名(`compose.yaml` / `compose.override.yaml` / `compose.production.yaml`)を使用しています。

```bash
# 開発用(devターゲット、compose.override.yamlを使用)
docker compose up -d

# 本番相当の動作確認用(prdターゲット、ポート8888)
docker compose -f compose.yaml -f compose.production.yaml up -d --build
```

## ディレクトリ構成

```
.
├── Dockerfile                  # UBI9ベースのマルチステージビルド (base → dependencies → dev/prd)
├── compose.yaml / compose.override.yaml / compose.production.yaml
├── app/                        # Poetryプロジェクトのルート
│   ├── main.py                 # FastAPIアプリのエントリーポイント
│   ├── routes/                 # HTMXページ用ルート(ui.py) / JSON API(api.py)
│   ├── services/                # ビジネスロジック
│   ├── providers/ , repositories/  # データアクセス層(現状はJSONファイル)
│   ├── schemas/                 # Pydanticモデル
│   ├── core/                    # 設定・ロギング
│   ├── templates/ , static/     # Jinja2テンプレート・CSS/JS
│   └── data/sample/              # サンプルデータ(レイアウト/状態/タグマッピング/API設定)
└── .github/workflows/            # CI/CD (test.yaml, build.yaml)
```

## ブランチ運用

GitHub Flow(長期ブランチは `main` のみ)を採用しています。開発ブランチ(`feature/...`、`claude/...`など)を `main` から切り、PRで `main` へ直接マージします。バージョンの公開は `main` へのマージとは別に、`vX.Y.Z` 形式のgitタグを切ったタイミングで行います。

詳細な設計・アーキテクチャ上の意思決定については [`CLAUDE.md`](./CLAUDE.md) を参照してください。
