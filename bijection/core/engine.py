"""Core transform / restore engine."""
import os
from typing import List, Optional

from bijection.core.bijection_map import BijectionMap
from bijection.core.token import Token, TokenKind
from bijection.lexers import get_lexer_for_file
from bijection.strategies.base import BaseStrategy


class Engine:
    """Orchestrates tokenisation, mapping, and file reconstruction."""

    def __init__(self, bmap: BijectionMap, strategy: BaseStrategy) -> None:
        self.bmap = bmap
        self.strategy = strategy

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transform_file(self, src_path: str, dst_path: str) -> int:
        """Transform *src_path* and write result to *dst_path*.

        Returns the number of identifiers replaced.
        """
        source = _read(src_path)
        lexer = get_lexer_for_file(src_path)
        tokens = lexer.tokenize(source)

        # First pass: collect all new identifiers and generate mappings
        identifiers = [
            t.value for t in tokens
            if t.kind == TokenKind.IDENTIFIER and not self.bmap.has_original(t.value)
        ]
        self.strategy.generate_mappings(identifiers, self.bmap)

        # Second pass: reconstruct
        replaced = 0
        parts: List[str] = []
        for token in tokens:
            if token.kind == TokenKind.IDENTIFIER:
                mapped = self.bmap.forward(token.value)
                if mapped is not None:
                    parts.append(mapped)
                    replaced += 1
                else:
                    parts.append(token.value)
            else:
                parts.append(token.value)

        _write(dst_path, "".join(parts))
        return replaced

    def restore_file(self, src_path: str, dst_path: str) -> int:
        """Restore a transformed file back to the original.

        Returns the number of identifiers restored.
        """
        source = _read(src_path)
        lexer = get_lexer_for_file(src_path)
        tokens = lexer.tokenize(source)

        restored = 0
        parts: List[str] = []
        for token in tokens:
            if token.kind == TokenKind.IDENTIFIER:
                original = self.bmap.inverse(token.value)
                if original is not None:
                    parts.append(original)
                    restored += 1
                else:
                    parts.append(token.value)
            else:
                parts.append(token.value)

        _write(dst_path, "".join(parts))
        return restored

    def transform_directory(
        self,
        src_dir: str,
        dst_dir: str,
        extensions: Optional[List[str]] = None,
    ) -> dict:
        """Transform all supported files under *src_dir* into *dst_dir*."""
        results = {}
        for rel_path in _walk(src_dir, extensions):
            src = os.path.join(src_dir, rel_path)
            dst = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                count = self.transform_file(src, dst)
                results[rel_path] = {"status": "ok", "replaced": count}
            except Exception as exc:
                results[rel_path] = {"status": "error", "error": str(exc)}
        return results

    def restore_directory(
        self,
        src_dir: str,
        dst_dir: str,
        extensions: Optional[List[str]] = None,
    ) -> dict:
        """Restore all supported files under *src_dir* into *dst_dir*."""
        results = {}
        for rel_path in _walk(src_dir, extensions):
            src = os.path.join(src_dir, rel_path)
            dst = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                count = self.restore_file(src, dst)
                results[rel_path] = {"status": "ok", "restored": count}
            except Exception as exc:
                results[rel_path] = {"status": "error", "error": str(exc)}
        return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


SUPPORTED_EXTENSIONS = {
    ".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
    ".sh", ".bash", ".pl", ".pm",
    ".json", ".yaml", ".yml", ".ini", ".cfg", ".md",
}


def _walk(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    allowed = (
        {e if e.startswith(".") else "." + e for e in extensions}
        if extensions
        else SUPPORTED_EXTENSIONS
    )
    results = []
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for fname in sorted(files):
            _, ext = os.path.splitext(fname)
            if ext.lower() in allowed:
                rel = os.path.relpath(os.path.join(root, fname), directory)
                results.append(rel)
    return results
