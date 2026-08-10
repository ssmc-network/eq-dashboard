from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

LANGUAGE_CHOICES = ("ja", "en")
DEFAULT_LANGUAGE = "ja"

TRANSLATIONS: dict[str, dict[str, str]] = {
    # 共通・サイドナビ
    "app.name": {"ja": "EQ Dashboard", "en": "EQ Dashboard"},
    "app.tagline": {"ja": "設備稼働状態可視化", "en": "Equipment status visualization"},
    "nav.aria_label": {"ja": "画面ナビゲーション", "en": "Screen navigation"},
    "nav.dashboard": {"ja": "ダッシュボード", "en": "Dashboard"},
    "nav.layout_editor": {"ja": "レイアウト編集", "en": "Layout Editor"},
    "nav.settings": {"ja": "システム設定", "en": "Settings"},
    "nav.back_to_settings": {"ja": "← システム設定へ", "en": "← Back to Settings"},
    "nav.back_to_layouts": {"ja": "← キャンバス一覧へ", "en": "← Back to Canvas List"},
    "nav.toggle_sidebar": {"ja": "サイドバーの折りたたみ切替", "en": "Toggle sidebar"},
    "common.save": {"ja": "保存", "en": "Save"},
    "common.cancel": {"ja": "キャンセル", "en": "Cancel"},
    "common.edit": {"ja": "編集", "en": "Edit"},
    "common.delete": {"ja": "削除", "en": "Delete"},
    "common.unused": {"ja": "未使用", "en": "Unused"},
    "common.none_value": {"ja": "—", "en": "—"},
    # ダッシュボード
    "dashboard.title": {"ja": "ダッシュボード", "en": "Dashboard"},
    "dashboard.canvas_label": {"ja": "キャンバス", "en": "Canvas"},
    "dashboard.auto_refresh_label": {"ja": "自動更新", "en": "Auto refresh"},
    "dashboard.auto_refresh_off": {"ja": "なし", "en": "Off"},
    "dashboard.auto_refresh_on": {"ja": "自動更新", "en": "On"},
    "dashboard.interval_label": {"ja": "間隔(秒)", "en": "Interval (sec)"},
    "dashboard.refresh_status_on": {"ja": "{interval}秒ごとに更新", "en": "Refreshing every {interval}s"},
    "dashboard.refresh_status_off": {"ja": "自動更新なし", "en": "Auto refresh off"},
    "dashboard.updated_at_label": {"ja": "更新", "en": "Updated"},
    "dashboard.fullscreen_enter": {"ja": "全画面表示", "en": "Fullscreen"},
    "dashboard.fullscreen_exit": {"ja": "全画面終了", "en": "Exit Fullscreen"},
    "dashboard.fallback_notice": {
        "ja": "指定されたキャンバス「{requested}」が見つからなかったため、代わりに「{shown}」を表示しています。",
        "en": 'Canvas "{requested}" could not be found, showing "{shown}" instead.',
    },
    # 装置ステータス
    "status.running": {"ja": "稼働中", "en": "Running"},
    "status.stopped": {"ja": "停止中", "en": "Stopped"},
    "status.alarm": {"ja": "アラーム", "en": "Alarm"},
    "status.unknown": {"ja": "不明", "en": "Unknown"},
    # キャンバス一覧
    "layouts_list.title": {"ja": "キャンバス一覧", "en": "Canvas List"},
    "layouts_list.description": {
        "ja": "編集するキャンバスを選択するか、新しいキャンバスを作成します。",
        "en": "Select a canvas to edit, or create a new one.",
    },
    "layouts_list.delete_confirm": {
        "ja": "キャンバス「{name}」を削除しますか?この操作は取り消せません。",
        "en": 'Delete canvas "{name}"? This action cannot be undone.',
    },
    "layouts_list.new_canvas": {"ja": "新規キャンバス", "en": "New Canvas"},
    "layouts_list.new_canvas_desc": {"ja": "空のキャンバスを新しく作成します。", "en": "Create a new, empty canvas."},
    # レイアウト編集
    "layout_editor.title_new": {"ja": "新規キャンバス", "en": "New Canvas"},
    "layout_editor.title_suffix": {"ja": "編集", "en": "Edit"},
    "layout_editor.heading_edit_suffix": {"ja": "を編集", "en": "- Edit"},
    "layout_editor.field_id": {"ja": "ID", "en": "ID"},
    "layout_editor.field_name": {"ja": "名前", "en": "Name"},
    "layout_editor.field_name_placeholder": {"ja": "1F 組立ライン", "en": "1F Assembly Line"},
    "layout_editor.field_width": {"ja": "幅", "en": "Width"},
    "layout_editor.field_height": {"ja": "高さ", "en": "Height"},
    "layout_editor.zoom_out": {"ja": "縮小", "en": "Zoom out"},
    "layout_editor.zoom_in": {"ja": "拡大", "en": "Zoom in"},
    "layout_editor.zoom_reset": {"ja": "100%", "en": "100%"},
    "layout_editor.add_item": {"ja": "+ 装置を追加", "en": "+ Add Equipment"},
    "layout_editor.save_to_server": {"ja": "サーバーへ保存", "en": "Save to Server"},
    "layout_editor.download_json": {"ja": "JSONをダウンロード", "en": "Download JSON"},
    "layout_editor.item_count": {"ja": "{count}件の装置", "en": "{count} equipment"},
    "layout_editor.panel_empty": {"ja": "装置をクリックすると編集できます。", "en": "Click an item to edit it."},
    "layout_editor.field_label": {"ja": "ラベル", "en": "Label"},
    "layout_editor.field_tag_id": {"ja": "タグID", "en": "Tag ID"},
    "layout_editor.field_x": {"ja": "X", "en": "X"},
    "layout_editor.field_y": {"ja": "Y", "en": "Y"},
    "layout_editor.field_w": {"ja": "幅", "en": "W"},
    "layout_editor.field_h": {"ja": "高さ", "en": "H"},
    "layout_editor.delete_item": {"ja": "この装置を削除", "en": "Delete This Item"},
    "layout_editor.new_item_label": {"ja": "新規装置", "en": "New Equipment"},
    "layout_editor.no_label": {"ja": "(ラベル未設定)", "en": "(no label)"},
    "layout_editor.saving": {"ja": "保存中...", "en": "Saving..."},
    "layout_editor.save_ok": {"ja": "✓ サーバーに保存しました({id})", "en": "✓ Saved to server ({id})"},
    "layout_editor.save_failed": {"ja": "✕ 保存に失敗しました: {errors}", "en": "✕ Save failed: {errors}"},
    "layout_editor.save_cancelled": {"ja": "保存をキャンセルしました。", "en": "Save cancelled."},
    "layout_editor.network_error": {"ja": "✕ 通信エラーが発生しました。", "en": "✕ A network error occurred."},
    "layout_editor.id_name_required": {
        "ja": "ID と 名前 を入力してください。",
        "en": "Please enter an ID and a name.",
    },
    "layout_editor.overwrite_confirm": {
        "ja": "id「{id}」は既存のキャンバス「{name}」です。上書きしますか?",
        "en": 'ID "{id}" already belongs to canvas "{name}". Overwrite it?',
    },
    # システム設定
    "settings.title": {"ja": "システム設定", "en": "Settings"},
    "settings.description": {
        "ja": "動作モード・テーマ・ダッシュボードの既定動作を設定します。",
        "en": "Configure operation mode, theme, and default dashboard behavior.",
    },
    "settings.operation_mode_label": {"ja": "動作モード", "en": "Operation Mode"},
    "settings.operation_mode_offline": {"ja": "オフライン", "en": "Offline"},
    "settings.operation_mode_online": {"ja": "オンライン", "en": "Online"},
    "settings.theme_label": {"ja": "テーマ", "en": "Theme"},
    "settings.theme_system": {"ja": "システム(自動)", "en": "System (auto)"},
    "settings.theme_light": {"ja": "ライト", "en": "Light"},
    "settings.theme_dark": {"ja": "ダーク", "en": "Dark"},
    "settings.language_label": {"ja": "言語", "en": "Language"},
    "settings.language_ja": {"ja": "日本語", "en": "Japanese"},
    "settings.language_en": {"ja": "英語", "en": "English"},
    "settings.default_layout_label": {"ja": "デフォルトキャンバス", "en": "Default Canvas"},
    "settings.default_refresh_label": {
        "ja": "ダッシュボードの初期更新間隔(秒)",
        "en": "Default Dashboard Refresh Interval (sec)",
    },
    "settings.related_settings": {"ja": "関連設定", "en": "Related Settings"},
    "settings.api_sources_title": {"ja": "Online設定", "en": "Online Settings"},
    "settings.api_sources_desc": {
        "ja": "オンラインモードで使用するAPI接続先・認証・エンドポイントを管理します。",
        "en": "Manage the API endpoint, authentication, and connection settings used in online mode.",
    },
    "settings.tag_mappings_title": {"ja": "タグマッピング", "en": "Tag Mapping"},
    "settings.tag_mappings_desc": {
        "ja": "APIレスポンス項目と内部タグを紐づけます。",
        "en": "Link API response fields to internal tags.",
    },
    "settings.standalone_title": {"ja": "Offline設定", "en": "Offline Settings"},
    "settings.standalone_desc": {
        "ja": "オフラインモードで使用するレイアウト・状態JSONのexport/importを行います。",
        "en": "Export/import the layout and status JSON used in offline mode.",
    },
    # Online設定(API接続)
    "api_settings.title": {"ja": "Online設定", "en": "Online Settings"},
    "api_settings.description": {
        "ja": "オンラインモードで使用するマスターAPIの接続先、認証方式を管理します。",
        "en": "Manage the master API endpoint and authentication method used in online mode.",
    },
    "api_settings.current_mode": {"ja": "現在の動作モード: {mode}", "en": "Current mode: {mode}"},
    "api_settings.base_url_label": {"ja": "接続先URL", "en": "Endpoint URL"},
    "api_settings.auth_type_label": {"ja": "認証方式", "en": "Authentication"},
    "api_settings.auth_none": {"ja": "なし", "en": "None"},
    "api_settings.auth_api_key": {"ja": "APIキー", "en": "API Key"},
    "api_settings.auth_bearer": {"ja": "Bearerトークン", "en": "Bearer Token"},
    "api_settings.api_key_header_label": {"ja": "APIキーのヘッダー名", "en": "API Key Header Name"},
    "api_settings.credential_label": {"ja": "APIキー / トークン", "en": "API Key / Token"},
    "api_settings.test_connection": {"ja": "接続テスト", "en": "Test Connection"},
    "api_test.base_url_missing": {"ja": "接続先URLが設定されていません。", "en": "No endpoint URL is configured."},
    "api_test.timeout": {"ja": "接続がタイムアウトしました。", "en": "The connection timed out."},
    "api_test.connection_failed": {"ja": "接続に失敗しました: {error}", "en": "Connection failed: {error}"},
    "api_test.auth_failed": {
        "ja": "認証に失敗しました(HTTP {status})。",
        "en": "Authentication failed (HTTP {status}).",
    },
    "api_test.error_response": {
        "ja": "接続はできましたが、エラー応答でした(HTTP {status})。",
        "en": "Connected, but received an error response (HTTP {status}).",
    },
    "api_test.success": {
        "ja": "接続に成功しました(HTTP {status}, {elapsed}ms)。",
        "en": "Connection succeeded (HTTP {status}, {elapsed}ms).",
    },
    # タグマッピング(APIから取得して作成)
    "api_discovery.invalid_json": {
        "ja": "レスポンスがJSON形式ではありません。",
        "en": "The response is not valid JSON.",
    },
    "api_discovery.no_fields": {
        "ja": "取得したデータから項目が見つかりませんでした。",
        "en": "No fields were found in the retrieved data.",
    },
    "api_discovery.section_title": {"ja": "APIから取得して作成", "en": "Create from API Data"},
    "api_discovery.section_desc": {
        "ja": "Online設定に保存された接続先へアクセスし、取得できた項目から複数のマッピングをまとめて作成します。",
        "en": "Connects to the endpoint saved in Online Settings and bulk-creates mappings from the fields found.",
    },
    "api_discovery.fetch_button": {"ja": "APIから取得", "en": "Fetch from API"},
    "api_discovery.sample_value_column": {"ja": "サンプル値", "en": "Sample Value"},
    "api_discovery.create_selected": {"ja": "選択した項目からマッピングを作成", "en": "Create Mappings from Selected"},
    "api_discovery.truncated_notice": {
        "ja": "項目数が多いため、先頭{limit}件のみ表示しています。",
        "en": "Showing only the first {limit} fields because there were too many.",
    },
    "api_discovery.bulk_result": {
        "ja": "{created}件作成しました({skipped}件は既存のためスキップ)。",
        "en": "Created {created} mapping(s) ({skipped} skipped as already existing).",
    },
    # タグマッピング
    "tag_mappings.title": {"ja": "タグマッピング", "en": "Tag Mapping"},
    "tag_mappings.description": {
        "ja": (
            "外部APIのレスポンス項目名と内部タグ(tagId)、稼働中/停止中/アラームそれぞれに対応する生値を紐づけます。"
            "オンラインモードでバックエンドAPIと接続する際にこの対応表を使用します。"
        ),
        "en": (
            "Link external API response field names to internal tags (tagId), and the raw values for "
            "running/stopped/alarm. This mapping is used when connecting to the backend API in online mode."
        ),
    },
    "tag_mappings.form_edit_title": {"ja": "マッピングを編集", "en": "Edit Mapping"},
    "tag_mappings.form_add_title": {"ja": "マッピングを追加", "en": "Add Mapping"},
    "tag_mappings.field_api_field": {"ja": "APIフィールド", "en": "API Field"},
    "tag_mappings.field_running_value": {"ja": "稼働中の値", "en": "Running Value"},
    "tag_mappings.field_stopped_value": {"ja": "停止中の値", "en": "Stopped Value"},
    "tag_mappings.field_alarm_value": {"ja": "アラームの値", "en": "Alarm Value"},
    "tag_mappings.update": {"ja": "更新", "en": "Update"},
    "tag_mappings.add": {"ja": "追加", "en": "Add"},
    "tag_mappings.usage_column": {"ja": "使用箇所", "en": "Used In"},
    "tag_mappings.delete_confirm": {
        "ja": "「{tag_id}」のマッピングを削除しますか?",
        "en": 'Delete the mapping for "{tag_id}"?',
    },
    "tag_mappings.empty": {"ja": "マッピングが登録されていません。", "en": "No mappings registered."},
    "tag_mappings.already_registered": {
        "ja": "tagId「{tag_id}」は既に登録されています。",
        "en": 'tagId "{tag_id}" is already registered.',
    },
    "tag_mappings.blank_value_error": {
        "ja": "tagIdとAPIフィールドは必須です(空白のみは不可)。",
        "en": "tagId and API field are required (cannot be blank).",
    },
    # Offline設定(スタンドアロン)
    "standalone.title": {"ja": "Offline設定", "en": "Offline Settings"},
    "standalone.description": {
        "ja": "オフラインモードで使用するレイアウト・状態JSONのexport/importを行います。",
        "en": "Export/import the layout and status JSON used in offline mode.",
    },
    "standalone.current_mode": {"ja": "現在の動作モード: {mode}", "en": "Current mode: {mode}"},
    "standalone.data_source_notice": {
        "ja": (
            "装置状態はサーバー上のサンプルJSON(layout.json / status.json)から取得しています。"
            "外部REST APIに接続するオンラインモードは、バックエンドとの接続実装後に対応予定です。"
        ),
        "en": (
            "Equipment status is read from the sample JSON files on the server (layout.json / status.json). "
            "Online mode, which connects to an external REST API, will be supported once the backend "
            "integration is implemented."
        ),
    },
    "standalone.persistence_notice": {
        "ja": (
            "Import・保存した内容はコンテナ内のファイルに直接書き込まれ、ブラウザをリロードしても消えません。"
            "ただし永続化ボリュームは使用していないため、コンテナを再作成すると初期データに戻ります"
            "(将来のオンライン運用が本命のため)。"
        ),
        "en": (
            "Imported or saved content is written directly to files inside the container and survives a "
            "browser reload. However, no persistent volume is used, so recreating the container resets it to "
            "the initial sample data (online mode is the intended long-term setup)."
        ),
    },
    "standalone.layout_json_title": {"ja": "レイアウトJSON", "en": "Layout JSON"},
    "standalone.layout_json_desc": {
        "ja": "キャンバスごとの図形配置(schemaVersion / layout / items)。",
        "en": "Per-canvas shape layout (schemaVersion / layout / items).",
    },
    "standalone.export_heading": {"ja": "Export", "en": "Export"},
    "standalone.import_heading": {"ja": "Import", "en": "Import"},
    "standalone.download": {"ja": "ダウンロード", "en": "Download"},
    "standalone.download_all_zip": {
        "ja": "全キャンバスをまとめてダウンロード(.zip)",
        "en": "Download All Canvases (.zip)",
    },
    "standalone.validate": {"ja": "検証", "en": "Validate"},
    "standalone.status_json_title": {"ja": "状態JSON", "en": "Status JSON"},
    "standalone.status_json_desc": {
        "ja": (
            "全キャンバス共通の装置状態スナップショット(schemaVersion / generatedAt / statuses)。"
            "キャンバスごとではなく、装置のタグID単位で1つに集約しています。"
        ),
        "en": (
            "A single equipment-status snapshot shared across all canvases (schemaVersion / generatedAt / "
            "statuses), keyed by equipment tag ID rather than per canvas."
        ),
    },
    "standalone.download_status_json": {"ja": "status.jsonをダウンロード", "en": "Download status.json"},
    "import_result.kind_layout": {"ja": "レイアウト", "en": "layout"},
    "import_result.kind_status": {"ja": "状態", "en": "status"},
    "import_result.revalidation_filename": {"ja": "(保存時の再検証)", "en": "(re-validated on save)"},
    "import_result.layout_saved_overwrite": {
        "ja": "✓ キャンバス「{name}」({id})を上書き保存しました。",
        "en": '✓ Canvas "{name}" ({id}) was overwritten and saved.',
    },
    "import_result.layout_saved_new": {
        "ja": "✓ キャンバス「{name}」({id})を新規作成しました。",
        "en": '✓ Canvas "{name}" ({id}) was created.',
    },
    "import_result.status_saved": {
        "ja": "✓ 状態JSON(status.json)をサーバーに上書き保存しました。({count}件)",
        "en": "✓ status.json was saved to the server, overwriting the previous content. ({count} entries)",
    },
    "import_result.valid_json": {
        "ja": "✓ {filename} は正しい{kind}JSONです。",
        "en": "✓ {filename} is a valid {kind} JSON.",
    },
    "import_result.invalid_json": {
        "ja": "✕ {filename} は無効な{kind}JSONです。",
        "en": "✕ {filename} is not a valid {kind} JSON.",
    },
    "import_result.layout_exists_notice": {
        "ja": "id {id} は既存のキャンバスです。上書きされます。",
        "en": "ID {id} already belongs to an existing canvas. It will be overwritten.",
    },
    "import_result.layout_new_notice": {
        "ja": "id {id} は新規キャンバスとして作成されます。",
        "en": "ID {id} will be created as a new canvas.",
    },
    "import_result.status_overwrite_notice": {
        "ja": "サーバー上の status.json({count}件)を上書きします。",
        "en": "This will overwrite status.json on the server ({count} entries).",
    },
    "import_result.confirm_save": {"ja": "この内容で保存", "en": "Save This"},
    "import.json_parse_error": {"ja": "JSONの解析に失敗しました: {error}", "en": "Failed to parse JSON: {error}"},
    # エラーページ
    "error.page_title": {"ja": "エラー", "en": "Error"},
    "error.not_found": {"ja": "ページが見つかりませんでした。", "en": "The page could not be found."},
    "error.server_error": {"ja": "予期しないエラーが発生しました。", "en": "An unexpected error occurred."},
    "error.generic": {"ja": "エラーが発生しました。", "en": "An error occurred."},
    "error.back_to_dashboard": {"ja": "ダッシュボードへ戻る", "en": "Back to Dashboard"},
}


def get_language(request: Request) -> str:
    lang = request.cookies.get("language", DEFAULT_LANGUAGE)
    return lang if lang in LANGUAGE_CHOICES else DEFAULT_LANGUAGE


def translate(key: str, lang: str, **kwargs: object) -> str:
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get(DEFAULT_LANGUAGE, key))
    return text.format(**kwargs) if kwargs else text


@pass_context
def _translate_in_template(context: dict, key: str, **kwargs: object) -> str:
    lang = get_language(context["request"])
    return translate(key, lang, **kwargs)


def register_i18n_globals(templates: Jinja2Templates) -> None:
    """各Jinja2Templatesインスタンスは独自のEnvironmentを持つため、
    routes/ui.pyとmain.pyのそれぞれで個別に呼び出す必要がある。"""
    templates.env.globals["t"] = _translate_in_template
    templates.env.globals["get_language"] = get_language
