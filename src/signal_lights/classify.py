"""Lit = explained by a known source. Dark = unexplained, passed through untouched.

The classifier only ever *labels*. It never edits, replaces, subtracts, or synthesises data.
"""
from __future__ import annotations

from .io import Observation
from .search import Hit

# Known human transmitter bands (MHz). Sources: ITU-R allocations, GPS/GLONASS/Galileo ICDs,
# Iridium/Inmarsat public specs, FCC band plans. First match wins (specific bands first).
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
    (1675.0, 1710.0, "meteorological-satellite downlink (GOES/NOAA/Meteosat, ITU 1675-1710 MHz)"),
    # US allocations, 47 CFR 2.106 (FCC/NTIA Table of Frequency Allocations), NTIA Manual (Redbook) ch. 4:
    # 1300-1390 MHz is federal aeronautical radionavigation / radiolocation (ARSR-4 / FAA-DoD long-range
    # air-route surveillance radars). 1215-1300 MHz is already covered by the GNSS entries above. The band stops
    # at 1390 MHz, and 1400-1427 MHz (protected radio astronomy, footnote US246) is never listed.
    (1300.0, 1390.0, "L-band long-range air-route surveillance radar (ARSR), 47 CFR 2.106 / NTIA Redbook"),
    # AWS-1/AWS-3 mobile uplink, 47 CFR Part 27 (27.5(h), 27.5(j)).
    (1710.0, 1780.0, "AWS cellular uplink (47 CFR Part 27)"),
    # Broadband PCS, 47 CFR Part 24 (24.229): 1850-1915 MHz uplink (incl. H-block 1915-1920, Part 27),
    # 1920-1930 MHz unlicensed PCS (47 CFR Part 15 Subpart D, e.g. DECT 6.0 phones), 1930-1995 MHz downlink.
    (1850.0, 1920.0, "PCS cellular uplink (47 CFR Part 24 / Part 27 H-block)"),
    (1920.0, 1930.0, "unlicensed PCS, e.g. DECT 6.0 cordless phones (47 CFR Part 15 Subpart D)"),
    (1930.0, 1995.0, "PCS cellular downlink (47 CFR Part 24)"),
    (2110.0, 2200.0, "AWS/UMTS cellular downlink"),
    (2320.0, 2345.0, "SiriusXM satellite radio"),
    (3700.0, 4200.0, "C-band geostationary satellite downlink"),
    (960.0, 1215.0, "aeronautical radionavigation (DME/TACAN, ITU 960-1215 MHz)"),
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
    df_khz = abs(obs.foff_mhz) * 1e3
    if 1419.4 <= hit.freq_mhz <= 1421.4 and hit.width_chans * df_khz >= 50:
        return {"light": SIGNAL_LIT, "known_source": "natural-hi",
                "reason": f"broad ({hit.width_chans * df_khz:.0f} kHz) emission at the 1420.406 MHz neutral-hydrogen line: natural Galactic HI"}
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
