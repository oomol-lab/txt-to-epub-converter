"""
Batch Conversion Example: Convert multiple TXT files to EPUB

This example shows how to batch convert all text files in a directory.
"""

from pathlib import Path
from txt_to_epub import txt_to_epub, ParserConfig
import sys

def batch_convert(input_dir: str, output_dir: str, use_ai: bool = False):
    """
    Convert all TXT files in input_dir to EPUB in output_dir
    
    Args:
        input_dir: Directory containing TXT files
        output_dir: Directory for output EPUB files
        use_ai: Whether to use AI-enhanced parsing
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Configure parser
    config = ParserConfig(enable_llm_assistance=use_ai) if use_ai else None
    
    # Find all TXT files
    txt_files = list(input_path.glob("*.txt"))
    
    if not txt_files:
        print(f"No TXT files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} TXT files to convert")
    print(f"AI enhancement: {'enabled' if use_ai else 'disabled'}\n")
    
    # Convert each file
    success_count = 0
    failed_files = []
    
    for i, txt_file in enumerate(txt_files, 1):
        epub_file = output_path / f"{txt_file.stem}.epub"
        
        try:
            print(f"[{i}/{len(txt_files)}] Converting: {txt_file.name}...")
            
            result = txt_to_epub(
                txt_file=str(txt_file),
                epub_file=str(epub_file),
                title=txt_file.stem,
                author="Unknown",
                config=config
            )
            
            print(f"  ✓ Success: {result['chapter_count']} chapters, "
                  f"{result['total_chars']} characters")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed_files.append(txt_file.name)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"Successful: {success_count}/{len(txt_files)}")
    
    if failed_files:
        print(f"\nFailed files:")
        for filename in failed_files:
            print(f"  - {filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch convert TXT files to EPUB"
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing TXT files"
    )
    parser.add_argument(
        "output_dir",
        help="Directory for output EPUB files"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable AI-enhanced chapter detection"
    )
    
    args = parser.parse_args()
    
    batch_convert(args.input_dir, args.output_dir, args.ai)

if __name__ == "__main__":
    main()
