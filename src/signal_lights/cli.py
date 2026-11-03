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
        "snr_threshold": snr_threshold, "foff_mhz": obs.foff_mhz,
        "counts": {"hits": len(results), "lit": len(results) - len(dark), "dark": len(dark)},
        "status": "dark" if dark else "lit",
        "rule": RULE, "passthrough": passthrough, "hits": results,
    }


def scan_set(paths: list[str], snr_threshold: float = 10.0, tol_chans: float = 3.0) -> dict:
    """Scan several observations; a dark hit that also appears (any light) in an observation of a
    *different* sky target is relabeled lit as local interference. Labels only; data untouched."""
    results = [scan(p, snr_threshold) for p in paths]
    foffs = [abs(r["foff_mhz"]) for r in results if r.get("foff_mhz")]
    tol = tol_chans * (max(foffs) if foffs else 0.0)
    for i, r in enumerate(results):
        for h in r["hits"]:
            if h["light"] != "dark":
                continue
            others = sorted({o["source_name"] for j, o in enumerate(results)
                             if j != i and o["source_name"] != r["source_name"]
                             and any(abs(oh["freq_mhz"] - h["freq_mhz"]) <= tol for oh in o["hits"])})
            h["also_in_targets"] = others
            if others:
                h["light"], h["known_source"] = "lit", "multi-target"
                h["reason"] = (f"seen in multiple targets ({r['source_name']}, {', '.join(others)}) "
                               f"within {tol * 1e3:.2f} kHz -> local interference")
        dark = sum(h["light"] == "dark" for h in r["hits"])
        r["counts"] = {"hits": len(r["hits"]), "lit": len(r["hits"]) - dark, "dark": dark}
        r["status"] = "dark" if dark else "lit"
    total_dark = sum(r["counts"]["dark"] for r in results)
    return {"tool": "signal-lights", "mode": "scan-set", "tolerance_mhz": tol,
            "targets": [r["source_name"] for r in results],
            "counts": {"hits": sum(r["counts"]["hits"] for r in results), "dark": total_dark},
            "status": "dark" if total_dark else "lit", "rule": RULE, "observations": results}


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
    m = sub.add_parser("scan-set", help="scan several observations; reject hits repeated across different targets")
    m.add_argument("files", nargs="+")
    m.add_argument("--snr", type=float, default=10.0)
    m.add_argument("--tol-chans", type=float, default=3.0, help="match tolerance in fine channels (default 3)")
    m.add_argument("--json-only", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "scan-set":
        res = scan_set(a.files, a.snr, a.tol_chans)
        print(json.dumps(res, indent=2))
        if not a.json_only:
            print()
            for r in res["observations"]:
                print(report(r) + "\n")
            print(f"scan-set: {res['counts']['dark']} dark hits remain across {len(res['targets'])} observations.")
        return 0
    res = scan(a.file, a.snr, a.emit_dark)
    print(json.dumps(res, indent=2))
    if not a.json_only:
        print("\n" + report(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
