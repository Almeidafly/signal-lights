"""Narrowband hit search (turboSETI-inspired, simplified: integrate, threshold, fit drift)."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from .io import Observation


@dataclass
class Hit:
    chan_start: int
    chan_stop: int  # inclusive
    peak_chan: int
    freq_mhz: float
    snr: float
    width_chans: int
    drift_hz_s: float | None
    drift_resolution_hz_s: float | None
    raw_peak_value: float  # exact value read from the file, untouched

    def to_dict(self):
        return asdict(self)


def _robust_snr(spec: np.ndarray, block: int) -> np.ndarray:
    snr = np.zeros_like(spec)
    for i in range(0, len(spec), block):
        seg = spec[i:i + block]
        med = np.median(seg)
        mad = np.median(np.abs(seg - med)) * 1.4826
        snr[i:i + block] = (seg - med) / (mad if mad > 0 else 1.0)
    return snr


def find_hits(obs: Observation, snr_threshold: float = 10.0, max_hits: int = 5000) -> list[Hit]:
    data = obs.data
    if obs.meta.get("already_snr_units"):
        # Big Ear: values are already SNR; one channel, time series = transit through beam.
        col = data[:, 0]
        peak = int(np.argmax(col))
        if col[peak] < snr_threshold:
            return []
        return [Hit(0, 0, 0, obs.fch1_mhz, float(col[peak]), 1, None, None, float(col[peak]))]

    spec = data.mean(axis=0)
    block = int(obs.meta.get("nfpc", 0) or min(1024, obs.nchan))
    snr = _robust_snr(spec, block)
    above = snr > snr_threshold
    hits: list[Hit] = []
    i = 0
    n = len(spec)
    ntime = data.shape[0]
    t_obs = ntime * obs.tsamp_s
    df_hz = abs(obs.foff_mhz) * 1e6
    while i < n:
        if not above[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and above[j + 1]:
            j += 1
        peak = i + int(np.argmax(snr[i:j + 1]))
        drift = res = None
        if ntime >= 4:
            lo, hi = max(0, peak - 8), min(n, peak + 9)
            track = lo + np.argmax(data[:, lo:hi], axis=1)
            t = np.arange(ntime) * obs.tsamp_s
            slope_chan_s = np.polyfit(t, track, 1)[0]
            drift = float(slope_chan_s * obs.foff_mhz * 1e6)
            res = float(df_hz / t_obs)
        hits.append(Hit(i, j, peak, float(obs.freq_mhz(peak)), float(snr[peak]), j - i + 1,
                        drift, res, float(spec[peak])))
        i = j + 1
    hits.sort(key=lambda h: -h.snr)
    return hits[:max_hits]
