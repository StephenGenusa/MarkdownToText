# Markdown to Plain Text Converter

A robust, production-ready Python tool for converting Markdown files to clean plain text while preserving content integrity and providing detailed conversion logging.

I used a Python module which ended up stripping over half the valid content from my document. I would have submitted a pull request but this ended up being a very different solution.

## Features

- **Safe Processing**: Line-by-line regex processing prevents catastrophic backtracking on large files
- **Content Preservation**: Conservative approach ensures no important content is accidentally removed
- **Comprehensive Logging**: Optional detailed logging of all stripped content for validation
- **Malformed Input Handling**: Gracefully handles unclosed code blocks and malformed markdown
- **Debug Mode**: Step-by-step character count reporting for conversion analysis
- **Professional Error Handling**: Comprehensive exception handling with clear error messages

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/markdown-cleaner.git
cd markdown-cleaner

# No dependencies required - uses Python standard library only
python markdown_cleaner.py --help
```

## Quick Start

```bash
# Basic conversion
python markdown_cleaner.py input.md output.txt

# With debug output
python markdown_cleaner.py --debug input.md output.txt

# With stripped content logging
python markdown_cleaner.py --show-stripped input.md output.txt

# Verbose mode with all features
python markdown_cleaner.py --verbose --debug --show-stripped document.md clean_document.txt
```

## Usage Examples

### Basic Conversion
```bash
python markdown_cleaner.py README.md README_clean.txt
```

### Development and Debugging
```bash
# See exactly what's being processed at each step
python markdown_cleaner.py --debug large_document.md output.txt

# Audit what content was stripped
python markdown_cleaner.py --show-stripped suspicious_file.md clean_file.txt
# Creates: clean_file.txt and clean_file_removed.txt
```

### Processing Multiple Files
```bash
# Process multiple files in a loop
for file in *.md; do
    python markdown_cleaner.py "$file" "${file%%.md}_clean.txt"
done
```

## What Gets Converted

| Markdown Element | Action | Example |
|------------------|--------|---------|
| Code blocks | Replaced with `[CODE BLOCK]` | ` ```code``` ` → `[CODE BLOCK]` |
| Inline code | Backticks removed | `` `code` `` → `code` |
| Headers | Hash symbols removed | `# Title` → `Title` |
| Bold/Italic | Formatting removed | `**bold**` → `bold` |
| Links | URLs removed, text preserved | `[text](url)` → `text` |
| Images | URLs removed, alt text preserved | `![alt](url)` → `alt` |
| Lists | Bullets/numbers removed | `- item` → `item` |
| Tables | Only separator lines removed | Data rows preserved |
| Blockquotes | `>` symbols removed | `> quote` → `quote` |
| HTML tags | Tags removed, content preserved | `<em>text</em>` → `text` |

## Command Line Options

```
positional arguments:
  input_file            Input markdown file path
  output_file           Output text file path

options:
  -h, --help            Show help message and exit
  -v, --verbose         Show processing information
  -d, --debug           Show detailed step-by-step conversion statistics
  -s, --show-stripped   Save all stripped content to [filename]_removed.txt
```

## Debug Output Example

```
Starting conversion - original length: 1051719
Step 1 - Code blocks: 1051719 → 872254 (diff: 179465)
Step 2 - Inline code: 872254 → 872254 (diff: 0)
Step 3a - Hash headers: 872254 → 871174 (diff: 1080)
Step 3b - Underline headers: 871174 → 871174 (diff: 0)
Step 4 - All emphasis: 871174 → 869564 (diff: 1610)
...
Final length: 865141 (total reduction: 186578)
```

## Stripped Content Logging

When using `--show-stripped`, a detailed log file is created showing exactly what was removed:

```
MARKDOWN CONVERTER - REMOVED CONTENT LOG
==================================================

CODE_BLOCKS
-----------

[Item 1]
```python
def hello():
    print("world")
```

HASH_HEADERS
------------

[Item 1]
# Main Title

[Item 2]
## Subsection
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Error Handling

The tool handles various error conditions gracefully:

- **File not found**: Clear error message with exit code 1
- **Permission issues**: Detailed permission error reporting
- **Encoding problems**: Unicode decode error handling
- **Malformed markdown**: Warnings for unclosed code blocks, continues processing
- **Large files**: Safe regex patterns prevent catastrophic backtracking

## Performance

- **Memory efficient**: Processes files line-by-line where possible
- **Regex safe**: All patterns designed to avoid catastrophic backtracking
- **Scalable**: Successfully tested on files over 1MB
- **Fast processing**: Typical conversion rate of 1M+ characters per second

## Technical Details

### Safe Processing Approach

The converter uses several techniques to ensure reliability:

1. **Line-by-line processing** for code blocks and emphasis to prevent regex issues
2. **Conservative table detection** to avoid false positives
3. **Bounded regex patterns** with maximum length limits
4. **Multiple pass processing** for complex nested structures

### Architecture

- `StrippedContentLogger`: Centralized logging of removed content
- `safe_remove_code_blocks()`: Handles malformed code blocks gracefully
- `safe_remove_emphasis()`: Prevents catastrophic backtracking on emphasis
- `conservative_remove_tables()`: Minimal false positive table detection
- `convert_markdown_to_text()`: Main conversion pipeline with 16 processing steps

## License

MIT License

Copyright (c) 2025 by Stephen Genusa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Changelog

### v1.0.0
- Initial release
- Safe code block processing
- Comprehensive markdown element support
- Debug mode and stripped content logging
