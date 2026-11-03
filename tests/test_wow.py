import json
from pathlib import Path

from signal_lights.cli import scan
from signal_lights.io import read_bigear, sha256_file

WOW = Path(__file__).parent / "fixtures" / "wow_1977.json"


def test_wow_fixture_is_the_published_record():
    rec = json.loads(WOW.read_text())
    assert rec["channel_2_printout"] == "6EQUJ5"
    assert rec["frequency_mhz"] == 1420.4556
    assert rec["integration_s"] * len(rec["channel_2_printout"]) == rec["window_s"] == 72
    obs = read_bigear(str(WOW))
    assert obs.data[:, 0].tolist() == [6, 14, 26, 30, 19, 5]


def test_wow_is_dark_and_untouched(tmp_path):
    before = WOW.read_bytes()
    res = scan(str(WOW), emit_dark=str(tmp_path))
    assert res["status"] == "dark"
    assert res["counts"] == {"hits": 1, "lit": 0, "dark": 1}
    hit = res["hits"][0]
    assert hit["light"] == "dark" and hit["known_source"] is None
    assert hit["raw_peak_value"] == 30.0  # 'U'
    assert WOW.read_bytes() == before
    out = tmp_path / WOW.name
    assert out.read_bytes() == before  # byte-identical passthrough
    assert res["passthrough"]["sha256"] == sha256_file(WOW) == res["input_sha256"]


def test_wow_never_lit_at_any_threshold():
    for snr in (1, 5, 10, 25):
        assert scan(str(WOW), snr)["status"] == "dark"
