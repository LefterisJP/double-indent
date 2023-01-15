from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence, Union

from tokenize_rt import Token, reversed_enumerate, src_to_tokens, tokens_to_src


def _find_outer_parens(tokens: list[Token]) -> tuple[int, int]:
    paren_idx = 0
    idx_opening = []
    idx_closing = []
    for idx, token in enumerate(tokens):
        if token.src == '(':
            idx_opening.append(idx)
            paren_idx += 1
        elif token.src == ')':
            idx_closing.append(idx)
            paren_idx -= 1
            # paren_idx must be zero if we have the last match
            if paren_idx == 0:
                return idx_opening[0], idx_closing[-1]
    else:
        raise AssertionError('past end did not find matching parenthesis')


def _is_multiline_def(tokens: list[Token], start: int) -> bool:
    end = start + 1
    token_len = len(tokens)
    while end < token_len:
        if (
                tokens[end].name == 'OP' and tokens[end].src == '(' and
                # what about trailing ws?
                tokens[end + 1].name == 'NL'
        ):
            return True
        # end of function def found, so not multiline
        elif tokens[end].name == 'OP' and tokens[end].src == ':':
            return False

        end += 1
    else:
        raise AssertionError('past end')


def _fix_indent(
        tokens: list[Token],
        start: int,
        end: int,
        indent: int,
        offset: int,
) -> None:
    idx = start
    while idx < end:
        if tokens[idx].name == 'NL':
            if (
                    tokens[idx + 1].name == 'UNIMPORTANT_WS' and
                    len(tokens[idx + 1].src) != (indent * 2) + offset and
                    # another argument must follow
                    (
                        tokens[idx + 2].name == 'NAME' or
                        tokens[idx + 2].name == 'COMMENT' or
                        # if not a named argument, the operator for positional
                        # or named only arguments must follow
                        (
                            tokens[idx + 2].name == 'OP' and
                            (
                                tokens[idx + 2].src == '*' or
                                tokens[idx + 2].src == '**' or
                                tokens[idx + 2].src == '/'
                            )
                        )
                    )
            ):
                new_indent = ' ' * ((indent * 2) + offset)
                tokens[idx + 1] = tokens[idx + 1]._replace(src=new_indent)
            elif tokens[idx + 1].name == 'NAME':
                # was not indented at all
                ws = Token('UNIMPORTANT_WS', src=' ' * ((indent * 2) + offset))
                tokens.insert(idx + 1, ws)
        idx += 1


def _fix_src(contents_text: str, indent: int) -> str:
    tokens = src_to_tokens(contents_text)
    for idx, token in reversed_enumerate(tokens):
        if token.src == 'def' and _is_multiline_def(tokens, idx):
            offset = token.utf8_byte_offset
            # check if it's an async def, then the async keyword does not
            # change the offset, like a nested function would
            if idx >= 2 and tokens[idx-2].src == 'async':
                offset = tokens[idx-2].utf8_byte_offset

            # we found the start of a a FunctionDef
            start_def, end_def = _find_outer_parens(tokens[idx:])
            _fix_indent(
                tokens,
                start=start_def + idx,
                end=end_def + idx,
                indent=indent,
                offset=offset,
            )

    return tokens_to_src(tokens)


def _fix_file(filename: Path, args: argparse.Namespace) -> int:
    if filename == '-':
        contents = sys.stdin.buffer.read().decode()
    else:
        with open(filename, 'rb') as f:
            contents = f.read().decode()

    contents_orig = contents_text = contents
    contents_text = _fix_src(contents_text, indent=args.indent)

    if filename == '-':
        print(contents_text, end='')
    elif contents_text != contents_orig:
        print(f'Rewriting {filename}', file=sys.stderr)
        with open(filename, 'wb') as f:
            f.write(contents_text.encode())

    return contents_text != contents_orig


def _process_file_or_directory(
        file_or_dir: Union[str, Path],
        args: argparse.Namespace,
) -> int:
    path = Path(file_or_dir)
    ret = 0
    if path.is_dir():
        for child in path.iterdir():
            ret |= _process_file_or_directory(child, args)
    elif path.suffix == '.py':
        ret |= _fix_file(path, args)

    return ret


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_data', nargs='*')
    parser.add_argument(
        '-i', '--indent',
        default=4,
        type=int,
        help='number of spaces for indentation',
    )
    args = parser.parse_args(argv)
    ret = 0
    for entry in args.input_data:
        ret |= _process_file_or_directory(entry, args=args)

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
