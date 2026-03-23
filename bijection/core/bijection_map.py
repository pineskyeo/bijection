"""Bidirectional mapping that enforces the bijection invariant."""
import json
import os
from typing import Dict, Optional


class BijectionError(Exception):
    pass


class BijectionMap:
    """Maintains a 1-to-1 mapping between original and transformed identifiers.

    Invariant: inverse[forward[x]] == x  for all x in the map.
    """

    def __init__(self) -> None:
        self._forward: Dict[str, str] = {}   # original -> transformed
        self._inverse: Dict[str, str] = {}   # transformed -> original

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, original: str, transformed: str) -> None:
        """Register a mapping.  Raises BijectionError on collision."""
        if original in self._forward:
            if self._forward[original] != transformed:
                raise BijectionError(
                    f"Collision: '{original}' is already mapped to "
                    f"'{self._forward[original]}', cannot remap to '{transformed}'"
                )
            return  # idempotent

        if transformed in self._inverse:
            raise BijectionError(
                f"Collision: '{transformed}' is already the image of "
                f"'{self._inverse[transformed]}', cannot also map '{original}' to it"
            )

        self._forward[original] = transformed
        self._inverse[transformed] = original

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def forward(self, original: str) -> Optional[str]:
        return self._forward.get(original)

    def inverse(self, transformed: str) -> Optional[str]:
        return self._inverse.get(transformed)

    def has_original(self, original: str) -> bool:
        return original in self._forward

    def has_transformed(self, transformed: str) -> bool:
        return transformed in self._inverse

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        data = {"forward": self._forward}
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "BijectionMap":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        bm = cls()
        for original, transformed in data["forward"].items():
            bm.add(original, transformed)
        return bm

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._forward)

    def __repr__(self) -> str:
        return f"BijectionMap({len(self)} entries)"

    @property
    def forward_map(self) -> Dict[str, str]:
        return dict(self._forward)

    @property
    def inverse_map(self) -> Dict[str, str]:
        return dict(self._inverse)
