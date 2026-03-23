"""Tests for transform strategies."""
import tempfile
import os
import pytest

from bijection.core.bijection_map import BijectionMap
from bijection.strategies.sequential import SequentialStrategy
from bijection.strategies.hash_strategy import HashStrategy
from bijection.strategies.dict_strategy import DictStrategy


class TestSequentialStrategy:
    def test_generates_bij_prefix(self):
        bm = BijectionMap()
        s = SequentialStrategy()
        s.generate_mappings(["foo", "bar", "baz"], bm)
        for v in bm.forward_map.values():
            assert v.startswith("bij_")

    def test_sequential_numbering(self):
        bm = BijectionMap()
        s = SequentialStrategy()
        s.generate_mappings(["a", "b", "c"], bm)
        values = list(bm.forward_map.values())
        assert "bij_0001" in values
        assert "bij_0002" in values
        assert "bij_0003" in values

    def test_idempotent(self):
        bm = BijectionMap()
        s = SequentialStrategy()
        s.generate_mappings(["foo"], bm)
        s.generate_mappings(["foo"], bm)  # second call — should not change anything
        assert len(bm) == 1

    def test_no_collisions(self):
        bm = BijectionMap()
        s = SequentialStrategy()
        words = [f"word_{i}" for i in range(100)]
        s.generate_mappings(words, bm)
        assert len(bm) == 100
        values = list(bm.forward_map.values())
        assert len(values) == len(set(values))  # all unique


class TestHashStrategy:
    def test_generates_b_prefix(self):
        bm = BijectionMap()
        s = HashStrategy()
        s.generate_mappings(["foo", "bar"], bm)
        for v in bm.forward_map.values():
            assert v.startswith("b_")

    def test_deterministic(self):
        bm1 = BijectionMap()
        bm2 = BijectionMap()
        HashStrategy().generate_mappings(["hello"], bm1)
        HashStrategy().generate_mappings(["hello"], bm2)
        assert bm1.forward("hello") == bm2.forward("hello")

    def test_no_collisions(self):
        bm = BijectionMap()
        s = HashStrategy()
        words = [f"identifier_{i}" for i in range(50)]
        s.generate_mappings(words, bm)
        values = list(bm.forward_map.values())
        assert len(values) == len(set(values))


class TestDictStrategy:
    def test_uses_word_list(self):
        bm = BijectionMap()
        s = DictStrategy(words=["alpha", "beta", "gamma"])
        s.generate_mappings(["x", "y", "z"], bm)
        assert bm.forward("x") == "alpha"
        assert bm.forward("y") == "beta"
        assert bm.forward("z") == "gamma"

    def test_fallback_when_exhausted(self):
        bm = BijectionMap()
        s = DictStrategy(words=["alpha"])
        s.generate_mappings(["x", "y"], bm)
        assert bm.forward("x") == "alpha"
        # y should fall back to sequential
        assert bm.forward("y") is not None
        assert bm.forward("y") != "alpha"

    def test_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("apple\nbanana\ncherry\n")
            fname = f.name
        try:
            bm = BijectionMap()
            s = DictStrategy(dict_path=fname)
            s.generate_mappings(["a", "b", "c"], bm)
            assert bm.forward("a") == "apple"
            assert bm.forward("b") == "banana"
            assert bm.forward("c") == "cherry"
        finally:
            os.unlink(fname)
