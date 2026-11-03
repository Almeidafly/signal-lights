# signal-lights

Watch real radio-telescope data. Known sources light up (**lit**): human satellites and
transmitters (RFI), Earth-locked interference, backend artifacts, known pulsars. Whatever is
left is **dark**: unexplained, passed through **byte-for-byte untouched**, and flagged for humans.

Inspired by [fitzyracing1/patch-cloud](https://github.com/fitzyracing1/patch-cloud), with one
deliberate inversion: patch-cloud fixes what went dark. signal-lights never does.
**No unknown signal is ever replaced, patched, smoothed, subtracted or fabricated. Not even the Wow! signal.**

## Install & use

```bash
pip install -e .[test]
signal-lights scan tests/fixtures/wow_1977.json           # Big Ear 1977 "6EQUJ5" -> dark
signal-lights scan tests/fixtures/bl_gbt_3C295_ku_cut.fil  # real GBT cut -> lit (Ku-band satellite)
signal-lights scan-set data/spliced_*.h5                   # reject hits repeated across different sky targets
python scripts/fetch_sample.py                             # 20 MB real Breakthrough Listen file, sha256-checked
signal-lights scan data/blc52_guppi_60070_45462_3C295_0007.rawspec.0002.h5 --emit-dark out/
```

Output is JSON followed by a plain-English report. `--emit-dark DIR` copies the original file,
unchanged and checksum-verified, whenever anything is dark.

## Data

* **Breakthrough Listen open data** (GBT, target 3C295, 2023-05-06, 10.69-10.88 GHz, 111 x 65536,
  ~2.86 kHz x 1.07 s): `https://bldata.berkeley.edu/pipeline/AGBT22B_999_44/blc52_blp12/blc52_guppi_60070_45462_3C295_0007.rawspec.0002.h5`
  sha256 `c498d51f...61278c`. Fetched by script, not committed.
* `tests/fixtures/bl_gbt_3C295_ku_cut.fil`: 256 real channels cut verbatim from that file (114 kB, SIGPROC).
* `tests/fixtures/wow_1977.json`: the published Big Ear record. Channel 2, `6EQUJ5`
  (6, 14, 26, 30, 19, 5 sigma), six 12 s integrations = 72 s, 1420.4556 MHz (Ehman's original note
  gives 1420.3556 MHz). Only the published column is encoded. Other channels are not invented.

## How it decides

1. Hit search (turboSETI-inspired, simplified): time-integrate, robust per-coarse-channel SNR,
   threshold (default 10), linear drift fit.
2. Lit if: coarse-channel DC spike; inside a known transmitter band (GNSS, Iridium, ADS-B,
   cellular, C/Ku satellite downlink...); zero drift when the drift resolution is fine enough;
   broadband on a known pulsar target.
3. Otherwise dark.

## Limitations

* Simplified search: this is not a full turboSETI de-Doppler tree, and it has no ON/OFF cadence filter. `scan-set` does reject hits repeated across different targets.
* The band list is coarse. A real ET signal inside a satellite band would be lit (false negative).
  The defaults lean toward labeling, not discarding: lit hits stay in the JSON too.
* At 2.86 kHz resolution the Earth-frame (zero-drift) test cannot run. The tool says so instead of guessing.
* The pulsar rule is a name match plus a width check, with no folding.

MIT licensed.
