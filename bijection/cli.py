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
    p_t.add_argument(
        "--include", dest="include_path", default=None,
        help="Path to a file listing identifiers to transform (one per line). "
             "If omitted, all identifiers are transformed.",
    )

    # ── list-identifiers ───────────────────────────────────────────────
    p_l = sub.add_parser(
        "list-identifiers",
        help="List all unique identifiers found in source files (no transformation).",
    )
    p_l.add_argument("source", help="Source file or directory.")
    p_l.add_argument(
        "--ext", nargs="*", default=None,
        help="File extensions to include.",
    )
    p_l.add_argument(
        "--output", default=None,
        help="Write identifier list to this file instead of stdout.",
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

    # ── encode-map ─────────────────────────────────────────────────────
    p_em = sub.add_parser(
        "encode-map",
        help="Encode original identifiers (map keys) to numeric strings. "
             "Transformed values (bij_*) are kept as-is.",
    )
    p_em.add_argument(
        "--map", default="bijection_map.json",
        help="Path to input bijection map file. Default: bijection_map.json",
    )
    p_em.add_argument(
        "--output", default=None,
        help="Output path for encoded map. Defaults to overwriting --map.",
    )

    # ── decode-map ─────────────────────────────────────────────────────
    p_dm = sub.add_parser(
        "decode-map",
        help="Decode numeric-encoded original identifiers back to plaintext.",
    )
    p_dm.add_argument(
        "--map", default="bijection_map.json",
        help="Path to encoded bijection map file. Default: bijection_map.json",
    )
    p_dm.add_argument(
        "--output", default=None,
        help="Output path for decoded map. Defaults to overwriting --map.",
    )

    # ── compact-map ────────────────────────────────────────────────────
    p_cm = sub.add_parser(
        "compact-map",
        help="Compact the map into two parallel arrays (minimal JSON size).",
    )
    p_cm.add_argument(
        "--map", default="bijection_map.json",
        help="Path to bijection map file. Default: bijection_map.json",
    )
    p_cm.add_argument(
        "--output", default=None,
        help="Output path. Defaults to overwriting --map.",
    )

    # ── expand-map ─────────────────────────────────────────────────────
    p_xm = sub.add_parser(
        "expand-map",
        help="Expand a compacted map back to standard {forward: {...}} format.",
    )
    p_xm.add_argument(
        "--map", default="bijection_map.json",
        help="Path to compacted map file. Default: bijection_map.json",
    )
    p_xm.add_argument(
        "--output", default=None,
        help="Output path. Defaults to overwriting --map.",
    )

    # ── pack ───────────────────────────────────────────────────────────
    p_pk = sub.add_parser(
        "pack",
        help="Transform files then encode+compact the map in one step.",
    )
    p_pk.add_argument("source", help="Source file or directory.")
    p_pk.add_argument("dest", help="Destination file or directory for transformed output.")
    p_pk.add_argument(
        "--map", default="bijection_map.json",
        help="Path to output map file. Default: bijection_map.json",
    )
    p_pk.add_argument(
        "--strategy", default="sequential",
        choices=["sequential", "hash", "dict"],
        help="Naming strategy. Default: sequential",
    )
    p_pk.add_argument("--dict", dest="dict_path", default=None)
    p_pk.add_argument("--ext", nargs="*", default=None)
    p_pk.add_argument("--include", dest="include_path", default=None)

    # ── unpack ─────────────────────────────────────────────────────────
    p_up = sub.add_parser(
        "unpack",
        help="Expand+decode map then restore files in one step.",
    )
    p_up.add_argument("source", help="Transformed file or directory.")
    p_up.add_argument("dest", help="Destination file or directory for restored output.")
    p_up.add_argument(
        "--map", default="bijection_map.json",
        help="Path to packed map file. Default: bijection_map.json",
    )
    p_up.add_argument("--ext", nargs="*", default=None)

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

    # Load include filter if specified
    include = None
    if args.include_path:
        if not os.path.exists(args.include_path):
            print(f"ERROR: include file not found: {args.include_path}", file=sys.stderr)
            return 1
        with open(args.include_path, "r", encoding="utf-8") as fh:
            include = {line.strip() for line in fh if line.strip()}
        print(f"Include filter: {len(include)} identifiers from {args.include_path}")

    engine = Engine(bmap, strategy)

    if os.path.isfile(args.source):
        count = engine.transform_file(args.source, args.dest, include=include)
        print(f"Transformed {args.source} → {args.dest}  ({count} identifiers replaced)")
    else:
        results = engine.transform_directory(args.source, args.dest, args.ext, include=include)
        _print_results(results, "replaced")

    bmap.save(args.map)
    print(f"Map saved: {args.map} ({len(bmap)} entries total)")
    return 0


def cmd_list_identifiers(args: argparse.Namespace) -> int:
    from bijection.core.bijection_map import BijectionMap
    from bijection.core.engine import Engine
    from bijection.strategies.sequential import SequentialStrategy

    engine = Engine(BijectionMap(), SequentialStrategy())

    if os.path.isfile(args.source):
        identifiers = engine.list_identifiers(args.source)
    else:
        identifiers = engine.list_identifiers_directory(args.source, args.ext)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write("\n".join(identifiers) + ("\n" if identifiers else ""))
        print(f"Wrote {len(identifiers)} identifiers to {args.output}")
    else:
        for ident in identifiers:
            print(ident)
        print(f"\nTotal: {len(identifiers)} unique identifiers", file=sys.stderr)

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


# ------------------------------------------------------------------
# Numeric codec helpers
# ------------------------------------------------------------------

def _encode_str(s: str) -> str:
    """Encode each character as 2-digit decimal (ord - 32)."""
    return ''.join(f'{ord(c) - 32:02d}' for c in s)


def _decode_str(s: str) -> str:
    """Decode a string produced by _encode_str."""
    if len(s) % 2 != 0:
        raise ValueError(f"Encoded string length must be even, got {len(s)}: {s!r}")
    return ''.join(chr(int(s[i:i+2]) + 32) for i in range(0, len(s), 2))


def cmd_encode_map(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"ERROR: map file not found: {args.map}", file=sys.stderr)
        return 1
    bmap = BijectionMap.load(args.map)
    encoded: dict = {}
    for original, transformed in bmap.forward_map.items():
        encoded[_encode_str(original)] = transformed
    out_path = args.output or args.map
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"forward": encoded}, fh, indent=2, ensure_ascii=False)
    print(f"Encoded {len(encoded)} identifiers → {out_path}")
    return 0


