#!/usr/bin/env python3
"""
Extract text between [TAG] and [/TAG] from stdin.

Usage: echo "...body..." | python3 extract_tag.py 投稿文

Prints the captured text (whitespace stripped) to stdout.
Exit 0: tag found and content non-empty.
Exit 1: tag not found, or content empty after stripping.
Exit 2: argument error.
"""
import re
import sys


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tag>", file=sys.stderr)
        sys.exit(2)

    tag = sys.argv[1]
    body = sys.stdin.read()
    pattern = rf"\[{re.escape(tag)}\](.*?)\[/{re.escape(tag)}\]"
    m = re.search(pattern, body, re.DOTALL)
    if not m:
        sys.exit(1)
    text = m.group(1).strip()
    if not text:
        sys.exit(1)
    print(text)


if __name__ == "__main__":
    main()
