"""Plain-text lexer — returns the whole file as a single SYNTAX token."""
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer


class PlainLexer(BaseLexer):
    def tokenize(self, source: str) -> List[Token]:
        return [Token(TokenKind.SYNTAX, source)]
