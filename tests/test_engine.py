"""Integration tests for the Engine — round-trip bijection verification."""
import os
import shutil
import tempfile

import pytest

from bijection.core.bijection_map import BijectionMap
from bijection.core.engine import Engine
from bijection.strategies.sequential import SequentialStrategy
from bijection.strategies.hash_strategy import HashStrategy

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

FIXTURE_FILES = [
    "sample.py",
    "sample.c",
    "sample.cpp",
    "sample.sh",
    "sample.pl",
    "sample.json",
    "sample.yaml",
    "sample.ini",
    "sample.md",
]


def _round_trip(fixture_name: str, strategy_cls=SequentialStrategy) -> bool:
    """Transform then restore a fixture file and check byte-for-byte equality."""
    src = os.path.join(FIXTURES_DIR, fixture_name)
    with tempfile.TemporaryDirectory() as tmpdir:
        transformed = os.path.join(tmpdir, "transformed_" + fixture_name)
        restored = os.path.join(tmpdir, "restored_" + fixture_name)

        bmap = BijectionMap()
        strategy = strategy_cls()
        engine = Engine(bmap, strategy)

        engine.transform_file(src, transformed)
        engine.restore_file(transformed, restored)

        with open(src, encoding="utf-8") as fa, open(restored, encoding="utf-8") as fb:
            return fa.read() == fb.read()


class TestRoundTripSequential:
    @pytest.mark.parametrize("fname", FIXTURE_FILES)
    def test_round_trip(self, fname):
        assert _round_trip(fname, SequentialStrategy), (
            f"Round-trip failed for {fname} with SequentialStrategy"
        )


class TestRoundTripHash:
    @pytest.mark.parametrize("fname", FIXTURE_FILES)
    def test_round_trip(self, fname):
        assert _round_trip(fname, HashStrategy), (
            f"Round-trip failed for {fname} with HashStrategy"
        )


class TestTransformChangesContent:
    """Verify that at least some identifiers are actually renamed."""

    def test_python_identifiers_renamed(self):
        src = os.path.join(FIXTURES_DIR, "sample.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            transformed = os.path.join(tmpdir, "t.py")
            bmap = BijectionMap()
            engine = Engine(bmap, SequentialStrategy())
            count = engine.transform_file(src, transformed)
            assert count > 0, "No identifiers were transformed"
            with open(src) as fa, open(transformed) as fb:
                assert fa.read() != fb.read(), "Transformed file is identical to source"

    def test_c_identifiers_renamed(self):
        src = os.path.join(FIXTURES_DIR, "sample.c")
        with tempfile.TemporaryDirectory() as tmpdir:
            transformed = os.path.join(tmpdir, "t.c")
            bmap = BijectionMap()
            engine = Engine(bmap, SequentialStrategy())
            count = engine.transform_file(src, transformed)
            assert count > 0

    def test_json_keys_renamed(self):
        src = os.path.join(FIXTURES_DIR, "sample.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            transformed = os.path.join(tmpdir, "t.json")
            bmap = BijectionMap()
            engine = Engine(bmap, SequentialStrategy())
            count = engine.transform_file(src, transformed)
            assert count > 0


class TestDirectoryTransform:
    def test_directory_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transformed_dir = os.path.join(tmpdir, "transformed")
            restored_dir = os.path.join(tmpdir, "restored")

            bmap = BijectionMap()
            engine = Engine(bmap, SequentialStrategy())

            results = engine.transform_directory(FIXTURES_DIR, transformed_dir)
            assert any(r["status"] == "ok" for r in results.values())

            results2 = engine.restore_directory(transformed_dir, restored_dir)
            assert any(r["status"] == "ok" for r in results2.values())

            for fname in FIXTURE_FILES:
                orig = os.path.join(FIXTURES_DIR, fname)
                rest = os.path.join(restored_dir, fname)
                with open(orig, encoding="utf-8") as fa, open(rest, encoding="utf-8") as fb:
                    orig_content = fa.read()
                    rest_content = fb.read()
                    assert orig_content == rest_content, (
                        f"Directory round-trip failed for {fname}"
                    )


class TestMapPersistence:
    def test_map_saved_and_reloaded(self):
        src = os.path.join(FIXTURES_DIR, "sample.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = os.path.join(tmpdir, "map.json")
            transformed = os.path.join(tmpdir, "t.py")
            restored = os.path.join(tmpdir, "r.py")

            bmap = BijectionMap()
            engine = Engine(bmap, SequentialStrategy())
            engine.transform_file(src, transformed)
            bmap.save(map_path)

            # Load fresh map and restore
            bmap2 = BijectionMap.load(map_path)
            engine2 = Engine(bmap2, SequentialStrategy())
            engine2.restore_file(transformed, restored)

            with open(src) as fa, open(restored) as fb:
                assert fa.read() == fb.read()
