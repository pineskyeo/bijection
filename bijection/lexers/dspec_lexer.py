"""DSPEC list file (.dspec) lexer.

Pipe-delimited format:
    !...          — comment / separator / header lines
    f0|f1|f2|..   — data rows (pipe-separated fields)
    [EOF]         — end marker

Field indices (0-based from pipe split) treated as identifiers:
    1  (BBB)   — plain identifier when non-empty
    2  (DDD)   — plain identifier when non-empty
    3  (IIII)  — plain identifier
    9  (PPP)   — plain identifier
    10 (BBBB)  — Name[.Variant] as identifier + (params) as OTHER
"""
import re
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer

# Identifier: letters/digits/underscore, starting with letter or underscore
_IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
# Identifier with optional dot-variant suffix: RRRR2.XX
_IDENT_DOT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*')

_PLAIN_IDENT_FIELDS = {1, 2, 3, 9}
_DOT_IDENT_FIELD = 10


class DSpecLexer(BaseLexer):

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        pos = 0
        n = len(source)

        while pos < n:
            eol = source.find('\n', pos)
            line_end = eol if eol != -1 else n
            line = source[pos:line_end]
            nl = '\n' if eol != -1 else ''
            stripped = line.strip()

            if not stripped:
                tokens.append(Token(TokenKind.WHITESPACE, line + nl))
            elif stripped.startswith('!'):
                tokens.append(Token(TokenKind.COMMENT, line + nl))
            elif stripped == '[EOF]':
                lead = line[: len(line) - len(line.lstrip())]
                if lead:
                    tokens.append(Token(TokenKind.WHITESPACE, lead))
                tokens.append(Token(TokenKind.SYNTAX, '['))
                tokens.append(Token(TokenKind.IDENTIFIER, 'EOF'))
                tokens.append(Token(TokenKind.SYNTAX, ']'))
                trail = line.lstrip()[5:]  # after '[EOF]'
                if trail:
                    tokens.append(Token(TokenKind.OTHER, trail))
                if nl:
                    tokens.append(Token(TokenKind.SYNTAX, nl))
            else:
                self._tok_data_row(line, tokens)
                if nl:
                    tokens.append(Token(TokenKind.SYNTAX, nl))

            pos = line_end + (1 if eol != -1 else 0)

        return tokens

    # ------------------------------------------------------------------

    def _tok_data_row(self, line: str, tokens: List[Token]) -> None:
        """Scan pipe-separated fields, emitting appropriate token kinds."""
        field_idx = 0
        field_start = 0
        n = len(line)
        i = 0

        while i <= n:
            if i == n or line[i] == '|':
                content = line[field_start:i]
                self._tok_field(content, field_idx, tokens)
                if i < n:
                    tokens.append(Token(TokenKind.SYNTAX, '|'))
                field_idx += 1
                field_start = i + 1
                i += 1
            else:
                i += 1

    def _tok_field(self, content: str, field_idx: int,
                   tokens: List[Token]) -> None:
        if not content:
            return

        if field_idx in _PLAIN_IDENT_FIELDS:
            tokens.append(Token(TokenKind.IDENTIFIER, content))

        elif field_idx == _DOT_IDENT_FIELD:
            # e.g. RRRR2.XX(11E-1) → IDENT=RRRR2.XX  OTHER=(11E-1)
            m = _IDENT_DOT_RE.match(content)
            if m:
                tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                rest = content[m.end():]
                if rest:
                    tokens.append(Token(TokenKind.OTHER, rest))
            else:
                tokens.append(Token(TokenKind.OTHER, content))

        else:
            tokens.append(Token(TokenKind.OTHER, content))