def cmd_decode_map(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"ERROR: map file not found: {args.map}", file=sys.stderr)
        return 1
    with open(args.map, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    decoded: dict = {}
    errors = 0
    for encoded_key, transformed in data["forward"].items():
        try:
            decoded[_decode_str(encoded_key)] = transformed
        except (ValueError, OverflowError) as exc:
            print(f"WARNING: cannot decode key {encoded_key!r}: {exc}", file=sys.stderr)
            decoded[encoded_key] = transformed
            errors += 1
    out_path = args.output or args.map
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"forward": decoded}, fh, indent=2, ensure_ascii=False)
    print(f"Decoded {len(decoded)} identifiers → {out_path}")
    if errors:
        print(f"WARNING: {errors} key(s) could not be decoded and were kept as-is.", file=sys.stderr)
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    """transform → encode-map → compact-map in one shot."""
    # 1. transform
    rc = cmd_transform(args)
    if rc != 0:
        return rc
    # 2. encode-map (in-place)
    enc_args = argparse.Namespace(map=args.map, output=args.map)
    rc = cmd_encode_map(enc_args)
    if rc != 0:
        return rc
    # 3. compact-map (in-place)
    cmp_args = argparse.Namespace(map=args.map, output=args.map)
    return cmd_compact_map(cmp_args)


def cmd_unpack(args: argparse.Namespace) -> int:
    """expand-map → decode-map → restore in one shot."""
    # 1. expand-map (in-place)
    xp_args = argparse.Namespace(map=args.map, output=args.map)
    rc = cmd_expand_map(xp_args)
    if rc != 0:
        return rc
    # 2. decode-map (in-place)
    dc_args = argparse.Namespace(map=args.map, output=args.map)
    rc = cmd_decode_map(dc_args)
    if rc != 0:
        return rc
    # 3. restore
    return cmd_restore(args)


def cmd_compact_map(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"ERROR: map file not found: {args.map}", file=sys.stderr)
        return 1
    with open(args.map, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Support both standard {"forward": {...}} and already-compacted {"k":[],"v":[]}
    if "forward" in data:
        fwd = data["forward"]
    elif "k" in data and "v" in data:
        fwd = dict(zip(data["k"], data["v"]))
    else:
        print("ERROR: unrecognised map format", file=sys.stderr)
        return 1
    keys = list(fwd.keys())
    vals = list(fwd.values())
    compact = json.dumps({"k": keys, "v": vals}, ensure_ascii=False, separators=(',', ':'))
    out_path = args.output or args.map
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(compact)
    original_size = os.path.getsize(args.map)
    compact_size = len(compact.encode("utf-8"))
    print(f"Compacted {len(keys)} entries → {out_path}  ({original_size} → {compact_size} bytes)")
    return 0


def cmd_expand_map(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"ERROR: map file not found: {args.map}", file=sys.stderr)
        return 1
    with open(args.map, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "k" not in data or "v" not in data:
        print("ERROR: not a compacted map (expected 'k' and 'v' arrays)", file=sys.stderr)
        return 1
    fwd = dict(zip(data["k"], data["v"]))
    out_path = args.output or args.map
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"forward": fwd}, fh, indent=2, ensure_ascii=False)
    print(f"Expanded {len(fwd)} entries → {out_path}")
    return 0


def cmd_show_map(args: argparse.Namespace) -> int:
    if not os.path.exists(args.map):
        print(f"Map file not found: {args.map}", file=sys.stderr)
        return 1
    with open(args.map, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "k" in data and "v" in data:
        fwd = dict(zip(data["k"], data["v"]))
    elif "forward" in data:
        fwd = data["forward"]
    else:
        print("ERROR: unrecognised map format", file=sys.stderr)
        return 1
    print(f"Bijection map ({len(fwd)} entries):")
    for original, transformed in sorted(fwd.items()):
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
        "list-identifiers": cmd_list_identifiers,
        "encode-map": cmd_encode_map,
        "decode-map": cmd_decode_map,
        "compact-map": cmd_compact_map,
        "expand-map": cmd_expand_map,
        "pack": cmd_pack,
        "unpack": cmd_unpack,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
