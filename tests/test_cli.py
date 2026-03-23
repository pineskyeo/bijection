"""Tests for the CLI interface."""
import os
import tempfile
import shutil

import pytest

from bijection.cli import main

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestCLI:
    def test_transform_and_restore_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = os.path.join(tmpdir, "map.json")
            transformed = os.path.join(tmpdir, "sample.py")
            restored = os.path.join(tmpdir, "restored.py")
            src = os.path.join(FIXTURES_DIR, "sample.py")

            # Transform
            rc = main(["transform", src, transformed, "--map", map_path])
            assert rc == 0
            assert os.path.exists(transformed)
            assert os.path.exists(map_path)

            # Restore
            rc = main(["restore", transformed, restored, "--map", map_path])
            assert rc == 0

            # Verify round-trip
            with open(src) as fa, open(restored) as fb:
                assert fa.read() == fb.read()

    def test_verify_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = os.path.join(tmpdir, "map.json")
            transformed_dir = os.path.join(tmpdir, "transformed")
            src = os.path.join(FIXTURES_DIR, "sample.py")
            dst = os.path.join(transformed_dir, "sample.py")
            os.makedirs(transformed_dir, exist_ok=True)

            main(["transform", src, dst, "--map", map_path])
            rc = main(["verify", src, "--map", map_path])
            assert rc == 0

    def test_show_map_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = os.path.join(tmpdir, "map.json")
            src = os.path.join(FIXTURES_DIR, "sample.py")
            dst = os.path.join(tmpdir, "sample.py")
            main(["transform", src, dst, "--map", map_path])
            rc = main(["show-map", "--map", map_path])
            assert rc == 0

    def test_transform_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = os.path.join(tmpdir, "map.json")
            transformed_dir = os.path.join(tmpdir, "transformed")
            restored_dir = os.path.join(tmpdir, "restored")

            rc = main(["transform", FIXTURES_DIR, transformed_dir, "--map", map_path])
            assert rc == 0

            rc = main(["restore", transformed_dir, restored_dir, "--map", map_path])
            assert rc == 0

            for fname in ["sample.py", "sample.c", "sample.json"]:
                orig = os.path.join(FIXTURES_DIR, fname)
                rest = os.path.join(restored_dir, fname)
                with open(orig) as fa, open(rest) as fb:
                    assert fa.read() == fb.read(), f"CLI directory round-trip failed: {fname}"

    def test_hash_strategy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = os.path.join(tmpdir, "map.json")
            transformed = os.path.join(tmpdir, "sample.py")
            restored = os.path.join(tmpdir, "restored.py")
            src = os.path.join(FIXTURES_DIR, "sample.py")

            main(["transform", src, transformed, "--map", map_path, "--strategy", "hash"])
            main(["restore", transformed, restored, "--map", map_path])

            with open(src) as fa, open(restored) as fb:
                assert fa.read() == fb.read()

    def test_dict_strategy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dict_path = os.path.join(tmpdir, "words.txt")
            with open(dict_path, "w") as f:
                for word in ["alpha", "beta", "gamma", "delta", "epsilon",
                             "zeta", "eta", "theta", "iota", "kappa",
                             "lambda_", "mu", "nu", "xi", "omicron",
                             "pi_", "rho", "sigma", "tau", "upsilon",
                             "phi", "chi", "psi", "omega", "aleph",
                             "beth", "gimel", "dalet", "he_", "vav",
                             "zayin", "chet", "tet", "yod", "kaf"]:
                    f.write(word + "\n")

            map_path = os.path.join(tmpdir, "map.json")
            transformed = os.path.join(tmpdir, "sample.py")
            restored = os.path.join(tmpdir, "restored.py")
            src = os.path.join(FIXTURES_DIR, "sample.py")

            main(["transform", src, transformed, "--map", map_path,
                  "--strategy", "dict", "--dict", dict_path])
            main(["restore", transformed, restored, "--map", map_path])

            with open(src) as fa, open(restored) as fb:
                assert fa.read() == fb.read()

    def test_restore_missing_map_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc = main(["restore", FIXTURES_DIR, tmpdir,
                       "--map", os.path.join(tmpdir, "nonexistent.json")])
            assert rc == 1
