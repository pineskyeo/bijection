"""Token data structures for bijection."""
from enum import Enum


class TokenKind(Enum):
    KEYWORD = "KEYWORD"          # language keyword — never transform
    BUILTIN = "BUILTIN"          # built-in name — never transform
    IDENTIFIER = "IDENTIFIER"    # user-defined name — transform target
    LITERAL = "LITERAL"          # string/number literal
    SYNTAX = "SYNTAX"            # operators, brackets, etc.
    WHITESPACE = "WHITESPACE"    # spaces, newlines, tabs
    COMMENT = "COMMENT"          # comments
    OTHER = "OTHER"              # anything else


class Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind: TokenKind, value: str) -> None:
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.kind.name}, {self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self.kind == other.kind and self.value == other.value
