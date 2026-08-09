from pathlib import Path

import pytest

from providers.json_status_provider import InvalidLayoutIdError, JsonStatusProvider, LayoutFileNotFoundError
from schemas.layout import LayoutDefinition, LayoutMeta


@pytest.fixture
def provider(tmp_path: Path) -> JsonStatusProvider:
    layouts_dir = tmp_path / "layouts"
    layouts_dir.mkdir()
    return JsonStatusProvider(
        layouts_dir=layouts_dir,
        status_path=tmp_path / "status.json",
        tag_mappings_path=tmp_path / "tag_mappings.json",
    )


def _layout(layout_id: str) -> LayoutDefinition:
    return LayoutDefinition(
        schemaVersion="1.0",
        layout=LayoutMeta.model_construct(id=layout_id, name="x", width=10, height=10),
        items=[],
    )


@pytest.mark.parametrize("evil_id", ["../evil", "../../etc/passwd", "..", "a/b"])
def test_load_layout_rejects_path_traversal_id(provider: JsonStatusProvider, evil_id: str) -> None:
    """layouts_dirの外にあるlayout.jsonを読み取れてはいけない(パストラバーサル対策)。"""
    with pytest.raises(LayoutFileNotFoundError):
        provider.load_layout(evil_id)


def test_load_layout_rejects_id_with_embedded_null_byte_cleanly(provider: JsonStatusProvider) -> None:
    """埋め込みNUL文字はPath.resolve()がValueErrorを送出する — 500ではなく
    他の不正なidと同じ「見つからない」扱いになることを確認する。"""
    with pytest.raises(LayoutFileNotFoundError):
        provider.load_layout("evil\x00id")


def test_save_layout_rejects_absolute_path_id(provider: JsonStatusProvider, tmp_path: Path) -> None:
    """絶対パスをidにすると`layouts_dir / id`がpathlibの仕様でlayouts_dirを無視して
    そのまま絶対パスになってしまう(実際に検証済みの脆弱性) — 拒否されることを確認する。"""
    outside = tmp_path / "outside"
    with pytest.raises(InvalidLayoutIdError):
        provider.save_layout(_layout(str(outside / "evil")))
    assert not outside.exists()


@pytest.mark.parametrize("evil_id", ["../evil", "../../etc/passwd", ".."])
def test_save_layout_rejects_relative_traversal_id(provider: JsonStatusProvider, evil_id: str) -> None:
    with pytest.raises(InvalidLayoutIdError):
        provider.save_layout(_layout(evil_id))


def test_delete_layout_is_noop_for_path_traversal_id_instead_of_deleting_outside(
    provider: JsonStatusProvider, tmp_path: Path
) -> None:
    """delete_layoutは(存在しないidの削除と同様に)不正なidも安全にno-opにする
    ——`shutil.rmtree`が意図しないディレクトリを削除してしまう実害を防ぐ。"""
    target = tmp_path / "must-survive"
    target.mkdir()
    (target / "file.txt").write_text("keep me", encoding="utf-8")

    provider.delete_layout(f"../{target.name}")

    assert target.exists()
    assert (target / "file.txt").read_text(encoding="utf-8") == "keep me"


def test_save_and_load_layout_round_trip_for_normal_id(provider: JsonStatusProvider) -> None:
    provider.save_layout(_layout("line-a"))
    loaded = provider.load_layout("line-a")
    assert loaded.layout.id == "line-a"
