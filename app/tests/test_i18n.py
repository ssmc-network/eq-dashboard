from starlette.requests import Request

from core.i18n import DEFAULT_LANGUAGE, LANGUAGE_CHOICES, TRANSLATIONS, get_language, translate


def _request_with_cookie_header(cookie_header: str) -> Request:
    scope = {
        "type": "http",
        "headers": [(b"cookie", cookie_header.encode())] if cookie_header else [],
    }
    return Request(scope)


def test_get_language_defaults_to_japanese_without_cookie() -> None:
    assert get_language(_request_with_cookie_header("")) == "ja"


def test_get_language_reads_cookie_value() -> None:
    assert get_language(_request_with_cookie_header("language=en")) == "en"


def test_get_language_falls_back_for_invalid_cookie_value() -> None:
    assert get_language(_request_with_cookie_header("language=fr")) == DEFAULT_LANGUAGE


def test_translate_returns_requested_language() -> None:
    assert translate("common.save", "ja") == "保存"
    assert translate("common.save", "en") == "Save"


def test_translate_formats_placeholders() -> None:
    assert translate("layout_editor.item_count", "en", count=3) == "3 equipment"


def test_translate_falls_back_to_key_for_unknown_key() -> None:
    assert translate("does.not.exist", "ja") == "does.not.exist"


def test_all_translation_entries_have_every_supported_language() -> None:
    missing = [key for key, entry in TRANSLATIONS.items() if not all(lang in entry for lang in LANGUAGE_CHOICES)]

    assert missing == []
