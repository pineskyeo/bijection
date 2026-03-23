"""Pygments-backed lexer for code files (Python, C, C++, Shell, Perl)."""
from typing import List, Set

from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token as PygToken

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer


# ---------------------------------------------------------------------------
# Per-language hard exclusion sets
# ---------------------------------------------------------------------------
_EXTRA_BUILTINS: dict = {
    "python": {
        "True", "False", "None",
        "print", "input", "len", "range", "type", "isinstance", "issubclass",
        "int", "str", "float", "list", "dict", "set", "tuple", "bool",
        "bytes", "bytearray", "memoryview", "complex",
        "open", "iter", "next", "enumerate", "zip", "map", "filter",
        "sorted", "reversed", "sum", "min", "max", "abs", "round",
        "repr", "id", "hash", "hex", "oct", "bin", "chr", "ord",
        "hasattr", "getattr", "setattr", "delattr", "dir", "vars",
        "callable", "staticmethod", "classmethod", "property",
        "super", "object", "Exception", "BaseException",
        "ValueError", "TypeError", "KeyError", "IndexError",
        "AttributeError", "RuntimeError", "StopIteration",
        "NotImplementedError", "OSError", "IOError", "FileNotFoundError",
        "__name__", "__file__", "__doc__", "__init__", "__main__",
        "__all__", "__slots__", "__dict__", "__class__",
        "__str__", "__repr__", "__len__", "__iter__", "__next__",
        "__getitem__", "__setitem__", "__delitem__", "__contains__",
        "__enter__", "__exit__", "__call__", "__new__",
        "__add__", "__sub__", "__mul__", "__div__", "__mod__",
        "__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__",
        "NotImplemented", "Ellipsis",
        "format", "breakpoint", "compile", "exec", "eval",
        "globals", "locals", "quit", "exit",
    },
    "c": {
        "printf", "fprintf", "sprintf", "snprintf",
        "scanf", "fscanf", "sscanf",
        "malloc", "calloc", "realloc", "free",
        "memcpy", "memmove", "memset", "memcmp",
        "strcpy", "strncpy", "strcat", "strncat",
        "strcmp", "strncmp", "strlen", "strdup",
        "fopen", "fclose", "fread", "fwrite", "fgets", "fputs",
        "fseek", "ftell", "rewind", "feof", "ferror",
        "exit", "abort", "atexit", "system",
        "atoi", "atof", "atol", "strtol", "strtod",
        "qsort", "bsearch", "rand", "srand", "abs",
        "NULL", "EOF", "stdin", "stdout", "stderr",
        "main",
    },
    "cpp": {
        "printf", "fprintf", "sprintf", "snprintf",
        "scanf", "fscanf", "sscanf",
        "malloc", "calloc", "realloc", "free",
        "memcpy", "memmove", "memset", "memcmp",
        "strcpy", "strncpy", "strcat", "strncat",
        "strcmp", "strncmp", "strlen",
        "fopen", "fclose", "fread", "fwrite",
        "exit", "abort", "NULL", "EOF",
        "main",
        "std", "cout", "cin", "cerr", "endl", "string", "vector",
        "map", "set", "list", "deque", "queue", "stack",
        "pair", "make_pair", "tuple", "make_tuple",
        "shared_ptr", "unique_ptr", "weak_ptr", "make_shared", "make_unique",
        "begin", "end", "size", "empty", "push_back", "pop_back",
        "insert", "erase", "find", "clear", "sort", "reverse",
        "move", "forward", "swap",
        "runtime_error", "logic_error", "invalid_argument",
        "out_of_range", "overflow_error",
        "exception", "what",
    },
    "bash": {
        "echo", "printf", "read", "exit", "return", "source",
        "export", "local", "declare", "typeset", "readonly",
        "shift", "set", "unset", "eval", "exec", "builtin",
        "cd", "pwd", "ls", "mkdir", "rmdir", "rm", "cp", "mv",
        "cat", "grep", "sed", "awk", "sort", "uniq", "wc",
        "find", "xargs", "cut", "tr", "head", "tail",
        "test", "true", "false",
        "IFS", "PATH", "HOME", "USER", "SHELL", "PWD",
        "BASH", "BASH_VERSION", "BASH_SOURCE", "FUNCNAME",
        "LINENO", "RANDOM", "SECONDS", "PIPESTATUS",
    },
    "perl": {
        "print", "say", "printf", "sprintf", "die", "warn",
        "open", "close", "read", "write", "eof", "binmode",
        "push", "pop", "shift", "unshift", "splice", "join", "split",
        "length", "substr", "index", "rindex", "uc", "lc", "ucfirst", "lcfirst",
        "defined", "undef", "ref", "bless", "tied",
        "chomp", "chop", "chdir", "mkdir", "rmdir", "rename", "unlink",
        "stat", "opendir", "readdir", "closedir",
        "exit", "system", "exec",
        "scalar", "wantarray",
        "STDIN", "STDOUT", "STDERR",
        "ARGV", "ENV", "INC",
    },
}

