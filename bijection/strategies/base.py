"""Abstract base strategy."""
from abc import ABC, abstractmethod
from typing import List

from bijection.core.bijection_map import BijectionMap


class BaseStrategy(ABC):
    """A strategy generates transformed names for a list of original identifiers."""

    @abstractmethod
    def generate_mappings(self, identifiers: List[str], bmap: BijectionMap) -> None:
        """Populate *bmap* with mappings for each identifier in *identifiers*.

        Must not overwrite existing mappings (idempotent).
        Must maintain the bijection invariant.
        """
        raise NotImplementedError

    def _next_available(self, candidate: str, bmap: BijectionMap, suffix_fn) -> str:
        """Return *candidate* if not already a transformed value, else try suffix_fn(n)."""
        if not bmap.has_transformed(candidate):
            return candidate
        n = 2
        while True:
            attempt = suffix_fn(n)
            if not bmap.has_transformed(attempt):
                return attempt
            n += 1
