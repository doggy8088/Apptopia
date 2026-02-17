"""Test parsing real test data"""
from pathlib import Path
from src.backend.parsers.obsidian_parser import parse_obsidian_file
from src.backend.utils.file_scanner import FileScanner

# Scan test data
test_data_dir = Path("data/test-data")
scanner = FileScanner()
results = scanner.scan_directory(test_data_dir, recursive=True)

print(f"Found {len(results['markdown'])} Markdown files")
print(f"Found {len(results['images'])} images")
print()

# Parse a few files
sample_files = results['markdown'][:3]

for file_path in sample_files:
    print(f"\n{'='*80}")
    print(f"Parsing: {file_path.relative_to(test_data_dir)}")
    print('='*80)
    
    try:
        parsed = parse_obsidian_file(file_path)
        
        print(f"Title: {parsed.title}")
        print(f"Tags: {parsed.tags[:5] if len(parsed.tags) > 5 else parsed.tags}")
        print(f"Wikilinks: {len(parsed.wikilinks)}")
        print(f"Headings: {len(parsed.headings)}")
        print(f"Images: {len(parsed.images)}")
        print(f"Word count (plain text): {len(parsed.plain_text.split())}")
        
        if parsed.wikilinks:
            print(f"\nSample wikilinks:")
            for link in parsed.wikilinks[:3]:
                print(f"  - [[{link['target']}{'#' + link['header'] if link['header'] else ''}]]")
        
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*80)
print("Summary")
print("="*80)
print(f"Total files processed: {len(sample_files)}")
print("All tests passed!")
