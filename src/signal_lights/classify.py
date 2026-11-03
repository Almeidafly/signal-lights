"""Lit = explained by a known source. Dark = unexplained, passed through untouched.

The classifier only ever *labels*. It never edits, replaces, subtracts, or synthesises data.
"""
from __future__ import annotations

from .io import Observation
from .search import Hit

# Known human transmitter bands (MHz). Sources: ITU-R allocations, GPS/GLONASS/Galileo ICDs,
# Iridium/Inmarsat public specs, FCC band plans.
RFI_BANDS = [
    (1089.0, 1091.0, "ADS-B aircraft transponders (1090 MHz)"),
    (1164.0, 1189.0, "GNSS L5/E5a (GPS/Galileo satellites)"),
    (1192.0, 1215.0, "Galileo E5b / BeiDou B2 satellites"),
    (1217.0, 1238.0, "GPS L2 satellites"),
    (1240.0, 1260.0, "GLONASS L2 satellites"),
    (1268.0, 1300.0, "Galileo E6 / BeiDou B3 / L-band radar"),
    (1559.0, 1563.0, "BeiDou B1 satellites"),
    (1563.0, 1587.0, "GPS L1 / Galileo E1 satellites"),
    (1592.0, 1610.0, "GLONASS L1 satellites"),
    (1525.0, 1559.0, "Inmarsat / mobile-satellite downlink"),
    (1616.0, 1626.5, "Iridium satellites"),
    (1930.0, 1995.0, "PCS cellular downlink"),
    (2110.0, 2200.0, "AWS/UMTS cellular downlink"),
    (2320.0, 2345.0, "SiriusXM satellite radio"),
    (3700.0, 4200.0, "C-band geostationary satellite downlink"),
    (10700.0, 12750.0, "Ku-band geostationary / LEO (e.g. Starlink) satellite downlink"),
]

PROTECTED_BANDS = [(1400.0, 1427.0, "1400-1427 MHz radio-astronomy band (transmissions prohibited)")]

KNOWN_PULSARS = {"B0329+54", "PSR B0329+54", "B0531+21", "CRAB", "B0833-45", "VELA", "J0437-4715",
                 "B1933+16", "B0355+54", "B1133+16"}

SIGNAL_LIT, SIGNAL_DARK = "lit", "dark"


def _band(freq, bands):
    for lo, hi, name in bands:
        if lo <= freq <= hi:
            return name
    return None


def classify(hit: Hit, obs: Observation) -> dict:
    reasons = []
    nfpc = int(obs.meta.get("nfpc", 0) or 0)
    if nfpc and (hit.peak_chan % nfpc) == nfpc // 2 and hit.width_chans <= 2:
        return {"light": SIGNAL_LIT, "known_source": "instrument", "reason": "coarse-channel DC spike (BL backend artifact)"}
    band = _band(hit.freq_mhz, RFI_BANDS)
    if band:
        return {"light": SIGNAL_LIT, "known_source": "rfi", "reason": f"inside known human transmitter band: {band}"}
    if (obs.source_name or "").upper().replace("PSR ", "") in {p.upper().replace("PSR ", "") for p in KNOWN_PULSARS} \
            and hit.width_chans > 16:
        return {"light": SIGNAL_LIT, "known_source": "pulsar", "reason": f"broadband emission on known pulsar target {obs.source_name}"}
    if hit.drift_hz_s is not None and hit.drift_resolution_hz_s is not None \
            and abs(hit.drift_hz_s) < 0.5 * hit.drift_resolution_hz_s and hit.drift_resolution_hz_s < 1.0:
        return {"light": SIGNAL_LIT, "known_source": "earth", "reason": "zero drift: locked to Earth's frame (terrestrial interference)"}
    if hit.drift_resolution_hz_s is not None and hit.drift_resolution_hz_s >= 1.0:
        reasons.append(f"drift resolution {hit.drift_resolution_hz_s:.2f} Hz/s too coarse to apply Earth-frame test")
    prot = _band(hit.freq_mhz, PROTECTED_BANDS)
    if prot:
        reasons.append(f"inside {prot}")
    reasons.append("no known source matched")
    return {"light": SIGNAL_DARK, "known_source": None, "reason": "; ".join(reasons)}
