"""YAML lexer — transforms mapping keys using the PyYAML event stream."""
import re
from typing import List

import yaml

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer


class YamlLexer(BaseLexer):
    """Transforms YAML mapping keys.

    Strategy:
        1. Use PyYAML's parser to identify key values and their positions.
        2. Use a character-scan approach to emit tokens that cover the source
           exactly, marking key strings as IDENTIFIER.

    Because YAML is complex (anchors, flow style, multi-line strings, etc.),
    we take a conservative approach: only plain (unquoted) scalar keys are
    transformed; quoted keys and block scalars are left as LITERAL.
    """

    def tokenize(self, source: str) -> List[Token]:
        keys = self._extract_keys(source)
        return self._scan_tokens(source, keys)

    # ------------------------------------------------------------------

    def _extract_keys(self, source: str) -> set:
        """Return the set of all mapping key strings in the YAML document."""
        keys: set = set()
        try:
            self._walk(yaml.safe_load(source), keys)
        except yaml.YAMLError:
            pass
        return keys

    def _walk(self, node, keys: set) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and k.isidentifier():
                    keys.add(k)
                self._walk(v, keys)
        elif isinstance(node, list):
            for item in node:
                self._walk(item, keys)

    def _scan_tokens(self, source: str, keys: set) -> List[Token]:
        """Character scan that emits IDENTIFIER for key occurrences."""
        tokens: List[Token] = []
        i = 0
        n = len(source)

        # Build a pattern that matches any key on a mapping line.
        # A YAML key on a line looks like:  ^(\s*)(key_word)(\s*:)
        # We only replace the word, not the surrounding whitespace or colon.
        if keys:
            # Sort by length descending so longer keys match first
            sorted_keys = sorted(keys, key=len, reverse=True)
            key_pattern = re.compile(
                r'(?<![a-zA-Z0-9_])(' + '|'.join(re.escape(k) for k in sorted_keys) + r')(?=\s*:)'
            )
        else:
            key_pattern = None

        buf = ""
        while i < n:
            if key_pattern:
                m = key_pattern.search(source, i)
                if m:
                    # Emit everything before the match as SYNTAX
                    before = source[i:m.start()]
                    if before:
                        tokens.append(Token(TokenKind.SYNTAX, before))
                    # Emit the key as IDENTIFIER
                    tokens.append(Token(TokenKind.IDENTIFIER, m.group(1)))
                    i = m.end()
                    continue
            # No more keys found — emit remainder
            tokens.append(Token(TokenKind.SYNTAX, source[i:]))
            break

        return tokens if tokens else [Token(TokenKind.SYNTAX, source)]
