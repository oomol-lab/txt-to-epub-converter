"""
Basic tests for txt-to-epub-converter

To run tests:
    pytest tests/
"""

import pytest
import os
import tempfile
import zipfile
from pathlib import Path


def test_import():
    """Test that the package can be imported"""
    try:
        from txt_to_epub import txt_to_epub, ParserConfig
        assert txt_to_epub is not None
        assert ParserConfig is not None
    except ImportError as e:
        pytest.fail(f"Failed to import package: {e}")


def test_parser_config():
    """Test ParserConfig initialization"""
    from txt_to_epub import ParserConfig
    
    # Test default config
    config = ParserConfig()
    assert config.enable_llm_assistance == False
    assert config.llm_confidence_threshold == 0.7
    assert config.llm_base_url == "https://llm.oomol.com/v1"
    assert config.enable_ai_metadata == False
    assert config.enable_ai_cover == False
    assert config.hide_unknown_author == True
    
    # Test custom config
    config = ParserConfig(
        enable_llm_assistance=True,
        llm_confidence_threshold=0.7
    )
    assert config.enable_llm_assistance == True
    assert config.llm_confidence_threshold == 0.7


def test_basic_conversion():
    """Test basic TXT to EPUB conversion"""
    from txt_to_epub import txt_to_epub
    
    # Create a temporary TXT file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一章 开始\n\n这是第一章的内容。\n\n")
        f.write("第二章 继续\n\n这是第二章的内容。\n\n")
        txt_file = f.name
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name
    
    try:
        # Convert
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title="测试书籍",
            author="测试作者"
        )
        
        # Check result
        assert result is not None
        assert 'output_file' in result
        assert os.path.exists(result['output_file'])
        assert result['chapters_count'] > 0
        
    finally:
        # Cleanup
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_version():
    """Test that version is defined"""
    from txt_to_epub import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_generated_epub_uses_paragraph_markup_for_content():
    """Ensure body content is rendered as paragraph tags for reader compatibility."""
    from txt_to_epub import txt_to_epub

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一章 开始\n\n")
        f.write("这是第一段。\n\n")
        f.write("这是第二段，包含 <标签> 与 & 符号。\n")
        txt_file = f.name

    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title="段落测试",
            author="测试作者",
            show_progress=False,
        )

        assert result["success"] is True

        with zipfile.ZipFile(epub_file, "r") as zf:
            xhtml_payload = "\n".join(
                zf.read(name).decode("utf-8")
                for name in zf.namelist()
                if name.endswith(".xhtml")
            )

        assert "<pre>" not in xhtml_payload
        assert "<p>这是第一段。</p>" in xhtml_payload
        assert "这是第二段，包含 &lt;标签&gt; 与 &amp; 符号。" in xhtml_payload
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_context_progress_is_monotonic():
    """Test context progress values never decrease during conversion."""
    from txt_to_epub import txt_to_epub

    class FakeContext:
        def __init__(self):
            self.values = []

        def report_progress(self, value):
            self.values.append(value)

    context = FakeContext()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一章 开始\n\n这是第一章的内容。\n\n")
        f.write("第二章 继续\n\n这是第二章的内容。\n\n")
        f.write("第三章 结尾\n\n这是第三章的内容。\n\n")
        txt_file = f.name

    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title="测试书籍",
            author="测试作者",
            context=context,
            show_progress=False,
        )

        assert result["success"] is True
        assert context.values, "Expected progress to be reported"
        assert context.values[0] == 1
        assert context.values[-1] == 100
        assert all(curr >= prev for prev, curr in zip(context.values, context.values[1:])), context.values
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


def test_context_progress_is_monotonic_with_multiple_volumes():
    """Test context progress remains monotonic when the parser processes multiple volumes."""
    from txt_to_epub import txt_to_epub

    class FakeContext:
        def __init__(self):
            self.values = []

        def report_progress(self, value):
            self.values.append(value)

    context = FakeContext()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("第一卷 起始卷\n")
        f.write("第一章 开端\n\n这是第一卷第一章内容。\n\n")
        f.write("第二章 波动\n\n这是第一卷第二章内容。\n\n")
        f.write("第二卷 终局卷\n")
        f.write("第三章 冲突\n\n这是第二卷第一章内容。\n\n")
        f.write("第四章 尾声\n\n这是第二卷第二章内容。\n")
        txt_file = f.name

    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
        epub_file = f.name

    try:
        result = txt_to_epub(
            txt_file=txt_file,
            epub_file=epub_file,
            title="多卷测试书籍",
            author="测试作者",
            context=context,
            show_progress=False,
        )

        assert result["success"] is True
        assert context.values, "Expected progress to be reported"
        assert context.values[0] == 1
        assert context.values[-1] == 100
        assert all(curr >= prev for prev, curr in zip(context.values, context.values[1:])), context.values
    finally:
        if os.path.exists(txt_file):
            os.unlink(txt_file)
        if os.path.exists(epub_file):
            os.unlink(epub_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
