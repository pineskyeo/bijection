"""Tests for all lexers — primarily verifying losslessness."""
import os
import pytest

from bijection.core.token import TokenKind
from bijection.lexers.base import BaseLexer
from bijection.lexers.code_lexer import CodeLexer
from bijection.lexers.json_lexer import JsonLexer
from bijection.lexers.yaml_lexer import YamlLexer
from bijection.lexers.ini_lexer import IniLexer
from bijection.lexers.markdown_lexer import MarkdownLexer

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(fname: str) -> str:
    with open(os.path.join(FIXTURES_DIR, fname), encoding="utf-8") as fh:
        return fh.read()


def _assert_lossless(lexer: BaseLexer, source: str) -> None:
    tokens = lexer.tokenize(source)
    reconstructed = "".join(t.value for t in tokens)
    assert reconstructed == source, (
        f"Lexer {lexer.__class__.__name__} is not lossless!\n"
        f"  source length: {len(source)}, reconstructed: {len(reconstructed)}"
    )


def _identifiers(lexer: BaseLexer, source: str):
    tokens = lexer.tokenize(source)
    return [t.value for t in tokens if t.kind == TokenKind.IDENTIFIER]


# ------------------------------------------------------------------
# Losslessness tests
# ------------------------------------------------------------------

class TestLossless:
    def test_python(self):
        _assert_lossless(CodeLexer("python"), _read("sample.py"))

    def test_c(self):
        _assert_lossless(CodeLexer("c"), _read("sample.c"))

    def test_cpp(self):
        _assert_lossless(CodeLexer("cpp"), _read("sample.cpp"))

    def test_shell(self):
        _assert_lossless(CodeLexer("bash"), _read("sample.sh"))

    def test_perl(self):
        _assert_lossless(CodeLexer("perl"), _read("sample.pl"))

    def test_json(self):
        _assert_lossless(JsonLexer(), _read("sample.json"))

    def test_yaml(self):
        _assert_lossless(YamlLexer(), _read("sample.yaml"))

    def test_ini(self):
        _assert_lossless(IniLexer(), _read("sample.ini"))

    def test_markdown(self):
        _assert_lossless(MarkdownLexer(), _read("sample.md"))


# ------------------------------------------------------------------
# Identifier extraction tests
# ------------------------------------------------------------------

class TestIdentifierExtraction:
    def test_python_extracts_function_names(self):
        ids = _identifiers(CodeLexer("python"), _read("sample.py"))
        assert "calculate_area" in ids
        assert "greet_user" in ids
        assert "ShapeCalculator" in ids

    def test_python_excludes_keywords(self):
        ids = _identifiers(CodeLexer("python"), _read("sample.py"))
        assert "def" not in ids
        assert "if" not in ids
        assert "return" not in ids
        assert "class" not in ids

    def test_python_excludes_builtins(self):
        ids = _identifiers(CodeLexer("python"), _read("sample.py"))
        assert "print" not in ids

    def test_c_extracts_function_names(self):
        ids = _identifiers(CodeLexer("c"), _read("sample.c"))
        assert "add_numbers" in ids
        assert "multiply_values" in ids

    def test_c_excludes_keywords(self):
        ids = _identifiers(CodeLexer("c"), _read("sample.c"))
        assert "int" not in ids
        assert "return" not in ids
        assert "void" not in ids

    def test_c_excludes_printf(self):
        ids = _identifiers(CodeLexer("c"), _read("sample.c"))
        assert "printf" not in ids

    def test_json_extracts_keys(self):
        ids = _identifiers(JsonLexer(), _read("sample.json"))
        assert "database_config" in ids
        assert "host_address" in ids
        assert "port_number" in ids

    def test_ini_extracts_sections_and_keys(self):
        ids = _identifiers(IniLexer(), _read("sample.ini"))
        assert "database_section" in ids
        assert "host_name" in ids
        assert "port_number" in ids

    def test_markdown_extracts_code_identifiers(self):
        ids = _identifiers(MarkdownLexer(), _read("sample.md"))
        assert "compute_fibonacci" in ids
        assert "compute_max" in ids

    def test_yaml_extracts_keys(self):
        ids = _identifiers(YamlLexer(), _read("sample.yaml"))
        assert "database" in ids or "host" in ids  # at least some keys extracted
