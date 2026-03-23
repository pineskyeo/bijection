"""Markdown lexer — only transforms identifiers inside fenced code blocks."""
import re
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer


# Matches the opening of a fenced code block: ```lang or ~~~lang (at start of line)
_FENCE_OPEN_RE = re.compile(r'^([ \t]*)(```+|~~~+)([^\n]*)\n', re.MULTILINE)

_LANG_MAP = {
    "python": ".py", "py": ".py",
    "c": ".c",
    "cpp": ".cpp", "c++": ".cpp", "cxx": ".cpp",
    "bash": ".sh", "sh": ".sh", "shell": ".sh",
    "perl": ".pl", "pl": ".pl",
    "json": ".json",
    "yaml": ".yaml", "yml": ".yaml",
    "ini": ".ini",
}


class MarkdownLexer(BaseLexer):
    """Tokenises Markdown, delegating fenced code blocks to their language lexer.

    Uses a linear scan (not finditer) so that close-fences are never mistaken
    for open-fences.
    """

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        pos = 0

        while pos < len(source):
            open_match = _FENCE_OPEN_RE.search(source, pos)

            if open_match is None:
                # No more fences — emit the rest as plain text
                if pos < len(source):
                    tokens.append(Token(TokenKind.SYNTAX, source[pos:]))
                break

            # Emit text before the fence opening as plain SYNTAX
            before = source[pos:open_match.start()]
            if before:
                tokens.append(Token(TokenKind.SYNTAX, before))

            fence_indent = open_match.group(1)
            fence_char = open_match.group(2)
            lang_tag = open_match.group(3).strip().lower()

            # Emit the fence opening line as SYNTAX
            tokens.append(Token(TokenKind.SYNTAX, open_match.group(0)))

            # Find the matching close fence (same or more fence chars, same indent)
            close_pattern = re.compile(
                r'^' + re.escape(fence_indent) + re.escape(fence_char[0]) + r'+[ \t]*(\n|$)',
                re.MULTILINE,
            )
            close_match = close_pattern.search(source, open_match.end())

            if close_match is None:
                # Unclosed fence — emit rest of file as SYNTAX
                tokens.append(Token(TokenKind.SYNTAX, source[open_match.end():]))
                pos = len(source)
                break

            code_body = source[open_match.end():close_match.start()]

            # Try to tokenise the code block body using the appropriate sub-lexer
            sub_tokens = self._tokenize_code(code_body, lang_tag)

            # Verify sub-lexer losslessness; fall back to plain if broken
            if "".join(t.value for t in sub_tokens) != code_body:
                tokens.append(Token(TokenKind.SYNTAX, code_body))
            else:
                tokens.extend(sub_tokens)

            # Emit the closing fence as SYNTAX
            tokens.append(Token(TokenKind.SYNTAX, close_match.group(0)))
            pos = close_match.end()

        return tokens

    # ------------------------------------------------------------------

    def _tokenize_code(self, code: str, lang_tag: str) -> List[Token]:
        ext = _LANG_MAP.get(lang_tag)
        if ext is None:
            return [Token(TokenKind.SYNTAX, code)]
        try:
            from bijection.lexers import _get_lexer_for_ext
            sub_lexer = _get_lexer_for_ext(ext)
            return sub_lexer.tokenize(code)
        except Exception:
            return [Token(TokenKind.SYNTAX, code)]
