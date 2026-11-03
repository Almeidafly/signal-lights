"""Readers for real radio-telescope data. All readers open files read-only."""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Observation:
    path: str
    fmt: str
    data: np.ndarray  # shape (ntime, nchan), float
    fch1_mhz: float
    foff_mhz: float
    tsamp_s: float
    source_name: str = ""
    telescope: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def nchan(self) -> int:
        return self.data.shape[1]

    def freq_mhz(self, chan: float) -> float:
        return self.fch1_mhz + chan * self.foff_mhz


TELESCOPES = {0: "Fake", 1: "Arecibo", 4: "Parkes", 6: "GBT", 64: "MeerKAT", 65: "KAT-7"}


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _b(v):
    return v.decode() if isinstance(v, (bytes, np.bytes_)) else v


def read_h5(path: str) -> Observation:
    import h5py
    try:
        import hdf5plugin  # noqa: F401  (bitshuffle filter used by BL files)
    except ImportError:  # pragma: no cover
        pass
    with h5py.File(path, "r") as f:
        d = f["data"]
        a = {k: _b(d.attrs[k]) for k in d.attrs if k != "DIMENSION_LABELS"}
        arr = np.asarray(d[:, 0, :], dtype=np.float64)
    return Observation(path, "bl-h5", arr, float(a["fch1"]), float(a["foff"]), float(a["tsamp"]),
                       str(a.get("source_name", "")), TELESCOPES.get(int(a.get("telescope_id", -1)), "unknown"),
                       {k: (v.item() if hasattr(v, "item") else v) for k, v in a.items()})


def _read_fil_header(fh):
    def rstr():
        n = struct.unpack("<i", fh.read(4))[0]
        return fh.read(n).decode()
    if rstr() != "HEADER_START":
        raise ValueError("not a SIGPROC filterbank file")
    ints = {"telescope_id", "machine_id", "data_type", "nchans", "nbits", "nifs", "nbeams", "ibeam", "barycentric"}
    hdr = {}
    while True:
        key = rstr()
        if key == "HEADER_END":
            break
        if key in ("source_name", "rawdatafile"):
            hdr[key] = rstr()
        elif key in ints:
            hdr[key] = struct.unpack("<i", fh.read(4))[0]
        else:
            hdr[key] = struct.unpack("<d", fh.read(8))[0]
    return hdr, fh.tell()


def read_fil(path: str) -> Observation:
    with open(path, "rb") as fh:
        hdr, off = _read_fil_header(fh)
    dtype = {32: np.float32, 16: np.uint16, 8: np.uint8}[hdr["nbits"]]
    raw = np.fromfile(path, dtype=dtype, offset=off)
    nchan, nifs = hdr["nchans"], hdr.get("nifs", 1)
    arr = raw.reshape(-1, nifs, nchan)[:, 0, :].astype(np.float64)
    return Observation(path, "sigproc-fil", arr, hdr["fch1"], hdr["foff"], hdr["tsamp"],
                       hdr.get("source_name", ""), TELESCOPES.get(hdr.get("telescope_id", -1), "unknown"), hdr)


def write_fil(path: str, data: np.ndarray, hdr: dict) -> None:
    """Write float32 SIGPROC filterbank (used only to cut small fixtures from real data)."""
    def s(x):
        b = x.encode()
        return struct.pack("<i", len(b)) + b
    ints = {"telescope_id", "machine_id", "data_type", "nchans", "nbits", "nifs", "nbeams", "ibeam"}
    out = s("HEADER_START")
    for k, v in hdr.items():
        if isinstance(v, str):
            out += s(k) + s(v)
        elif k in ints:
            out += s(k) + struct.pack("<i", int(v))
        else:
            out += s(k) + struct.pack("<d", float(v))
    out += s("HEADER_END")
    with open(path, "wb") as fh:
        fh.write(out)
        fh.write(np.asarray(data, dtype=np.float32).tobytes())


# Big Ear printout alphabet: 0-9 then A-Z = 10..35 (signal-to-noise units).
BIGEAR_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def read_bigear(path: str) -> Observation:
    """Big Ear printout: one character per 12 s integration, already in SNR units.

    Only the published column (channel 2 of the 50-channel receiver) is encoded; other
    channels are not reproduced because we do not invent values we do not have.
    """
    with open(path, "r", encoding="utf-8") as fh:
        rec = json.load(fh)
    col = rec["channel_2_printout"]
    arr = np.array([[float(BIGEAR_ALPHABET.index(c))] for c in col], dtype=np.float64)
    return Observation(path, "bigear-json", arr, rec["frequency_mhz"], rec["channel_width_mhz"],
                       rec["integration_s"], rec.get("source_name", ""), "Big Ear",
                       {"already_snr_units": True, **{k: v for k, v in rec.items()}})


def load(path: str) -> Observation:
    p = str(path)
    if p.endswith(".h5"):
        return read_h5(p)
    if p.endswith(".fil"):
        return read_fil(p)
    if p.endswith(".json"):
        return read_bigear(p)
    raise ValueError(f"unsupported file type: {p}")
