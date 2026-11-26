#!/usr/bin/env python3
"""Build a .jax file from a translation draft.

Usage: build.py EN_TXT DRAFT OUT_JAX

Draft lines:
  @N          line N of EN_TXT, copied verbatim
  @N-M        lines N to M of EN_TXT, copied verbatim
  =TEXT       TEXT as it is (an empty line is "=")
  §TEXT       a paragraph on one line, formatted with "gq"; continuation
              lines get the leading whitespace of TEXT
  §PREFIX§TEXT
              the same, PREFIX (e.g. '\t"name"\t\t' or '1. ') is replaced
              by whitespace of the same width while formatting, so that
              continuation lines get that whitespace, and is restored
              afterwards
  #!...       a comment, dropped

The paragraphs are formatted with autofmt in a Vim running on a pty, with
the settings of the AGENTS.md section on line breaks.

Environment:
  VIMPROG     the Vim to run (default: vim)
  AUTOFMT     the directory of the autofmt plugin, added to 'runtimepath'
              (not needed when autofmt is in the default 'packpath')
"""
import os
import pty
import sys
import unicodedata


def width(s):
    col = 0
    for c in s:
        if c == '\t':
            col += 8 - col % 8
        else:
            col += 2 if unicodedata.east_asian_width(c) in 'WF' else 1
    return col


def blank(w, tabs=True):
    # Whitespace of display width w starting at column 0.
    if not tabs:
        return ' ' * w
    return '\t' * (w // 8) + ' ' * (w % 8)


def prefix_blank(prefix):
    # Spaces for a prefix without a tab, see the end of main().
    return blank(width(prefix), '\t' in prefix)


def run_vim(path, lnums, listfile):
    cmds = ['set nocompatible encoding=utf-8 fileencodings=utf-8']
    if os.environ.get('AUTOFMT'):
        cmds.append('set rtp^=' + os.environ['AUTOFMT'].replace(' ', '\\ '))
    else:
        cmds.append('packadd autofmt')
    cmds += [
        'edit ' + path.replace(' ', '\\ '),
        'setlocal textwidth=78 tabstop=8 noexpandtab ambiwidth=single',
        'setlocal formatexpr=autofmt#japanese#formatexpr()',
        'let b:autofmt_allow_over_tw = 1',
        # 'formatoptions' of a help file in the maintainer's Vim, plus "n".
        'setlocal formatoptions=tcqlmMn formatlistpat=^\\\\s*-\\\\+\\\\s\\\\+',
        'setlocal autoindent',
        'let s:off = 0',
        'let s:res = []',
        f'for s:l in {lnums}',
        '  let s:n = line("$")',
        '  exe (s:l + s:off) .. "normal! gqq"',
        '  call add(s:res, (s:l + s:off) .. " " .. (line("$") - s:n + 1))',
        '  let s:off += line("$") - s:n',
        'endfor',
        f'call writefile(s:res, "{listfile}")',
        'write',
        'qall!',
    ]
    script = path + '.gq.vim'
    with open(script, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cmds) + '\n')
    pid, fd = pty.fork()
    if pid == 0:
        prog = os.environ.get('VIMPROG', 'vim')
        os.execvp(prog, [prog, '-u', 'NONE', '-i', 'NONE', '-N', '-S',
                         script])
    while True:
        try:
            if not os.read(fd, 4096):
                break
        except OSError:
            break
    os.waitpid(pid, 0)
    os.remove(script)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    en_path, draft_path, out_path = sys.argv[1:4]
    en = open(en_path, encoding='utf-8').read().split('\n')
    draft = open(draft_path, encoding='utf-8').read().split('\n')
    if draft[-1] == '':
        draft.pop()
    out = []
    paras = []      # (line number in out, prefix or None)
    spaces = []     # whether the paragraph is indented with spaces only
    for no, line in enumerate(draft, 1):
        if line.startswith('#!'):
            continue
        if line.startswith('@'):
            a, _, b = line[1:].partition('-')
            a = int(a)
            b = int(b) if b else a
            out.extend(en[a - 1:b])
        elif line.startswith('='):
            out.append(line[1:])
        elif line.startswith('§'):
            body = line[1:]
            if '§' in body:
                prefix, text = body.split('§', 1)
                out.append(prefix_blank(prefix) + text)
                paras.append((len(out), prefix))
            else:
                out.append(body)
                paras.append((len(out), None))
            line = out[-1]
            spaces.append('\t' not in line[:len(line) - len(line.lstrip())])
        else:
            sys.exit(f'{draft_path}:{no}: unknown line: {line[:40]}')
    out_path = os.path.abspath(out_path)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    listfile = out_path + '.lines'
    run_vim(out_path, [p[0] for p in paras], listfile)
    # The first line of each formatted paragraph and its number of lines.
    ranges = [tuple(int(x) for x in r.split())
              for r in open(listfile).read().splitlines()]
    os.remove(listfile)
    if len(ranges) != len(paras):
        sys.exit('Vim did not format all paragraphs')
    res = open(out_path, encoding='utf-8').read().split('\n')
    for (_, prefix), (lnum, count), sp in zip(paras, ranges, spaces):
        for i in range(lnum - 1, lnum + count - 1):
            if i >= lnum and res[i].strip() == '>':
                # A ">" that "gq" left alone on a line goes to column 1.
                res[i] = '>'
            elif sp:
                # "gq" indents with tabs, keep the spaces of the first line.
                body = res[i].lstrip(' \t')
                res[i] = ' ' * width(res[i][:len(res[i]) - len(body)]) + body
        if prefix is not None:
            first = res[lnum - 1]
            body = first.lstrip(' \t')
            if width(first[:len(first) - len(body)]) != width(prefix):
                sys.exit(f'{out_path}:{lnum}: prefix not found')
            res[lnum - 1] = prefix + body
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(res))


if __name__ == '__main__':
    main()
