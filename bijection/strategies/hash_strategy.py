"""Hash strategy: b_<first8 of sha256>."""
import hashlib
from typing import List

from bijection.core.bijection_map import BijectionMap
from bijection.strategies.base import BaseStrategy


class HashStrategy(BaseStrategy):
    """Replaces identifiers with a hash-derived name: b_<sha256[:8]>."""

    PREFIX = "b_"

    def generate_mappings(self, identifiers: List[str], bmap: BijectionMap) -> None:
        for original in identifiers:
            if bmap.has_original(original):
                continue
            transformed = self._make_name(original, bmap)
            bmap.add(original, transformed)

    def _make_name(self, original: str, bmap: BijectionMap) -> str:
        digest = hashlib.sha256(original.encode()).hexdigest()
        candidate = f"{self.PREFIX}{digest[:8]}"
        if not bmap.has_transformed(candidate):
            return candidate
        # Collision — extend hash
        for length in range(9, 33):
            candidate = f"{self.PREFIX}{digest[:length]}"
            if not bmap.has_transformed(candidate):
                return candidate
        # Extremely unlikely but handle gracefully
        n = 2
        while True:
            candidate = f"{self.PREFIX}{digest[:8]}_{n}"
            if not bmap.has_transformed(candidate):
                return candidate
            n += 1
