import os
from pathlib import Path

import pytest

from signal_lights.cli import main, scan
from signal_lights.classify import classify
from signal_lights.io import load
from signal_lights.search import Hit

FIX = Path(__file__).parent / "fixtures" / "bl_gbt_3C295_ku_cut.fil"
BIG = Path(__file__).parent.parent / "data" / "blc52_guppi_60070_45462_3C295_0007.rawspec.0002.h5"


def test_real_gbt_cut_reads():
    obs = load(str(FIX))
    assert obs.data.shape == (111, 256)
    assert obs.telescope == "GBT" and obs.source_name == "3C295"


def test_real_ku_band_carrier_is_lit_rfi(tmp_path):
    before = FIX.read_bytes()
    res = scan(str(FIX), emit_dark=str(tmp_path))
    assert res["status"] == "lit" and res["counts"]["dark"] == 0
    assert res["hits"][0]["known_source"] == "rfi"
    assert abs(res["hits"][0]["freq_mhz"] - 10700.0313) < 0.001
    assert res["passthrough"] is None and not os.listdir(tmp_path)
    assert FIX.read_bytes() == before


def test_cli_runs(capsys):
    assert main(["scan", str(FIX)]) == 0
    out = capsys.readouterr().out
    assert '"status": "lit"' in out and "Dark signals are never replaced" in out


def test_unknown_band_narrowband_is_dark():
    # Classifier unit test with a hand-built Hit object (not data): 4.5 GHz is outside our RFI list.
    obs = load(str(FIX))
    h = Hit(10, 10, 10, 4500.0, 50.0, 1, 0.3, 24.0, 1.0)
    assert classify(h, obs)["light"] == "dark"


@pytest.mark.skipif(not BIG.exists(), reason="run scripts/fetch_sample.py to download the 20 MB BL file")
def test_full_real_bl_file():
    res = scan(str(BIG))
    assert res["input_unchanged"] and res["counts"]["hits"] > 0
    assert all(h["known_source"] in {"rfi", "instrument"} for h in res["hits"] if h["light"] == "lit")


def test_broad_hi_line_is_natural_but_narrow_wow_like_is_not():
    # Classifier unit test with hand-built Hit objects (not data).
    obs = load(str(FIX))  # foff ~2.86 kHz
    broad = Hit(0, 77, 40, 1420.50, 88.0, 78, 0.0, 9.6, 1.0)
    narrow = Hit(0, 0, 0, 1420.4556, 30.0, 1, 0.0, 9.6, 1.0)
    assert classify(broad, obs)["known_source"] == "natural-hi"
    assert classify(narrow, obs)["light"] == "dark"
