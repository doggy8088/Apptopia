# Phase 1 Implementation - Setup Guide

## Overview

This directory contains the Python backend implementation for Phase 1: Data Import & Indexing.

## Project Structure

```
src/backend/
├── core/           # Core business logic
├── models/         # Data models (Document, Metadata, etc.)
├── parsers/        # Markdown/Obsidian parsers
├── indexer/        # Document indexing (future)
└── utils/          # Utilities (file scanning, etc.)
```

## Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Navigate to project root
cd apps/issue-3

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_obsidian_parser.py -v
```

## Current Implementation Status

### ✅ Completed Components

1. **Data Models** (`src/backend/models/document.py`)
   - Document, DocumentMetadata, DocumentChunk
   - SourceFolder, Relationship, KnowledgeBase
   - Complete type definitions per TECHNICAL_ARCHITECTURE.md

2. **Obsidian Parser** (`src/backend/parsers/obsidian_parser.py`)
   - Full P1 syntax support:
     - YAML frontmatter (tags, aliases, custom fields)
     - Wikilinks (all 4 variants)
     - Tags (inline and nested)
     - Obsidian images
     - Standard Markdown
   - P2 degraded support:
     - Code block titles (removed)
     - Callouts (converted to blockquotes)
     - Embeds (converted to links)
   - Comprehensive test coverage (200+ lines of tests)

3. **File Scanner** (`src/backend/utils/file_scanner.py`)
   - Directory scanning (recursive/non-recursive)
   - Change detection (new/modified/deleted/unchanged)
   - File hashing for integrity
   - Automatic skipping of hidden files and .obsidian directories
   - Comprehensive test coverage

### 🚧 In Progress

4. **Document Indexer** (src/backend/indexer/)
   - Not yet implemented
   - Will handle:
     - Document chunking
     - Vector embedding
     - Chroma integration
     - Incremental updates

5. **Core Logic** (src/backend/core/)
   - Not yet implemented
   - Will handle:
     - Knowledge base management
     - Source folder management
     - Document lifecycle

### ⏳ Future Work

6. **Frontend** (src/frontend/)
   - Tauri desktop application
   - UI for document management
   - Knowledge graph visualization

7. **OCR Pipeline**
   - PaddleOCR integration
   - Image text extraction

## Usage Examples

### Parsing an Obsidian File

```python
from pathlib import Path
from src.backend.parsers.obsidian_parser import parse_obsidian_file

# Parse a file
file_path = Path("data/test-data/Card卡片盒/學習/程式/Rust/Rust 所有權.md")
result = parse_obsidian_file(file_path)

# Access parsed data
print(f"Title: {result.title}")
print(f"Tags: {result.tags}")
print(f"Wikilinks: {len(result.wikilinks)}")
print(f"Headings: {result.headings}")
```

### Scanning a Directory

```python
from pathlib import Path
from src.backend.utils.file_scanner import FileScanner

# Create scanner
scanner = FileScanner()

# Scan directory
directory = Path("data/test-data")
results = scanner.scan_directory(directory, recursive=True)

print(f"Found {len(results['markdown'])} Markdown files")
print(f"Found {len(results['images'])} images")

# Detect changes
changes = scanner.detect_changes(results['markdown'])
print(f"New: {len(changes['new'])}")
print(f"Modified: {len(changes['modified'])}")
```

## Architecture Notes

### Design Principles

1. **Modular**: Each component has a single responsibility
2. **Testable**: Comprehensive test coverage (target: >80%)
3. **Type-Safe**: Full type hints for better IDE support
4. **Documented**: Docstrings for all public APIs

### Obsidian Syntax Support

Implementation follows `docs/OBSIDIAN_SYNTAX_SUPPORT.md`:

- **P1 (Full Support)**: Implemented ✅
  - YAML frontmatter
  - Wikilinks (all variants)
  - Tags (nested support)
  - Images
  - Standard Markdown

- **P2 (Degraded)**: Implemented ✅
  - Code block titles
  - Callouts
  - Embeds

- **P3 (Not Supported)**: As specified
  - Dataview queries
  - Canvas files
  - Plugin syntax

### Performance Targets

Based on `docs/OBSIDIAN_SYNTAX_SUPPORT.md`:

- Single file parsing: < 100ms (currently ~10-50ms)
- 43 test files: < 5 seconds (not yet tested at scale)
- Incremental updates: < 1 second (not yet implemented)

## Next Steps

1. **Complete Phase 1 (Week 3-6)**:
   - [ ] Implement document chunking
   - [ ] Integrate Chroma vector database
   - [ ] Implement incremental indexing
   - [ ] Add OCR pipeline

2. **Move to Phase 2 (Week 7-10)**:
   - [ ] Implement RAG Q&A system
   - [ ] Add source citation
   - [ ] Handle "data not found" cases

3. **Phase 3-5**: Per ROADMAP.md

## Contributing

See `docs/CONTRIBUTING.md` for development guidelines.

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions (future)
- **End-to-End Tests**: Test full workflows (future)

Current test coverage focuses on:
- Parser correctness (all syntax variants)
- File scanner functionality
- Edge cases and error handling

## Known Limitations

1. **Vector Database**: Not yet integrated (Phase 1 Week 6)
2. **OCR**: Not yet implemented (Phase 1 Week 6)
3. **UI**: Not yet started (Phase 1 Week 3-4)
4. **Relationship Analysis**: Not yet implemented (Phase 3)

## References

- Planning Documents: `docs/`
- Test Data: `data/test-data/`
- Architecture: `docs/TECHNICAL_ARCHITECTURE.md`
- Roadmap: `docs/ROADMAP.md`
