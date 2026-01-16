"""
Basic Example: Convert TXT to EPUB

This example shows the simplest way to convert a text file to EPUB format.
"""

from txt_to_epub import txt_to_epub

def main():
    # Basic conversion with minimal parameters
    result = txt_to_epub(
        txt_file="sample_book.txt",          # Input TXT file
        epub_file="output/sample_book.epub",  # Output EPUB file
        title="Sample Book",                  # Book title
        author="Author Name"                  # Author name
    )
    
    # Print results
    print(f"✓ Conversion completed!")
    print(f"Output file: {result['output_file']}")
    print(f"Total characters: {result['total_chars']}")
    print(f"Chapters detected: {result['chapter_count']}")
    print(f"\nValidation Report:")
    print(result['validation_report'])

if __name__ == "__main__":
    main()
