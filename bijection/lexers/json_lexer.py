"""JSON lexer — transforms object keys while preserving structure."""
import re
from typing import List, Tuple

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer


# Matches a JSON string (simplified but handles common escapes)
_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')
# Matches whitespace
_WS_RE = re.compile(r'\s+')
# Matches structural characters
_STRUCT_RE = re.compile(r'[{}\[\]:,]')
# Matches numbers, booleans, null
_LITERAL_RE = re.compile(r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null')


def _scan(source: str) -> List[Tuple[int, int, str]]:
    """Return list of (start, end, kind) spans covering the whole source."""
    spans = []
    i = 0
    n = len(source)
    while i < n:
        m = _WS_RE.match(source, i)
        if m:
            spans.append((m.start(), m.end(), "ws"))
            i = m.end()
            continue
        m = _STRING_RE.match(source, i)
        if m:
            spans.append((m.start(), m.end(), "string"))
            i = m.end()
            continue
        m = _STRUCT_RE.match(source, i)
        if m:
            spans.append((m.start(), m.end(), "struct"))
            i = m.end()
            continue
        m = _LITERAL_RE.match(source, i)
        if m:
            spans.append((m.start(), m.end(), "literal"))
            i = m.end()
            continue
        # Unknown character — emit as syntax
        spans.append((i, i + 1, "other"))
        i += 1
    return spans


class JsonLexer(BaseLexer):
    """Transforms JSON object keys (quoted strings immediately before ':').

    Values are left as LITERAL tokens and never transformed.
    """

    def tokenize(self, source: str) -> List[Token]:
        spans = _scan(source)
        tokens: List[Token] = []

        # Walk spans and identify keys: a string span followed (after optional
        # whitespace) by a ':' span indicates a key.
        n = len(spans)
        i = 0
        while i < n:
            start, end, kind = spans[i]
            value = source[start:end]

            if kind == "string":
                # Look ahead past whitespace to find ':'
                j = i + 1
                while j < n and spans[j][2] == "ws":
                    j += 1
                if j < n and spans[j][2] == "struct" and source[spans[j][0]:spans[j][1]] == ":":
                    # This is a key — strip quotes for the identifier value
                    inner = value[1:-1]  # remove surrounding quotes
                    # Emit: open-quote as SYNTAX, inner as IDENTIFIER, close-quote as SYNTAX
                    tokens.append(Token(TokenKind.SYNTAX, '"'))
                    tokens.append(Token(TokenKind.IDENTIFIER, inner))
                    tokens.append(Token(TokenKind.SYNTAX, '"'))
                else:
                    tokens.append(Token(TokenKind.LITERAL, value))
            elif kind == "ws":
                tokens.append(Token(TokenKind.WHITESPACE, value))
            elif kind == "struct":
                tokens.append(Token(TokenKind.SYNTAX, value))
            elif kind == "literal":
                tokens.append(Token(TokenKind.LITERAL, value))
            else:
                tokens.append(Token(TokenKind.OTHER, value))

            i += 1

        return tokens