# Token type string prefixes that should NEVER be transformed
_NON_TRANSFORM_NAME_PREFIXES = (
    "Token.Name.Builtin",
    "Token.Name.Exception",
    "Token.Name.Namespace",
    "Token.Name.Decorator",
    "Token.Name.Label",
    "Token.Name.Entity",
    "Token.Name.Attribute",  # XML/HTML attributes
    "Token.Name.Tag",        # XML/HTML tags
)


def _ttype_str(ttype) -> str:
    return str(ttype)


def _is_name_type(ttype_s: str) -> bool:
    return ttype_s == "Token.Name" or ttype_s.startswith("Token.Name.")


def _is_transformable(ttype_s: str, value: str, extra: Set[str]) -> bool:
    """Return True if this token should be treated as a transformable IDENTIFIER."""
    if not _is_name_type(ttype_s):
        return False

    # Exclude specific Name sub-hierarchies
    for prefix in _NON_TRANSFORM_NAME_PREFIXES:
        if ttype_s == prefix or ttype_s.startswith(prefix + "."):
            return False

    # Exclude language-specific builtins
    if value in extra:
        return False

    # Must be a valid identifier
    if not value or not value.isidentifier():
        return False

    # Exclude dunder names
    if value.startswith("__") and value.endswith("__"):
        return False

    return True


def _pygments_kind(ttype_s: str, value: str, extra: Set[str]) -> TokenKind:
    """Map a pygments token type string to our TokenKind."""
    if _is_name_type(ttype_s):
        if _is_transformable(ttype_s, value, extra):
            return TokenKind.IDENTIFIER
        return TokenKind.BUILTIN

    if ttype_s.startswith("Token.Keyword"):
        return TokenKind.KEYWORD

    if ttype_s.startswith("Token.Comment"):
        return TokenKind.COMMENT

    if ttype_s.startswith("Token.Literal"):
        return TokenKind.LITERAL

    if ttype_s.startswith("Token.Error"):
        return TokenKind.OTHER

    return TokenKind.SYNTAX


class CodeLexer(BaseLexer):
    """Tokenise source code using Pygments, marking user identifiers.

    Losslessness guarantee: pygments always appends a trailing '\\n'.
    We detect and strip this if the original source did not end with '\\n'.
    """

    def __init__(self, lang: str) -> None:
        self.lang = lang
        self._extra: Set[str] = _EXTRA_BUILTINS.get(lang, set())
        self._pyg_lexer = get_lexer_by_name(lang, stripnl=False, stripall=False)

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        for ttype, value in lex(source, self._pyg_lexer):
            ttype_s = _ttype_str(ttype)
            kind = _pygments_kind(ttype_s, value, self._extra)
            tokens.append(Token(kind, value))

        # Pygments always appends a trailing '\n' even if the source doesn't have one.
        # Detect and remove it to preserve losslessness.
        reconstructed = "".join(t.value for t in tokens)
        if reconstructed != source:
            if reconstructed == source + "\n" and tokens:
                last = tokens[-1]
                if last.value == "\n":
                    tokens.pop()
                elif last.value.endswith("\n"):
                    tokens[-1] = Token(last.kind, last.value[:-1])

        return tokens
