"""Parameter specification (.pspec) lexer.

Line format:
    name1[,name2,...]:key1=val1,key2=val2,...

Transforms:
    - Header names      (comma-separated identifiers before ':')
    - Parameter keys    (left of '=')
    - Unquoted values   (right of '=', not wrapped in double quotes)

Does not transform:
    - Quoted string literals  ("P1", "1", "2", ...)
"""
import re
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer

_IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_\-.]*')


class PSpecLexer(BaseLexer):
    """Line-by-line lexer for .pspec parameter specification files."""

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        pos = 0
        n = len(source)

        while pos < n:
            eol = source.find('\n', pos)
            line_end = eol if eol != -1 else n
            line = source[pos:line_end]

            if not line.strip():
                tokens.append(Token(TokenKind.WHITESPACE, line))
                if eol != -1:
                    tokens.append(Token(TokenKind.SYNTAX, '\n'))
                pos = line_end + (1 if eol != -1 else 0)
                continue

            colon = line.find(':')
            if colon == -1:
                tokens.append(Token(TokenKind.OTHER, line))
                if eol != -1:
                    tokens.append(Token(TokenKind.SYNTAX, '\n'))
                pos = line_end + (1 if eol != -1 else 0)
                continue

            # Header: comma-separated identifiers before ':'
            self._tokenize_idents(line[:colon], tokens)
            tokens.append(Token(TokenKind.SYNTAX, ':'))

            # Params: key=value pairs after ':'
            self._tokenize_params(line[colon + 1:], tokens)

            if eol != -1:
                tokens.append(Token(TokenKind.SYNTAX, '\n'))
            pos = line_end + (1 if eol != -1 else 0)

        return tokens

    def _tokenize_idents(self, text: str, tokens: List[Token]) -> None:
        """Tokenize comma-separated identifier list."""
        i = 0
        while i < len(text):
            m = _IDENT_RE.match(text, i)
            if m and m.start() == i:
                tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                i = m.end()
            elif text[i] == ',':
                tokens.append(Token(TokenKind.SYNTAX, ','))
                i += 1
            else:
                tokens.append(Token(TokenKind.OTHER, text[i]))
                i += 1

    def _tokenize_params(self, text: str, tokens: List[Token]) -> None:
        """Tokenize key=value,key=value,... parameter pairs."""
        i = 0
        while i < len(text):
            m = _IDENT_RE.match(text, i)
            if m and m.start() == i:
                tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                i = m.end()
                continue

            if text[i] == '=':
                tokens.append(Token(TokenKind.SYNTAX, '='))
                i += 1
                if i >= len(text):
                    continue
                # Quoted value → keep quotes as SYNTAX, content as IDENTIFIER (if valid) or OTHER
                if i < len(text) and text[i] == '"':
                    tokens.append(Token(TokenKind.SYNTAX, '"'))
                    i += 1
                    # Collect everything up to closing quote
                    close = text.find('"', i)
                    if close == -1:
                        close = len(text)
                    inner = text[i:close]
                    if inner:
                        m = _IDENT_RE.fullmatch(inner)
                        if m:
                            tokens.append(Token(TokenKind.IDENTIFIER, inner))
                        else:
                            tokens.append(Token(TokenKind.OTHER, inner))
                    i = close
                    if i < len(text) and text[i] == '"':
                        tokens.append(Token(TokenKind.SYNTAX, '"'))
                        i += 1
                else:
                    # Unquoted value → identifier
                    m = _IDENT_RE.match(text, i)
                    if m and m.start() == i:
                        tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                        i = m.end()
                continue

            if text[i] == ',':
                tokens.append(Token(TokenKind.SYNTAX, ','))
                i += 1
                continue

            tokens.append(Token(TokenKind.OTHER, text[i]))
            i += 1
