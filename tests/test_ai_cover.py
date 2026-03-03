"""
Tests for AI cover integration.
"""

import base64
import os
import tempfile


_SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAusB9Wv3p0sAAAAASUVORK5CYII="
)


def _create_sample_txt() -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一章 暮色之城\n\n")
        f.write("城市在雨夜中逐步显露它的秘密。\n\n")
        f.write("第二章 地下档案馆\n\n")
        f.write("主角发现被篡改的历史记录。\n")
        return f.name


def _create_png_file() -> str:
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
        f.write(base64.b64decode(_SAMPLE_PNG_BASE64))
        return f.name


def test_ai_cover_generated_when_no_cover_image(monkeypatch):
    from txt_to_epub import txt_to_epub, ParserConfig

    generated_cover_path = _create_png_file()
    set_cover_called = {'path': None}

    def fake_generate_ai_cover_image(*args, **kwargs):
        return generated_cover_path, True, {'total_calls': 1}, []

    def fake_set_cover_image(book, cover_image):
        set_cover_called['path'] = cover_image

    monkeypatch.setattr("txt_to_epub.core._generate_ai_cover_image", fake_generate_ai_cover_image)
    monkeypatch.setattr("txt_to_epub.core._set_cover_image", fake_set_cover_image)

    txt_file = _create_sample_txt()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(enable_ai_cover=True)
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='城市谜案',
            author='作者',
            config=config,
            show_progress=False
        )

        assert result['success'] is True
        assert result['ai_cover_generated'] is True
        assert set_cover_called['path'] == generated_cover_path
        assert result['ai_usage']['total_calls'] == 1
        assert not os.path.exists(generated_cover_path)
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_ai_cover_not_called_when_cover_image_provided(monkeypatch):
    from txt_to_epub import txt_to_epub, ParserConfig

    def fail_if_called(*args, **kwargs):
        raise AssertionError("AI cover generator should not be called when cover_image is provided")

    monkeypatch.setattr("txt_to_epub.core._generate_ai_cover_image", fail_if_called)

    txt_file = _create_sample_txt()
    manual_cover = _create_png_file()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(enable_ai_cover=True)
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='人工封面书',
            author='作者',
            cover_image=manual_cover,
            config=config,
            show_progress=False
        )
        assert result['success'] is True
        assert result['ai_cover_generated'] is False
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)
        if os.path.exists(manual_cover):
            os.unlink(manual_cover)
