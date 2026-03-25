"""MSPEC format (.mspec) lexer.

Structure:
    #FORMAT-version           — format declaration
    [SECTION_NAME]            — section open
    [EOL_SECTION_NAME]        — section close
    !                         — blank separator
    [EOF]                     — end of file marker
    key = value               — key/value lines inside sections
    identifier (x,y) ! label  — coordinate entries

Strategy: general line scanner — every line is scanned uniformly.
    [A-Za-z_][A-Za-z0-9_]*  → IDENTIFIER (keys, values, labels, section names, etc.)
    [ ] ( ) , = ! # |        → SYNTAX
    whitespace               → WHITESPACE
    everything else          → OTHER  (digits, dots, hyphens, dashes, ...)
"""
import re
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer

_IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
_WS_RE = re.compile(r'[ \t]+')
_SYNTAX_CHARS = frozenset('[](),=!#|')


class MSpecLexer(BaseLexer):

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        pos = 0
        n = len(source)

        while pos < n:
            eol = source.find('\n', pos)
            line_end = eol if eol != -1 else n
            line = source[pos:line_end]
            nl = '\n' if eol != -1 else ''

            self._scan(line, tokens)
            if nl:
                tokens.append(Token(TokenKind.SYNTAX, nl))

            pos = line_end + (1 if eol != -1 else 0)

        return tokens

    def _scan(self, text: str, tokens: List[Token]) -> None:
        """Scan a single line, emitting IDENTIFIER / SYNTAX / WHITESPACE / OTHER."""
        i = 0
        n = len(text)

        while i < n:
            # Identifier: [A-Za-z_][A-Za-z0-9_]*
            m = _IDENT_RE.match(text[i:])
            if m:
                tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                i += m.end()
                continue

            # Whitespace
            m = _WS_RE.match(text[i:])
            if m:
                tokens.append(Token(TokenKind.WHITESPACE, m.group()))
                i += m.end()
                continue

            c = text[i]

            # Single-char syntax
            if c in _SYNTAX_CHARS:
                tokens.append(Token(TokenKind.SYNTAX, c))
                i += 1
                continue

            # Other: collect run of non-identifier, non-whitespace, non-syntax chars
            j = i
            while j < n:
                if (_IDENT_RE.match(text[j:])
                        or text[j] in ' \t'
                        or text[j] in _SYNTAX_CHARS):
                    break
                j += 1
            if j == i:
                j = i + 1  # safety: consume at least one char
            tokens.append(Token(TokenKind.OTHER, text[i:j]))
            i = j
