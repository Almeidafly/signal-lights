"""scan-set tests. Multi-target fixtures are byte-for-byte copies of real files with only the
SIGPROC source_name header changed, so the same real carrier appears under two 'targets'."""
import shutil
from pathlib import Path

from signal_lights import cli
from signal_lights.cli import scan_set
from signal_lights.io import read_fil, write_fil
from signal_lights.search import Hit

FIX = Path(__file__).parent / "fixtures"
WOW = FIX / "wow_1977.json"
CUT = FIX / "bl_gbt_3C295_ku_cut.fil"


def _relabel(src, dst, name):
    o = read_fil(str(src))
    hdr = dict(o.meta)
    hdr["source_name"] = name
    write_fil(str(dst), o.data, hdr)


def _force_dark(monkeypatch):
    # Make every hit dark before cross-matching, to test the cross-target logic in isolation.
    monkeypatch.setattr(cli, "classify", lambda h, o: {"light": "dark", "known_source": None, "reason": "test"})


def test_repeat_across_targets_is_lit(tmp_path, monkeypatch):
    _force_dark(monkeypatch)
    a, b = tmp_path / "a.fil", tmp_path / "b.fil"
    _relabel(CUT, a, "TARGET_A")
    _relabel(CUT, b, "TARGET_B")
    before = a.read_bytes(), b.read_bytes()
    res = scan_set([str(a), str(b)])
    for obs in res["observations"]:
        h = obs["hits"][0]
        assert h["light"] == "lit" and h["known_source"] == "multi-target"
        assert len(h["also_in_targets"]) == 1
    assert res["counts"]["dark"] == 0
    assert (a.read_bytes(), b.read_bytes()) == before


def test_same_target_twice_is_not_rejected(tmp_path, monkeypatch):
    _force_dark(monkeypatch)
    a, b = tmp_path / "a.fil", tmp_path / "b.fil"
    shutil.copyfile(CUT, a)
    shutil.copyfile(CUT, b)
    res = scan_set([str(a), str(b)])
    assert res["counts"]["dark"] == 2  # same sky target: repetition proves nothing


def test_single_target_hit_stays_dark(tmp_path, monkeypatch):
    _force_dark(monkeypatch)
    other = tmp_path / "other.fil"
    _relabel(CUT, other, "TARGET_B")
    res = scan_set([str(WOW), str(other)])
    wow = res["observations"][0]["hits"][0]
    assert wow["light"] == "dark" and wow["also_in_targets"] == []


def test_wow_stays_dark_in_a_set():
    before = WOW.read_bytes()
    res = scan_set([str(WOW), str(CUT)])
    wow = res["observations"][0]
    assert wow["status"] == "dark" and wow["hits"][0]["light"] == "dark"
    assert WOW.read_bytes() == before and wow["input_unchanged"]


def test_cli_scan_set(capsys):
    assert cli.main(["scan-set", str(WOW), str(CUT)]) == 0
    assert "scan-set: 1 dark hits remain" in capsys.readouterr().out
