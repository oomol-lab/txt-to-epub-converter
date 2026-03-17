"""
Tests for AI chapter illustration integration.
"""

import base64
import os
import tempfile
import zipfile


_SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAusB9Wv3p0sAAAAASUVORK5CYII="
)


def _create_sample_txt() -> str:
    repeated = "这是一段用于插图生成测试的章节正文。" * 40
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一章 初入乱世\n\n")
        f.write(repeated + "\n\n")
        f.write("第二章 风云再起\n\n")
        f.write(repeated + "\n\n")
        f.write("第三章 江山如画\n\n")
        f.write(repeated + "\n")
        return f.name


def _create_png_file() -> str:
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
        f.write(base64.b64decode(_SAMPLE_PNG_BASE64))
        return f.name


def test_ai_illustrations_generated_and_embedded(monkeypatch):
    from txt_to_epub import ParserConfig, txt_to_epub

    generated_paths = []
    call_counter = {"count": 0}

    def fake_generate_ai_chapter_illustration(*args, **kwargs):
        call_counter["count"] += 1
        image_path = _create_png_file()
        generated_paths.append(image_path)
        return image_path, True, {"total_calls": 1}, []

    monkeypatch.setattr("txt_to_epub.core._generate_ai_chapter_illustration", fake_generate_ai_chapter_illustration)

    txt_file = _create_sample_txt()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(
            enable_ai_illustrations=True,
            ai_illustration_min_chapter_chars=20,
            ai_illustration_chapter_interval=1,
            ai_illustration_max_images_per_book=2
        )
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='插图测试书',
            author='测试作者',
            config=config,
            show_progress=False
        )

        assert result["success"] is True
        assert result["ai"]["illustration"]["generated_count"] == 2
        assert call_counter["count"] == 2
        assert result["ai"]["usage"]["total_calls"] >= 2
        assert result["ai"]["illustration"]["failed_count"] == 0
        assert len(result["ai"]["illustration"]["chapter_results"]) == 2
        assert all(item["status"] == "generated" for item in result["ai"]["illustration"]["chapter_results"])

        with zipfile.ZipFile(epub_file, "r") as zf:
            names = zf.namelist()
            image_files = [name for name in names if "illustration_" in name and name.endswith((".png", ".jpg", ".webp", ".gif"))]
            assert len(image_files) == 2

        for path in generated_paths:
            assert not os.path.exists(path)
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_ai_illustrations_not_called_when_disabled(monkeypatch):
    from txt_to_epub import ParserConfig, txt_to_epub

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Illustration generator should not be called when disabled")

    monkeypatch.setattr("txt_to_epub.core._generate_ai_chapter_illustration", fail_if_called)

    txt_file = _create_sample_txt()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(enable_ai_illustrations=False)
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='无插图测试书',
            author='测试作者',
            config=config,
            show_progress=False
        )

        assert result["success"] is True
        assert result["ai"]["illustration"]["generated_count"] == 0
        assert result["ai"]["illustration"]["attempted_count"] == 0
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_ai_illustration_continuity_guide_is_passed(monkeypatch):
    from txt_to_epub import ParserConfig, txt_to_epub

    captured = {
        "guide": None,
        "focus": None,
    }
    generated_paths = []

    def fake_generate_continuity(*args, **kwargs):
        return (
            {
                "style_bible": "写实油画质感，低饱和金棕色调，统一镜头语言。",
                "setting_bible": "明代城市与宫廷环境，避免现代元素。",
                "characters": [
                    {"name": "主角", "appearance": "青色直裾、瘦削脸型、佩木簪", "identity": "书生"}
                ],
                "negative_constraints": ["不要现代服饰", "不要科幻元素"]
            },
            True,
            {"total_calls": 1},
            []
        )

    def fake_generate_ai_chapter_illustration(*args, **kwargs):
        captured["guide"] = kwargs.get("continuity_guide")
        captured["focus"] = kwargs.get("character_focus")
        image_path = _create_png_file()
        generated_paths.append(image_path)
        return image_path, True, {"total_calls": 1}, []

    monkeypatch.setattr("txt_to_epub.core._generate_ai_illustration_continuity_guide", fake_generate_continuity)
    monkeypatch.setattr("txt_to_epub.core._generate_ai_chapter_illustration", fake_generate_ai_chapter_illustration)

    txt_file = _create_sample_txt()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(
            enable_ai_illustrations=True,
            ai_illustration_min_chapter_chars=20,
            ai_illustration_chapter_interval=1,
            ai_illustration_max_images_per_book=1
        )
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='连续性测试书',
            author='测试作者',
            config=config,
            show_progress=False
        )

        assert result["success"] is True
        assert result["ai"]["illustration"]["continuity_generated"] is True
        assert captured["guide"] is not None
        assert captured["guide"]["characters"][0]["name"] == "主角"
        assert captured["focus"] == ["主角"]
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)
        for path in generated_paths:
            if os.path.exists(path):
                os.unlink(path)


