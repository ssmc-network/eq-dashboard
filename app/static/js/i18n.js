(function () {
  const TRANSLATIONS = {
    "layout_editor.item_count": { ja: "{count}件の装置", en: "{count} equipment" },
    "layout_editor.new_item_label": { ja: "新規装置", en: "New Equipment" },
    "layout_editor.no_label": { ja: "(ラベル未設定)", en: "(no label)" },
    "layout_editor.saving": { ja: "保存中...", en: "Saving..." },
    "layout_editor.save_ok": { ja: "✓ サーバーに保存しました({id})", en: "✓ Saved to server ({id})" },
    "layout_editor.save_failed": { ja: "✕ 保存に失敗しました: {errors}", en: "✕ Save failed: {errors}" },
    "layout_editor.save_cancelled": { ja: "保存をキャンセルしました。", en: "Save cancelled." },
    "layout_editor.network_error": { ja: "✕ 通信エラーが発生しました。", en: "✕ A network error occurred." },
    "layout_editor.id_name_required": { ja: "ID と 名前 を入力してください。", en: "Please enter an ID and a name." },
    "layout_editor.overwrite_confirm": {
      ja: 'id「{id}」は既存のキャンバス「{name}」です。上書きしますか?',
      en: 'ID "{id}" already belongs to canvas "{name}". Overwrite it?',
    },
    "dashboard.refresh_status_on": { ja: "{interval}秒ごとに更新", en: "Refreshing every {interval}s" },
    "dashboard.refresh_status_off": { ja: "自動更新なし", en: "Auto refresh off" },
    "dashboard.fullscreen_enter": { ja: "全画面表示", en: "Fullscreen" },
    "dashboard.fullscreen_exit": { ja: "全画面終了", en: "Exit Fullscreen" },
  };

  function t(key, params) {
    const lang = document.documentElement.lang === "en" ? "en" : "ja";
    const entry = TRANSLATIONS[key];
    if (!entry) return key;
    let text = entry[lang] || entry.ja;
    if (params) {
      Object.keys(params).forEach((name) => {
        text = text.replace(`{${name}}`, params[name]);
      });
    }
    return text;
  }

  window.t = t;
})();
