#!/usr/bin/env python3
"""
Robust Markdown to Plain Text Converter with Stripped Content Logging.

This module provides a comprehensive solution for converting Markdown files to clean
plain text while preserving content integrity. Features include safe regex processing,
detailed logging of removed content, and comprehensive error handling.

Stephen Genusa https://www.github.com/StephenGenusa

Example:
    Convert a markdown file to plain text with debug output::

        $ python markdown_cleaner.py --debug --show-stripped input.md output.txt

    This will create both output.txt and output_removed.txt files.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional


class StrippedContentLogger:
    """
    Tracks and logs all content that gets stripped during markdown conversion.

    This class provides a centralized way to collect and organize all the markdown
    formatting elements that are removed during the conversion process, allowing
    users to audit what was stripped and verify no important content was lost.

    Attributes:
        enabled (bool): Whether logging is active
        sections (Dict[str, List[str]]): Storage for removed content by category
    """

    def __init__(self, enabled: bool = False) -> None:
        """
        Initialize the stripped content logger.

        Args:
            enabled: Whether to actively log stripped content
        """
        self.enabled = enabled
        self.sections: Dict[str, List[str]] = {}

    def log(self, step_name: str, removed_content: str) -> None:
        """
        Log content removed in a specific processing step.

        Args:
            step_name: Identifier for the processing step (e.g., 'code_blocks')
            removed_content: The actual content that was stripped

        Note:
            Content is only logged if logging is enabled and the content
            is not empty after stripping whitespace.
        """
        if not self.enabled or not removed_content.strip():
            return

        if step_name not in self.sections:
            self.sections[step_name] = []
        self.sections[step_name].append(removed_content)

    def save_to_file(self, output_path: Path) -> None:
        """
        Write all logged removed content to a structured file.

        Args:
            output_path: Path where the removed content file should be written

        Note:
            Only creates a file if logging is enabled and content was collected.
            The output file is structured with sections for each processing step.
        """
        if not self.enabled or not self.sections:
            return

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("MARKDOWN CONVERTER - REMOVED CONTENT LOG\n")
            f.write("=" * 50 + "\n\n")

            for step_name, content_list in self.sections.items():
                if content_list:
                    f.write(f"{step_name.upper()}\n")
                    f.write("-" * len(step_name) + "\n")

                    for i, content in enumerate(content_list, 1):
                        f.write(f"\n[Item {i}]\n")
                        f.write(content)
                        f.write("\n")

                    f.write("\n" + "=" * 50 + "\n\n")


def safe_remove_code_blocks(text: str, logger: StrippedContentLogger) -> str:
    """
    Safely remove markdown code blocks using line-by-line processing.

    This function handles both properly closed and malformed code blocks by
    processing the input line by line rather than using potentially dangerous
    regex patterns that could cause catastrophic backtracking.

    Args:
        text: Input text containing markdown code blocks
        logger: Logger instance for tracking removed content

    Returns:
        Text with code blocks replaced by '[CODE BLOCK]' placeholders

    Note:
        Warns to stderr if unclosed code blocks are detected and handles
        them gracefully by treating the rest of the file as part of the block.
    """
    lines = text.split('\n')
    result_lines = []
    in_code_block = False
    code_block_start_line = -1
    current_code_block = []

    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if not in_code_block:
                # Starting a code block
                in_code_block = True
                code_block_start_line = i
                current_code_block = [line]
                result_lines.append('[CODE BLOCK]')
            else:
                # Ending a code block
                current_code_block.append(line)
                logger.log("code_blocks", '\n'.join(current_code_block))
                in_code_block = False
                current_code_block = []
            continue

        if in_code_block:
            current_code_block.append(line)
            continue

        result_lines.append(line)

    # Handle unclosed code blocks
    if in_code_block:
        print(f"Warning: Unclosed code block starting at line {code_block_start_line + 1}", file=sys.stderr)
        if current_code_block:
            logger.log("code_blocks_unclosed", '\n'.join(current_code_block))

    return '\n'.join(result_lines)


def safe_remove_emphasis(text: str, logger: StrippedContentLogger) -> str:
    """
    Safely remove markdown emphasis formatting using line-by-line processing.

    Processes emphasis markers (bold and italic) on a per-line basis to prevent
    regex catastrophic backtracking that can occur with large documents or
    malformed emphasis markers.

    Args:
        text: Input text containing markdown emphasis
        logger: Logger instance for tracking removed content

    Returns:
        Text with emphasis markers removed, preserving the emphasized content

    Note:
        Processes in order: bold-italic, bold, italic to handle nested formatting
        correctly. Uses negative lookbehind/lookahead to avoid false matches.
    """
    lines = text.split('\n')
    result_lines = []

    for line in lines:
        original_line = line
        processed_line = line

        # Bold italic first (most specific) - ***text***
        matches = re.findall(r'\*\*\*([^*\n]{1,125}?)\*\*\*', processed_line)
        for match in matches:
            logger.log("bold_italic", f"***{match}***")
        processed_line = re.sub(r'\*\*\*([^*\n]{1,125}?)\*\*\*', r'\1', processed_line)

        # Bold patterns - **text**
        matches = re.findall(r'\*\*([^*\n]{1,125}?)\*\*', processed_line)
        for match in matches:
            logger.log("bold_asterisks", f"**{match}**")
        processed_line = re.sub(r'\*\*([^*\n]{1,125}?)\*\*', r'\1', processed_line)

        # Bold underscores - __text__
        matches = re.findall(r'__([^_\n]{1,125}?)__', processed_line)
        for match in matches:
            logger.log("bold_underscores", f"__{match}__")
        processed_line = re.sub(r'__([^_\n]{1,125}?)__', r'\1', processed_line)

        # Italic patterns - *text* (avoiding conflict with bold)
        matches = re.findall(r'(?<!\*)\*([^*\n]{1,125}?)\*(?!\*)', processed_line)
        for match in matches:
            logger.log("italic_asterisks", f"*{match}*")
        processed_line = re.sub(r'(?<!\*)\*([^*\n]{1,125}?)\*(?!\*)', r'\1', processed_line)

        # Italic underscores - _text_ (avoiding conflict with bold)
        matches = re.findall(r'(?<!_)_([^_\n]{1,125}?)_(?!_)', processed_line)
        for match in matches:
            logger.log("italic_underscores", f"_{match}_")
        processed_line = re.sub(r'(?<!_)_([^_\n]{1,125}?)_(?!_)', r'\1', processed_line)

        result_lines.append(processed_line)

    return '\n'.join(result_lines)


def conservative_remove_tables(text: str, logger: StrippedContentLogger) -> str:
    """
    Remove markdown table formatting using conservative detection.

    This function only removes obvious table separator lines (like |---|---|)
    while preserving table data content that might contain important information.
    This conservative approach minimizes false positives.

    Args:
        text: Input text potentially containing markdown tables
        logger: Logger instance for tracking removed content

    Returns:
        Text with table separator lines removed, data rows preserved

    Note:
        Only removes lines that match the exact table separator pattern:
        starting and ending with |, containing only spaces, dashes, colons,
        and pipes between the outer pipes.
    """
    lines = text.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Only remove lines that are clearly table separators
        # These are lines like: |---|---|---| or | --- | --- | --- |
        is_table_separator = False
        if stripped_line.startswith('|') and stripped_line.endswith('|'):
            # Check if it's mostly dashes, colons, spaces and pipes
            content_between_pipes = stripped_line[1:-1]  # Remove outer pipes
            if re.match(r'^[\s\-:|\|]*$', content_between_pipes) and '-' in content_between_pipes:
                # Count the separator parts
                parts = [part.strip() for part in content_between_pipes.split('|') if part.strip()]
                if len(parts) >= 2 and all(re.match(r'^:?-+:?$', part.strip()) for part in parts):
                    is_table_separator = True

        if is_table_separator:
            logger.log("table_separators", line)
            continue
        else:
            result_lines.append(line)

    return '\n'.join(result_lines)


def convert_markdown_to_text(
        markdown_content: str,
        debug: bool = False,
        logger: Optional[StrippedContentLogger] = None
) -> str:
    """
    Convert markdown text to plain text with comprehensive formatting removal.

    This is the main conversion function that processes markdown content through
    multiple steps to remove formatting while preserving the actual text content.
    Each step is designed to be safe and avoid regex catastrophic backtracking.

    Args:
        markdown_content: Raw markdown text to be converted
        debug: Whether to print step-by-step character count information
        logger: Optional logger for tracking removed content

    Returns:
        Clean plain text with markdown formatting removed

    Raises:
        No exceptions are raised; malformed input is handled gracefully

    Note:
        Processing order is important - more specific patterns (like bold-italic)
        are handled before more general ones (like italic) to avoid conflicts.
        JSON-like input is detected and unwrapped automatically.
    """

    if logger is None:
        logger = StrippedContentLogger(False)

    def debug_step(step_name: str, before_text: str, after_text: str) -> None:
        """Print debug information for a processing step."""
        if debug:
            before_len = len(before_text)
            after_len = len(after_text)
            diff = before_len - after_len
            print(f"{step_name}: {before_len} → {after_len} (diff: {diff})")

    # Handle JSON-like input (content wrapped in quotes with colons)
    if markdown_content.startswith('"') and ":" in markdown_content:
        try:
            content = markdown_content.split(":", 1)[1].strip().strip('"')
            content = content.replace("\\n", "\n").replace('\\"', '"')
        except Exception:
            content = markdown_content
    else:
        content = markdown_content

    text = content
    original_length = len(text)

    if debug:
        print(f"Starting conversion - original length: {original_length}")

    # Step 1: Remove code blocks safely
    before = text
    text = safe_remove_code_blocks(text, logger)
    debug_step("Step 1 - Code blocks", before, text)

    # Step 2: Remove inline code (backtick-wrapped text)
    before = text
    matches = re.findall(r'`([^`\n]+)`', text)
    for match in matches:
        logger.log("inline_code", f"`{match}`")
    text = re.sub(r'`([^`\n]+)`', r'\1', text)
    debug_step("Step 2 - Inline code", before, text)

    # Step 3a: Remove hash-style headers (# ## ### etc.)
    before = text
    matches = re.findall(r'^(#{1,6}\s+.*)$', text, flags=re.MULTILINE)
    for match in matches:
        logger.log("hash_headers", match)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    debug_step("Step 3a - Hash headers", before, text)

    # Step 3b: Handle alternate style headers (underlined with = or -)
    before = text
    lines = text.split('\n')
    processed_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        if skip_next:
            logger.log("underline_headers", lines[i])
            skip_next = False
            continue

        if i < len(lines) - 1:
            next_line = lines[i + 1]
            if re.match(r'^=+\s*$', next_line) or re.match(r'^-+\s*$', next_line):
                processed_lines.append(line)
                skip_next = True
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)

    text = '\n'.join(processed_lines)
    debug_step("Step 3b - Underline headers", before, text)

    # Step 4: Remove emphasis formatting (bold, italic) safely
    before = text
    text = safe_remove_emphasis(text, logger)
    debug_step("Step 4 - All emphasis", before, text)

    # Step 5: Remove reference-style links and their definitions
    before = text
    # Remove link definitions like [label]: url
    matches = re.findall(r'^(\[([^\]]+)\]:\s*[^\n]*)$', text, flags=re.MULTILINE)
    for match in matches:
        logger.log("reference_link_definitions", match[0])
    text = re.sub(r'^\[([^\]]+)\]:\s*[^\n]*$', '', text, flags=re.MULTILINE)

    # Remove reference links like [text][ref]
    matches = re.findall(r'\[([^\]]+)\]\[[^\]]*\]', text)
    for match in matches:
        logger.log("reference_links", f"[{match}][]")
    text = re.sub(r'\[([^\]]+)\]\[[^\]]*\]', r'\1', text)
    debug_step("Step 5 - Reference links", before, text)

    # Step 6: Remove inline links and images, preserving alt/link text
    before = text
    lines = text.split('\n')
    processed_lines = []

    for line in lines:
        original_line = line

        # Remove images ![alt](url) - keep alt text
        matches = re.findall(r'!\[([^\]\n]{0,125})\]\([^)\n]{1,125}\)', line)
        for match in matches:
            full_match = re.search(r'!\[[^\]\n]{0,125}\]\([^)\n]{1,125}\)', line).group()
            logger.log("images", full_match)
        line = re.sub(r'!\[([^\]\n]{0,125})\]\([^)\n]{1,125}\)', r'\1', line)

        # Remove links [text](url) - keep link text
        matches = re.findall(r'\[([^\]\n]{1,125})\]\([^)\n]{1,125}\)', line)
        for match in matches:
            full_match = re.search(r'\[[^\]\n]{1,125}\]\([^)\n]{1,125}\)', line).group()
            logger.log("links", full_match)
        line = re.sub(r'\[([^\]\n]{1,125})\]\([^)\n]{1,125}\)', r'\1', line)

        processed_lines.append(line)

    text = '\n'.join(processed_lines)
    debug_step("Step 6 - Links and images", before, text)

    # Step 7: Remove task list formatting, preserving task text
    before = text
    matches = re.findall(r'^(\s*[-*+]\s+\[([ xX])\]\s*(.+))$', text, flags=re.MULTILINE)
    for match in matches:
        logger.log("task_lists", match[0])
    text = re.sub(r'^\s*[-*+]\s+\[([ xX])\]\s*(.+)$', r'\2', text, flags=re.MULTILINE)
    debug_step("Step 7 - Task lists", before, text)

    # Step 8: Remove regular list formatting, preserving list content
    before = text
    # Unordered lists (-, *, +)
    matches = re.findall(r'^(\s*[-*+]\s+)(.+)', text, flags=re.MULTILINE)
    for match in matches:
        logger.log("unordered_lists", match[0])
    text = re.sub(r'^\s*[-*+]\s+(.+)', r'\1', text, flags=re.MULTILINE)

    # Ordered lists (1. 2. etc.)
    matches = re.findall(r'^(\s*\d+\.\s+)(.+)', text, flags=re.MULTILINE)
    for match in matches:
        logger.log("ordered_lists", match[0])
    text = re.sub(r'^\s*\d+\.\s+(.+)', r'\1', text, flags=re.MULTILINE)
    debug_step("Step 8 - Regular lists", before, text)

    # Step 9: Handle escaped characters (remove backslash escaping)
    before = text

    def replace_escape(match: re.Match[str]) -> str:
        """Replace escaped characters, preserving the character."""
        char = match.group(1)
        logger.log("escaped_characters", f"\\{char}")
        return char if char in r"`*_{}[]()#+-.!\\" else "\\" + char

    # Process escapes multiple times to handle nested escaping
    for _ in range(2):
        text = re.sub(r'\\([\\`*_{}\[\]()#+\-.!])', replace_escape, text)
    debug_step("Step 9 - Escaped characters", before, text)

    # Step 10: Remove blockquote formatting (> symbols)
    before = text
    lines = text.split('\n')
    result = []
    for line in lines:
        original_line = line
        gt_count = len(re.findall(r'>', line))
        processed_line = re.sub(r'^\s*(?:>\s*)+', ' ' * (gt_count + 1), line)
        if original_line != processed_line:
            removed_part = original_line[:len(original_line) - len(processed_line.lstrip())]
            logger.log("blockquotes", removed_part)
        result.append(processed_line)
    text = '\n'.join(result)
    debug_step("Step 10 - Blockquotes", before, text)

    # Step 11: Remove horizontal rules (--- *** ___)
    before = text
    removed_lines = []
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        if re.match(r'^\s*[-*_](\s*[-*_])*\s*$', line):
            logger.log("horizontal_rules", line)
        else:
            result_lines.append(line)
    text = '\n'.join(result_lines)
    debug_step("Step 11 - Horizontal rules", before, text)

    # Step 12: Remove table formatting conservatively
    before = text
    text = conservative_remove_tables(text, logger)
    debug_step("Step 12 - Tables (conservative)", before, text)

    # Step 13: Remove HTML tags while preserving content
    before = text
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        matches = re.findall(r'<[^>\n]{0,125}>', line)
        for match in matches:
            logger.log("html_tags", match)
        line = re.sub(r'<[^>\n]{0,125}>', '', line)
        processed_lines.append(line)
    text = '\n'.join(processed_lines)
    debug_step("Step 13 - HTML tags", before, text)

    # Step 14: Remove strikethrough formatting (~~text~~)
    before = text
    matches = re.findall(r'~~([^~\n]{1,125}?)~~', text)
    for match in matches:
        logger.log("strikethrough", f"~~{match}~~")
    text = re.sub(r'~~([^~\n]{1,125}?)~~', r'\1', text)
    debug_step("Step 14 - Strikethrough", before, text)

    # Step 15: Remove footnote references and definitions
    before = text
    # Remove footnote references [^1]
    matches = re.findall(r'\[\^([^\]\n]{1,125})\](?!:)', text)
    for match in matches:
        logger.log("footnote_references", f"[^{match}]")
    text = re.sub(r'\[\^([^\]\n]{1,125})\](?!:)', '', text)

    # Remove footnote definitions [^1]: content
    matches = re.findall(r'^(\[\^([^\]]+)\]:\s*(.+))$', text, flags=re.MULTILINE)
    for match in matches:
        logger.log("footnote_definitions", match[0])
    text = re.sub(r'^\[\^([^\]]+)\]:\s*(.+)$', '', text, flags=re.MULTILINE)
    debug_step("Step 15 - Footnotes", before, text)

    # Step 16: Clean up excessive whitespace
    before = text
    # Log excessive whitespace that gets cleaned
    excessive_newlines = re.findall(r'\n{3,}', text)
    if excessive_newlines:
        logger.log("excessive_whitespace", f"Found {len(excessive_newlines)} instances of 3+ consecutive newlines")

    # Normalize multiple newlines to double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace from each line
    text = '\n'.join(line.strip() for line in text.split('\n'))
    debug_step("Step 16 - Clean whitespace", before, text)

    final_length = len(text.strip())
    if debug:
        print(f"Final length: {final_length} (total reduction: {original_length - final_length})")

    return text.strip()


def main() -> None:
    """
    Main entry point with command-line interface and file I/O handling.

    Parses command-line arguments, validates input files, processes the markdown
    content, and writes output files. Handles various error conditions gracefully
    with appropriate error messages.

    Command Line Args:
        input_file: Path to the markdown file to be converted
        output_file: Path where the cleaned text should be written
        -v, --verbose: Enable verbose output showing file operations
        -d, --debug: Show detailed step-by-step conversion statistics
        -s, --show-stripped: Save stripped content to [filename]_removed.txt

    Exit Codes:
        0: Successful conversion
        1: Error occurred (file not found, permissions, encoding, etc.)
    """

    parser = argparse.ArgumentParser(
        description="Convert Markdown files to cleaned plain text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python markdown_cleaner.py input.md output.txt
  python markdown_cleaner.py document.md cleaned_document.txt
  python markdown_cleaner.py --debug input.md output.txt
  python markdown_cleaner.py --show-stripped input.md output.txt
        """
    )

    parser.add_argument("input_file", help="Input markdown file path")
    parser.add_argument("output_file", help="Output text file path")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show processing information")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Show detailed step-by-step conversion statistics")
    parser.add_argument("-s", "--show-stripped", action="store_true",
                        help="Save all stripped content to [filename]_removed.txt")

    args = parser.parse_args()

    # Validate input file exists and is readable
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: '{args.input_file}' is not a regular file.", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup stripped content logger if requested
    logger = StrippedContentLogger(enabled=args.show_stripped)
    removed_file_path = None
    if args.show_stripped:
        removed_file_path = output_path.with_name(output_path.stem + "_removed.txt")

    try:
        # Read input markdown file
        if args.verbose:
            print(f"Reading markdown from: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Process the markdown content
        if args.verbose:
            print("Converting markdown to plain text...")

        cleaned_text = convert_markdown_to_text(markdown_content, debug=args.debug, logger=logger)

        # Write cleaned text to output file
        if args.verbose:
            print(f"Writing cleaned text to: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)

        # Save stripped content log if requested
        if args.show_stripped:
            logger.save_to_file(removed_file_path)
            if args.verbose:
                print(f"Stripped content saved to: {removed_file_path}")

        # Report results
        if args.verbose:
            print(f"Successfully converted {len(markdown_content)} characters to {len(cleaned_text)} characters")

        print(f"Conversion complete: {args.input_file} → {args.output_file}")
        if args.show_stripped:
            print(f"Stripped content logged to: {removed_file_path}")

    except UnicodeDecodeError as e:
        print(f"Error: Unable to read file '{args.input_file}' - encoding issue: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: Permission denied: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: File system error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error during processing: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()