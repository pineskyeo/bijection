"""Tests for BijectionMap."""
import json
import os
import tempfile
import pytest

from bijection.core.bijection_map import BijectionMap, BijectionError


class TestBijectionMap:
    def test_add_and_forward(self):
        bm = BijectionMap()
        bm.add("foo", "bij_0001")
        assert bm.forward("foo") == "bij_0001"

    def test_add_and_inverse(self):
        bm = BijectionMap()
        bm.add("foo", "bij_0001")
        assert bm.inverse("bij_0001") == "foo"

    def test_idempotent_add(self):
        bm = BijectionMap()
        bm.add("foo", "bij_0001")
        bm.add("foo", "bij_0001")  # same mapping — should not raise
        assert len(bm) == 1

    def test_forward_collision_raises(self):
        bm = BijectionMap()
        bm.add("foo", "bij_0001")
        with pytest.raises(BijectionError):
            bm.add("foo", "bij_0002")  # foo already maps to bij_0001

    def test_inverse_collision_raises(self):
        bm = BijectionMap()
        bm.add("foo", "bij_0001")
        with pytest.raises(BijectionError):
            bm.add("bar", "bij_0001")  # bij_0001 is already an image

    def test_missing_returns_none(self):
        bm = BijectionMap()
        assert bm.forward("unknown") is None
        assert bm.inverse("unknown") is None

    def test_bijection_invariant(self):
        bm = BijectionMap()
        words = ["alpha", "beta", "gamma", "delta"]
        transformed = ["bij_0001", "bij_0002", "bij_0003", "bij_0004"]
        for w, t in zip(words, transformed):
            bm.add(w, t)
        for w, t in zip(words, transformed):
            assert bm.inverse(bm.forward(w)) == w
            assert bm.forward(bm.inverse(t)) == t

    def test_save_and_load(self):
        bm = BijectionMap()
        bm.add("foo", "bij_0001")
        bm.add("bar", "bij_0002")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "map.json")
            bm.save(path)
            loaded = BijectionMap.load(path)
        assert loaded.forward("foo") == "bij_0001"
        assert loaded.forward("bar") == "bij_0002"
        assert loaded.inverse("bij_0001") == "foo"
        assert loaded.inverse("bij_0002") == "bar"

    def test_len(self):
        bm = BijectionMap()
        assert len(bm) == 0
        bm.add("x", "y")
        assert len(bm) == 1
