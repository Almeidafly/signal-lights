"""signal-lights CLI."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

from . import __version__
from .classify import classify
from .io import load, sha256_file
from .search import find_hits

RULE = ("Dark signals are never replaced, patched, smoothed, subtracted or fabricated. "
        "They are passed through byte-for-byte and flagged for human review.")


def scan(path: str, snr_threshold: float = 10.0, emit_dark: str | None = None) -> dict:
    before = sha256_file(path)
    obs = load(path)
    hits = find_hits(obs, snr_threshold)
    results = []
    for h in hits:
        c = classify(h, obs)
        results.append({**h.to_dict(), **c})
    dark = [r for r in results if r["light"] == "dark"]
    after = sha256_file(path)
    if before != after:  # pragma: no cover - would indicate a bug; refuse loudly
        raise RuntimeError("input file changed during scan")
    passthrough = None
    if dark and emit_dark:
        os.makedirs(emit_dark, exist_ok=True)
        dest = os.path.join(emit_dark, os.path.basename(path))
        shutil.copyfile(path, dest)
        copied = sha256_file(dest)
        if copied != before:  # pragma: no cover
            raise RuntimeError("passthrough copy is not byte-identical")
        passthrough = {"path": dest, "sha256": copied, "byte_identical": True}
    return {
        "tool": "signal-lights", "version": __version__, "file": path, "format": obs.fmt,
        "telescope": obs.telescope, "source_name": obs.source_name,
        "input_sha256": before, "input_unchanged": before == after,
        "band_mhz": sorted([obs.freq_mhz(0), obs.freq_mhz(obs.nchan - 1)]),
        "snr_threshold": snr_threshold,
        "counts": {"hits": len(results), "lit": len(results) - len(dark), "dark": len(dark)},
        "status": "dark" if dark else "lit",
        "rule": RULE, "passthrough": passthrough, "hits": results,
    }


def report(res: dict) -> str:
    c = res["counts"]
    lines = [f"signal-lights scan of {res['file']} ({res['telescope']}, target {res['source_name'] or 'unknown'})",
             f"Band {res['band_mhz'][0]:.4f}-{res['band_mhz'][1]:.4f} MHz. {c['hits']} hits above SNR {res['snr_threshold']}: "
             f"{c['lit']} lit (explained), {c['dark']} dark (unexplained)."]
    for r in [r for r in res["hits"] if r["light"] == "dark"][:20]:
        lines.append(f"  DARK  {r['freq_mhz']:.6f} MHz  SNR {r['snr']:.1f}  -> {r['reason']}. Left untouched; needs a human.")
    for r in [r for r in res["hits"] if r["light"] == "lit"][:5]:
        lines.append(f"  lit   {r['freq_mhz']:.6f} MHz  SNR {r['snr']:.1f}  -> {r['reason']}")
    lines.append(f"Input sha256 {res['input_sha256']} unchanged: {res['input_unchanged']}.")
    if res["passthrough"]:
        lines.append(f"Original data passed through byte-identical to {res['passthrough']['path']}.")
    lines.append(res["rule"])
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="signal-lights")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="scan a .h5/.fil filterbank or Big Ear .json record")
    s.add_argument("file")
    s.add_argument("--snr", type=float, default=10.0)
    s.add_argument("--emit-dark", metavar="DIR", help="copy the untouched original into DIR if anything is dark")
    s.add_argument("--json-only", action="store_true")
    a = ap.parse_args(argv)
    res = scan(a.file, a.snr, a.emit_dark)
    print(json.dumps(res, indent=2))
    if not a.json_only:
        print("\n" + report(res), file=sys.stderr if a.json_only else sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
