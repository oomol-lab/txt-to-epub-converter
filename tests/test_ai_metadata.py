"""
Tests for AI metadata integration.
"""

import os
import tempfile

from ebooklib import epub


def _create_sample_txt() -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一章 旧城夜雨\n\n")
        f.write("少年在暴雨中醒来，记忆断裂，只记得一枚银色怀表。\n\n")
        f.write("第二章 追光者\n\n")
        f.write("他追随线索进入地下图书馆，发现城市历史被篡改。\n")
        return f.name


def test_ai_metadata_is_applied_when_title_author_are_defaults(monkeypatch):
    from txt_to_epub import txt_to_epub, ParserConfig

    def fake_ai_metadata(*args, **kwargs):
        return (
            {
                'title': '雨夜怀表',
                'author': 'AI 编辑部',
                'description': '一部关于记忆与真相的悬疑故事。',
                'tags': ['悬疑', '成长', '城市幻想'],
                'publisher': 'Test House',
                'date': '2026-02-25',
                'identifier': 'urn:txt2epub:test:rain-watch',
                'language': 'zh',
            },
            True,
            {'total_calls': 1},
            []
        )

    monkeypatch.setattr("txt_to_epub.core._generate_ai_book_metadata", fake_ai_metadata)

    txt_file = _create_sample_txt()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(enable_ai_metadata=True)
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='My Book',
            author='Unknown',
            config=config,
            show_progress=False
        )

        assert result['success'] is True
        assert result['ai']['metadata']['generated'] is True
        assert result['ai']['usage']['total_calls'] == 1

        book = epub.read_epub(epub_file)
        titles = [value for value, _ in book.get_metadata('DC', 'title')]
        authors = [value for value, _ in book.get_metadata('DC', 'creator')]
        descriptions = [value for value, _ in book.get_metadata('DC', 'description')]
        subjects = [value for value, _ in book.get_metadata('DC', 'subject')]

        assert '雨夜怀表' in titles
        assert 'AI 编辑部' in authors
        assert '一部关于记忆与真相的悬疑故事。' in descriptions
        assert '悬疑' in subjects
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_metadata_overrides_take_precedence(monkeypatch):
    from txt_to_epub import txt_to_epub, ParserConfig

    def fake_ai_metadata(*args, **kwargs):
        return (
            {
                'title': 'AI 标题',
                'author': 'AI 作者',
                'description': 'AI 简介',
                'tags': ['AI标签'],
                'language': 'zh',
            },
            True,
            {'total_calls': 1},
            []
        )

    monkeypatch.setattr("txt_to_epub.core._generate_ai_book_metadata", fake_ai_metadata)

    txt_file = _create_sample_txt()
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        config = ParserConfig(enable_ai_metadata=True)
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title='人工标题',
            author='人工作者',
            config=config,
            metadata_overrides={
                'description': '人工简介',
                'tags': ['人工标签']
            },
            show_progress=False
        )

        assert result['success'] is True

        book = epub.read_epub(epub_file)
        titles = [value for value, _ in book.get_metadata('DC', 'title')]
        authors = [value for value, _ in book.get_metadata('DC', 'creator')]
        descriptions = [value for value, _ in book.get_metadata('DC', 'description')]
        subjects = [value for value, _ in book.get_metadata('DC', 'subject')]

        assert '人工标题' in titles
        assert '人工作者' in authors
        assert '人工简介' in descriptions
        assert '人工标签' in subjects
        assert 'AI标签' not in subjects
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)
