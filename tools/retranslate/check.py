#!/usr/bin/env python3
"""Check a .jax file against its original .txt.

Usage: check.py EN_TXT JAX

Reports:
- a tag group (*tag* or |tag|) aligned with a tab at the end of a line,
  which does not start at the column of the same group in the original
- a line wider than 79 columns (78, plus a hanging punctuation mark)
- a translated line with an odd number of " or `, which may be a line
  break inside a quoted part (a hint: it also matches a quote character
  in the text, e.g. '"')
Lines inside a code block (after ">" up to "<") are not checked.
"""
import re
import sys
import unicodedata

TAIL = re.compile(r'((?:[*|][^*|\s]+[*|][ \t]*)+)$')


def width(s):
    # A "☆" heading is aligned with 'ambiwidth' set to "double".
    wide = 'WFA' if s.startswith('☆') else 'WF'
    col = 0
    for c in s:
        if c == '\t':
            col += 8 - col % 8
        else:
            col += 2 if unicodedata.east_asian_width(c) in wide else 1
    return col


def tail(line):
    m = TAIL.search(line)
    if not m:
        return None
    head = line[:m.start()]
    # Only a group after a tab is aligned, not a link at the end of a
    # sentence.
    if not head.strip() or '\t' not in head.rstrip(' ')[-1:]:
        return None
    return m.group(1).rstrip(), width(head)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    en = open(sys.argv[1], encoding='utf-8').read().split('\n')
    ja = open(sys.argv[2], encoding='utf-8').read().split('\n')
    en_tails = {}
    for line in en:
        t = tail(line)
        if t:
            en_tails.setdefault(t[0], t[1])
    bad = 0
    in_code = False
    for n, line in enumerate(ja, 1):
        # A line starting in column 1 ends a code block.
        if in_code and line and not line[0].isspace():
            in_code = False
        if not in_code:
            t = tail(line)
            if t and t[0] in en_tails and en_tails[t[0]] != t[1]:
                print(f'{n}: tag column {t[1]}, original {en_tails[t[0]]}:'
                      f' {line}')
                bad += 1
            if width(line) > 79:
                print(f'{n}: width {width(line)}: {line}')
                bad += 1
            if not line.isascii():
                s = re.sub(r'\*[^*\s]+\*|\|[^|\s]+\|', '', line)
                for q in '"`':
                    if s.count(q) % 2:
                        print(f'{n}: odd number of {q}: {line}')
                        bad += 1
        if re.search(r'(^|\s)>[a-z0-9]*$', line):
            in_code = True
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
