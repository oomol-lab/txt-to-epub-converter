"""
Advanced Example: Convert TXT to EPUB with AI Enhancement

This example demonstrates using AI-powered chapter detection for better accuracy.
"""

from txt_to_epub import txt_to_epub, ParserConfig
import os

def main():
    # Configure AI-enhanced parsing
    config = ParserConfig(
        # Enable LLM assistance
        enable_llm_assistance=True,
        llm_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        llm_base_url="https://api.openai.com/v1",
        llm_model="gpt-4",
        
        # Fine-tune confidence thresholds
        llm_confidence_threshold=0.5,          # When to trigger LLM (0-1)
        llm_toc_detection_threshold=0.5,      # Confidence for TOC existence
        llm_no_toc_threshold=0.6,             # Confidence for no TOC
        
        # TOC detection settings
        toc_detection_score_threshold=20,     # Minimum score for TOC
        toc_max_scan_lines=300                # Lines to scan for TOC
    )
    
    # Convert with full options
    result = txt_to_epub(
        txt_file="complex_book.txt",
        epub_file="output/complex_book.epub",
        title="Complex Format Book",
        author="Author Name",
        cover_image="cover.png",              # Optional: add cover
        config=config,                        # Use custom config
        enable_resume=True                    # Enable resume on interruption
    )
    
    # Print detailed results
    print(f"✓ Conversion completed with AI enhancement!")
    print(f"Output file: {result['output_file']}")
    print(f"Total characters: {result['total_chars']}")
    print(f"Chapters detected: {result['chapter_count']}")
    print(f"\nValidation Report:")
    print(result['validation_report'])

if __name__ == "__main__":
    main()
