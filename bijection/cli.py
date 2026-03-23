"""Command-line interface for bijection."""
import argparse
import json
import os
import sys
from typing import List, Optional

from bijection.core.bijection_map import BijectionMap
from bijection.core.engine import Engine
from bijection.strategies import get_strategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijection",
        description="Reversible identifier transformation for source files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── transform ──────────────────────────────────────────────────────
    p_t = sub.add_parser("transform", help="Transform identifiers in source files.")
    p_t.add_argument("source", help="Source file or directory.")
    p_t.add_argument("dest", help="Destination file or directory for transformed output.")
    p_t.add_argument(
        "--map", default="bijection_map.json",
        help="Path to bijection map file (created/updated). Default: bijection_map.json",
    )
    p_t.add_argument(
        "--strategy", default="sequential",
        choices=["sequential", "hash", "dict"],
        help="Naming strategy for transformed identifiers. Default: sequential",
    )
    p_t.add_argument(
        "--dict", dest="dict_path", default=None,
        help="Path to word list file (required when --strategy=dict).",
    )
    p_t.add_argument(
        "--ext", nargs="*", default=None,
        help="File extensions to include (e.g. --ext py c cpp). Default: all supported.",
    )

    # ── restore ────────────────────────────────────────────────────────
    p_r = sub.add_parser("restore", help="Restore transformed files to their originals.")
    p_r.add_argument("source", help="Transformed file or directory.")
    p_r.add_argument("dest", help="Destination file or directory for restored output.")
    p_r.add_argument(
        "--map", default="bijection_map.json",
        help="Path to bijection map file. Default: bijection_map.json",
    )
    p_r.add_argument(
        "--ext", nargs="*", default=None,
        help="File extensions to include.",
    )

    # ── verify ─────────────────────────────────────────────────────────
    p_v = sub.add_parser(
        "verify",
        help="Verify that transform→restore round-trip reproduces the original exactly.",
    )
    p_v.add_argument("source", help="Original source file or directory.")
    p_v.add_argument(
        "--map", default="bijection_map.json",
        help="Path to bijection map file. Default: bijection_map.json",
    )
    p_v.add_argument(
        "--ext", nargs="*", default=None,
        help="File extensions to include.",
    )

    # ── show-map ───────────────────────────────────────────────────────
    p_s = sub.add_parser("show-map", help="Pretty-print the bijection map.")
    p_s.add_argument(
        "--map", default="bijection_map.json",
        help="Path to bijection map file. Default: bijection_map.json",
    )

    return parser


# ------------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------------

def cmd_transform(args: argparse.Namespace) -> int:
    strategy_kwargs = {}
    if args.strategy == "dict":
        if not args.dict_path:
            print("ERROR: --dict is required when using --strategy=dict", file=sys.stderr)
            return 1
        strategy_kwargs["dict_path"] = args.dict_path

    strategy = get_strategy(args.strategy, **strategy_kwargs)

    # Load existing map if present
    bmap = BijectionMap()
    if os.path.exists(args.map):
        bmap = BijectionMap.load(args.map)
        print(f"Loaded existing map: {args.map} ({len(bmap)} entries)")

    engine = Engine(bmap, strategy)

    if os.path.isfile(args.source):
        count = engine.transform_file(args.source, args.dest)
        print(f"Transformed {args.source} → {args.dest}  ({count} identifiers replaced)")
    else:
        results = engine.transform_directory(args.source, args.dest, args.ext)
        _print_results(results, "replaced")

    bmap.save(args.map)
    print(f"Map saved: {args.map} ({len(bmap)} entries total)")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"ERROR: map file not found: {args.map}", file=sys.stderr)
        return 1

    bmap = BijectionMap.load(args.map)
    engine = Engine(bmap, strategy=None)  # type: ignore[arg-type]

    if os.path.isfile(args.source):
        count = engine.restore_file(args.source, args.dest)
        print(f"Restored {args.source} → {args.dest}  ({count} identifiers restored)")
    else:
        results = engine.restore_directory(args.source, args.dest, args.ext)
        _print_results(results, "restored")

    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Transform to a temp dir, restore, then diff against original."""
    import tempfile
    import shutil

    if not os.path.exists(args.map):
        print(f"ERROR: map file not found: {args.map}", file=sys.stderr)
        return 1

    bmap = BijectionMap.load(args.map)
    strategy = get_strategy("sequential")
    engine = Engine(bmap, strategy)

    with tempfile.TemporaryDirectory() as tmpdir:
        transformed_dir = os.path.join(tmpdir, "transformed")
        restored_dir = os.path.join(tmpdir, "restored")

        if os.path.isfile(args.source):
            tfile = os.path.join(transformed_dir, os.path.basename(args.source))
            rfile = os.path.join(restored_dir, os.path.basename(args.source))
            os.makedirs(transformed_dir, exist_ok=True)
            os.makedirs(restored_dir, exist_ok=True)
            engine.transform_file(args.source, tfile)
            engine.restore_file(tfile, rfile)
            ok = _compare_files(args.source, rfile)
            if ok:
                print(f"OK  {args.source}")
                return 0
            else:
                print(f"FAIL  {args.source}")
                return 1
        else:
            from bijection.core.engine import _walk, SUPPORTED_EXTENSIONS
            allowed = (
                {e if e.startswith(".") else "." + e for e in args.ext}
                if args.ext else SUPPORTED_EXTENSIONS
            )
            failures = 0
            for rel in _walk(args.source, args.ext):
                src = os.path.join(args.source, rel)
                tfile = os.path.join(transformed_dir, rel)
                rfile = os.path.join(restored_dir, rel)
                os.makedirs(os.path.dirname(tfile), exist_ok=True)
                os.makedirs(os.path.dirname(rfile), exist_ok=True)
                engine.transform_file(src, tfile)
                engine.restore_file(tfile, rfile)
                ok = _compare_files(src, rfile)
                status = "OK  " if ok else "FAIL"
                print(f"{status}  {rel}")
                if not ok:
                    failures += 1
            if failures:
                print(f"\n{failures} file(s) failed verification.")
                return 1
            print("\nAll files verified successfully.")
            return 0


def cmd_show_map(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"Map file not found: {args.map}", file=sys.stderr)
        return 1
    bmap = BijectionMap.load(args.map)
    print(f"Bijection map ({len(bmap)} entries):")
    for original, transformed in sorted(bmap.forward_map.items()):
        print(f"  {original:30s} → {transformed}")
    return 0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _print_results(results: dict, verb: str) -> None:
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    errors = [(f, r) for f, r in results.items() if r["status"] == "error"]
    for fname, r in results.items():
        if r["status"] == "ok":
            print(f"  OK    {fname}  ({r.get(verb, 0)} identifiers {verb})")
        else:
            print(f"  ERROR {fname}  {r['error']}")
    print(f"\nDone: {ok} ok, {len(errors)} errors")


def _compare_files(path_a: str, path_b: str) -> bool:
    try:
        with open(path_a, "r", encoding="utf-8", errors="replace") as fa:
            a = fa.read()
        with open(path_b, "r", encoding="utf-8", errors="replace") as fb:
            b = fb.read()
        return a == b
    except Exception:
        return False


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "transform": cmd_transform,
        "restore": cmd_restore,
        "verify": cmd_verify,
        "show-map": cmd_show_map,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
