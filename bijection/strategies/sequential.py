"""Sequential strategy: bij_0001, bij_0002, ..."""
from typing import List

from bijection.core.bijection_map import BijectionMap
from bijection.strategies.base import BaseStrategy


class SequentialStrategy(BaseStrategy):
    """Replaces identifiers with sequentially numbered names like bij_0001."""

    PREFIX = "bij_"

    def __init__(self) -> None:
        self._counter = 0

    def generate_mappings(self, identifiers: List[str], bmap: BijectionMap) -> None:
        for original in identifiers:
            if bmap.has_original(original):
                continue  # already mapped
            transformed = self._next_name(bmap)
            bmap.add(original, transformed)

    def _next_name(self, bmap: BijectionMap) -> str:
        while True:
            self._counter += 1
            candidate = f"{self.PREFIX}{self._counter:04d}"
            if not bmap.has_transformed(candidate):
                return candidate
