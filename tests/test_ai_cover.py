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
        assert result['ai']['cover']['generated'] is True
        assert set_cover_called['path'] == generated_cover_path
        assert result['ai']['usage']['total_calls'] == 1
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
        assert result['ai']['cover']['generated'] is False
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)
        if os.path.exists(manual_cover):
            os.unlink(manual_cover)


def test_cover_generator_prefers_fusion_for_llm_oomol_base_url():
    from txt_to_epub.ai.cover_generator import CoverGenerator

    generator = CoverGenerator(
        api_key="sk-demo",
        base_url="https://llm.oomol.com/",
        model="custom-image-model"
    )

    assert generator._should_use_fusion_api() is True


def test_cover_generator_accepts_custom_fusion_image_api_url(monkeypatch):
    from txt_to_epub.ai.cover_generator import CoverGenerator

    captured = {"post_url": None}

    class FakePostResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"data": [{"url": "https://example.com/generated.png"}]}

    class FakeGetResponse:
        content = b"png-bytes"

        @staticmethod
        def raise_for_status():
            return None

    def fake_post(url, **kwargs):
        captured["post_url"] = url
        return FakePostResponse()

    def fake_get(url, **kwargs):
        return FakeGetResponse()

    monkeypatch.setattr("txt_to_epub.ai.cover_generator.requests.post", fake_post)
    monkeypatch.setattr("txt_to_epub.ai.cover_generator.requests.get", fake_get)

    generator = CoverGenerator(
        api_key="api-demo",
        model="google/gemini-2.5-flash-image",
        fusion_image_api_url="https://example.com/custom-fusion-endpoint"
    )

    result = generator.generate_cover(title="测试书名", author="作者")

    assert result["success"] is True
    assert captured["post_url"] == "https://example.com/custom-fusion-endpoint"
    if result.get("cover_path") and os.path.exists(result["cover_path"]):
        os.unlink(result["cover_path"])


def test_ai_cover_hides_unknown_author_by_default(monkeypatch):
    from txt_to_epub.core import _generate_ai_cover_image
    from txt_to_epub import ParserConfig

    captured = {'author': None}

    class FakeCoverGenerator:
        def __init__(self, *args, **kwargs):
            pass

        def generate_cover(self, **kwargs):
            captured['author'] = kwargs.get('author')
            return {'success': True, 'cover_path': _create_png_file()}

        def get_stats(self):
            return {'total_calls': 1}

    monkeypatch.setattr('txt_to_epub.ai.CoverGenerator', FakeCoverGenerator)

    config = ParserConfig(enable_ai_cover=True)
    cover_path, generated, usage, warnings = _generate_ai_cover_image(
        content='示例正文',
        language='chinese',
        title='无名之书',
        author='Unknown Author',
        metadata_payload={},
        config=config
    )

    try:
        assert generated is True
        assert captured['author'] == ''
        assert usage['total_calls'] == 1
        assert warnings == []
    finally:
        if cover_path and os.path.exists(cover_path):
            os.unlink(cover_path)


def test_ai_cover_can_keep_unknown_author_when_disabled(monkeypatch):
    from txt_to_epub.core import _generate_ai_cover_image
    from txt_to_epub import ParserConfig

    captured = {'author': None}

    class FakeCoverGenerator:
        def __init__(self, *args, **kwargs):
            pass

        def generate_cover(self, **kwargs):
            captured['author'] = kwargs.get('author')
            return {'success': True, 'cover_path': _create_png_file()}

        def get_stats(self):
            return {'total_calls': 1}

    monkeypatch.setattr('txt_to_epub.ai.CoverGenerator', FakeCoverGenerator)

    config = ParserConfig(enable_ai_cover=True, hide_unknown_author=False)
    cover_path, generated, usage, warnings = _generate_ai_cover_image(
        content='示例正文',
        language='chinese',
        title='无名之书',
        author='Unknown Author',
        metadata_payload={},
        config=config
    )

    try:
        assert generated is True
        assert captured['author'] == 'Unknown Author'
        assert usage['total_calls'] == 1
        assert warnings == []
    finally:
        if cover_path and os.path.exists(cover_path):
            os.unlink(cover_path)


def test_cover_prompt_omits_placeholder_author_text():
    from txt_to_epub.ai.cover_generator import CoverGenerator

    prompt = CoverGenerator._build_cover_prompt(
        title='无名之书',
        author='',
        description='一个悬疑故事',
        tags=['悬疑'],
        language='chinese',
        style_hint='',
        content_sample='第一章开始',
        source_hint='sample'
    )

    assert 'Author: Unknown' not in prompt
    assert 'Author: [omit]' in prompt
    assert 'Do not render any author name text on the cover.' in prompt


def test_ai_cover_uses_ai_metadata_title_when_input_title_is_source_slug(monkeypatch):
    from txt_to_epub import txt_to_epub, ParserConfig

    captured = {'title': None, 'author': None, 'source_hint': None}
    generated_cover_path = _create_png_file()

    def fake_ai_metadata(*args, **kwargs):
        return (
            {
                'title': '琼明神女录',
                'author': '倒悬山剑气长存',
                'description': '示例简介',
                'tags': ['仙侠'],
                'language': 'zh',
            },
            True,
            {'total_calls': 1},
            []
        )

    def fake_generate_ai_cover_image(*args, **kwargs):
        captured['title'] = kwargs.get('title')
        captured['author'] = kwargs.get('author')
        captured['source_hint'] = kwargs.get('source_hint')
        return generated_cover_path, True, {'total_calls': 1}, []

    monkeypatch.setattr("txt_to_epub.core._generate_ai_book_metadata", fake_ai_metadata)
    monkeypatch.setattr("txt_to_epub.core._generate_ai_cover_image", fake_generate_ai_cover_image)

    with tempfile.TemporaryDirectory() as tmp_dir:
        txt_file = os.path.join(tmp_dir, "qm.txt")
        epub_file = os.path.join(tmp_dir, "qm.epub")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("第一章 暮色之城\n\n城市在雨夜中逐步显露它的秘密。")

        config = ParserConfig(enable_ai_cover=True, enable_ai_metadata=True)
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='qm',
            author='Unknown',
            config=config,
            show_progress=False
        )

        assert result['success'] is True
        assert captured['title'] == '琼明神女录'
        assert captured['author'] == '倒悬山剑气长存'
        assert captured['source_hint'] == 'qm'


def test_ai_cover_passes_custom_fusion_image_api_url_from_config(monkeypatch):
    from txt_to_epub.core import _generate_ai_cover_image
    from txt_to_epub import ParserConfig

    captured = {'fusion_image_api_url': None}

    class FakeCoverGenerator:
        def __init__(self, *args, **kwargs):
            captured['fusion_image_api_url'] = kwargs.get('fusion_image_api_url')

        def generate_cover(self, **kwargs):
            return {'success': True, 'cover_path': _create_png_file()}

        def get_stats(self):
            return {'total_calls': 1}

    monkeypatch.setattr('txt_to_epub.ai.CoverGenerator', FakeCoverGenerator)

    config = ParserConfig(
        enable_ai_cover=True,
        fusion_image_api_url='https://example.com/fusion-image-api'
    )
    cover_path, generated, usage, warnings = _generate_ai_cover_image(
        content='示例正文',
        language='chinese',
        title='无名之书',
        author='作者',
        metadata_payload={},
        config=config
    )

    try:
        assert generated is True
        assert captured['fusion_image_api_url'] == 'https://example.com/fusion-image-api'
        assert usage['total_calls'] == 1
        assert warnings == []
    finally:
        if cover_path and os.path.exists(cover_path):
            os.unlink(cover_path)
