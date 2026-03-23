"""INI/CFG lexer — transforms section names and key names."""
import re
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer


# Each pattern captures the full line content (including trailing \n if present).
# The named groups split the transformable part from the rest.
_COMMENT_RE = re.compile(r'^(\s*[;#][^\n]*\n?)')
_BLANK_RE = re.compile(r'^(\s*\n?)')
# [section_name]  — capture: (open_bracket)(name)(rest_of_line_including_newline)
_SECTION_RE = re.compile(r'^(\s*\[)([^\]\n]+)(\][^\n]*\n?)')
# key = value  — capture: (leading_ws)(key)(separator_and_rest)
_KEY_RE = re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_\-.]*)([ \t]*[=:][^\n]*\n?)')


class IniLexer(BaseLexer):
    """Line-by-line INI lexer.

    Transforms:
        - Section names:  [section_name]  → IDENTIFIER
        - Key names:      key = value     → IDENTIFIER
    Does not transform values or comments.
    """

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        pos = 0
        n = len(source)

        while pos < n:
            chunk = source[pos:]

            m = _COMMENT_RE.match(chunk)
            if m:
                tokens.append(Token(TokenKind.COMMENT, m.group(1)))
                pos += m.end()
                continue

            m = _SECTION_RE.match(chunk)
            if m:
                tokens.append(Token(TokenKind.SYNTAX, m.group(1)))
                tokens.append(Token(TokenKind.IDENTIFIER, m.group(2)))
                tokens.append(Token(TokenKind.SYNTAX, m.group(3)))
                pos += m.end()
                continue

            m = _KEY_RE.match(chunk)
            if m:
                if m.group(1):
                    tokens.append(Token(TokenKind.WHITESPACE, m.group(1)))
                tokens.append(Token(TokenKind.IDENTIFIER, m.group(2)))
                tokens.append(Token(TokenKind.SYNTAX, m.group(3)))
                pos += m.end()
                continue

            # Blank line or unrecognised content — consume up to and including \n
            m = _BLANK_RE.match(chunk)
            if m and m.end() > 0:
                tokens.append(Token(TokenKind.WHITESPACE, m.group(1)))
                pos += m.end()
                continue

            # Fallback: single character
            tokens.append(Token(TokenKind.OTHER, source[pos]))
            pos += 1

        return tokens