def test_first_chapter_always_gets_illustration():
    from txt_to_epub import ParserConfig
    from txt_to_epub.core import _should_generate_chapter_illustration

    config = ParserConfig(
        enable_ai_illustrations=True,
        ai_illustration_min_chapter_chars=1000,
        ai_illustration_chapter_interval=99,
        ai_illustration_max_images_per_book=2
    )

    # First chapter should be forced on, even if below min chars and using low-density interval.
    assert _should_generate_chapter_illustration(
        chapter_index=1,
        chapter_text="很短。",
        generated_count=0,
        config=config
    ) is True

    # Other chapters still follow regular interval strategy.
    assert _should_generate_chapter_illustration(
        chapter_index=2,
        chapter_text="这是一段足够长的章节内容。" * 100,
        generated_count=1,
        config=config
    ) is False


def test_ai_illustration_density_preset_low():
    from txt_to_epub import ParserConfig
    from txt_to_epub.core import _should_generate_chapter_illustration

    config = ParserConfig(
        enable_ai_illustrations=True,
        ai_illustration_density="低"
    )

    policy = config.get_ai_illustration_policy()
    assert policy["max_images_per_book"] == 4
    assert policy["chapter_interval"] == 10
    assert policy["min_chapter_chars"] == 3500

    # Chapter 2 fails because low density requires a long interval.
    assert _should_generate_chapter_illustration(
        chapter_index=2,
        chapter_text="这是一段足够长的章节内容。" * 500,
        generated_count=1,
        config=config
    ) is False

    # Chapter 11 matches interval (1, 11, 21...) and should pass with enough content.
    assert _should_generate_chapter_illustration(
        chapter_index=11,
        chapter_text="这是一段足够长的章节内容。" * 500,
        generated_count=1,
        config=config
    ) is True


def test_ai_illustration_density_alias_ultra():
    from txt_to_epub import ParserConfig

    config = ParserConfig(ai_illustration_density="ultra")
    assert config.get_ai_illustration_density() == "超高"

    policy = config.get_ai_illustration_policy()
    assert policy["max_images_per_book"] == 24
    assert policy["chapter_interval"] == 1
    assert policy["min_chapter_chars"] == 600


def test_ai_illustration_english_min_chars_scaled():
    """English min_chapter_chars should be multiplied by _ENGLISH_CHARS_PER_WORD
    so that the density preset yields a semantically equivalent illustration
    cadence for English text (word-count level, not raw character count)."""
    from txt_to_epub import ParserConfig
    from txt_to_epub.core import _ENGLISH_CHARS_PER_WORD, _should_generate_chapter_illustration

    # 中 preset: min_chapter_chars=2000, chapter_interval=6
    config = ParserConfig(
        enable_ai_illustrations=True,
        ai_illustration_density="中",
    )

    # A Chinese chapter with 2000 chars should pass.
    assert _should_generate_chapter_illustration(
        chapter_index=7,
        chapter_text="这是一段足够长的章节内容。" * 170,  # ~2040 chars
        generated_count=1,
        config=config,
        language="chinese",
    ) is True

    # An English chapter with only 2000 chars should NOT pass (below scaled threshold).
    short_english = "The hero walked through the dark forest. " * 48  # ~1968 chars
    assert len(short_english.strip()) < 2000 * _ENGLISH_CHARS_PER_WORD
    assert _should_generate_chapter_illustration(
        chapter_index=7,
        chapter_text=short_english,
        generated_count=1,
        config=config,
        language="english",
    ) is False

    # An English chapter with enough chars (≥ 2000 * 5 = 10000) should pass.
    long_english = "The hero walked through the dark forest. " * 250  # ~10250 chars
    assert len(long_english.strip()) >= 2000 * _ENGLISH_CHARS_PER_WORD
    assert _should_generate_chapter_illustration(
        chapter_index=7,
        chapter_text=long_english,
        generated_count=1,
        config=config,
        language="english",
    ) is True
