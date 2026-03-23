"""Dictionary strategy: substitute from a user-provided word list."""
from typing import List, Optional

from bijection.core.bijection_map import BijectionMap
from bijection.strategies.base import BaseStrategy
from bijection.strategies.sequential import SequentialStrategy


class DictStrategy(BaseStrategy):
    """Replaces identifiers with words from a dictionary file.

    Words that are already used or exhausted fall back to the sequential strategy.
    """

    def __init__(self, dict_path: Optional[str] = None, words: Optional[List[str]] = None) -> None:
        if words is not None:
            self._words = [w.strip() for w in words if w.strip().isidentifier()]
        elif dict_path is not None:
            with open(dict_path, "r", encoding="utf-8") as fh:
                self._words = [line.strip() for line in fh if line.strip().isidentifier()]
        else:
            raise ValueError("DictStrategy requires either dict_path or words")

        self._index = 0
        self._fallback = SequentialStrategy()

    def generate_mappings(self, identifiers: List[str], bmap: BijectionMap) -> None:
        for original in identifiers:
            if bmap.has_original(original):
                continue
            transformed = self._next_word(bmap)
            bmap.add(original, transformed)

    def _next_word(self, bmap: BijectionMap) -> str:
        while self._index < len(self._words):
            word = self._words[self._index]
            self._index += 1
            if not bmap.has_transformed(word):
                return word
        # Dictionary exhausted — fall back to sequential
        return self._fallback._next_name(bmap)
