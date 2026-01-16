"""
Basic tests for txt-to-epub-converter

To run tests:
    pytest tests/
"""

import pytest
import os
import tempfile
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
    assert config.llm_confidence_threshold == 0.5
    
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
        assert result['total_chars'] > 0
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
