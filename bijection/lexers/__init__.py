"""Lexer registry — maps file extensions to lexer instances."""
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bijection.lexers.base import BaseLexer


def get_lexer_for_file(path: str) -> "BaseLexer":
    """Return the appropriate lexer for *path* based on its extension."""
    ext = os.path.splitext(path)[1].lower()
    return _get_lexer_for_ext(ext)


def get_lexer_for_ext(ext: str) -> "BaseLexer":
    ext = ext if ext.startswith(".") else "." + ext
    return _get_lexer_for_ext(ext)


def _get_lexer_for_ext(ext: str) -> "BaseLexer":
    from bijection.lexers.code_lexer import CodeLexer
    from bijection.lexers.json_lexer import JsonLexer
    from bijection.lexers.yaml_lexer import YamlLexer
    from bijection.lexers.ini_lexer import IniLexer
    from bijection.lexers.markdown_lexer import MarkdownLexer
    from bijection.lexers.pspec_lexer import PSpecLexer

    mapping = {
        ".py": lambda: CodeLexer("python"),
        ".c": lambda: CodeLexer("c"),
        ".cpp": lambda: CodeLexer("cpp"),
        ".cc": lambda: CodeLexer("cpp"),
        ".cxx": lambda: CodeLexer("cpp"),
        ".h": lambda: CodeLexer("c"),
        ".hpp": lambda: CodeLexer("cpp"),
        ".sh": lambda: CodeLexer("bash"),
        ".bash": lambda: CodeLexer("bash"),
        ".pl": lambda: CodeLexer("perl"),
        ".pm": lambda: CodeLexer("perl"),
        ".json": JsonLexer,
        ".yaml": YamlLexer,
        ".yml": YamlLexer,
        ".ini": IniLexer,
        ".cfg": IniLexer,
        ".md": MarkdownLexer,
        ".pspec": PSpecLexer,
    }

    factory = mapping.get(ext)
    if factory is None:
        # Fallback: treat as plain text, no identifiers extracted
        from bijection.lexers.plain_lexer import PlainLexer
        return PlainLexer()
    return factory()
