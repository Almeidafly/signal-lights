# L-band results: four real Breakthrough Listen GBT files

Run with signal-lights at `build-v0`, using the default SNR threshold of 10. Every input sha256 was
the same before and after its scan. No data was altered. Reproduce with:

```bash
python scripts/fetch_sample.py --lband
signal-lights scan data/<file>.h5
```

## Files

All four files come from the GBT L-band receiver, observed on 2018-03-24 (MJD 58202). They are
Breakthrough Listen "spliced" gpuspec `.0002` products, covering **1023.93–1926.27 MHz** at
2.861 kHz per channel and 1.074 s per sample. Source: https://bldata.berkeley.edu/kepler-transits/
(Kepler-transit campaign, Franz et al. 2022).

| target | scan | samples (obs length) | size | sha256 |
|---|---|---|---|---|
| 3C295 (quasar calibrator) | 0006 | 111 (119 s) | 97,060,199 | `4450e0d0…dadf01` |
| KIC8462852 (Boyajian's star) | 0009 | 279 (300 s) | 243,554,126 | `f0fdb644…ce95` |
| Kepler-992b | 0010 | 279 (300 s) | 244,280,440 | `6d889e4d…4f21` |
| PSR B0329+54 | 0059 | 279 (300 s) | 243,423,189 | `b1c07c89…7e5b` |

The archive publishes no checksums. Sizes match the server's Content-Length, and the sha256 values
were computed on download. Full values are in `scripts/fetch_sample.py`.

## Counts

| target | hits | lit | dark | instrument (DC spike) | RFI band | natural HI |
|---|---|---|---|---|---|---|
| 3C295 | 510 | 495 | 15 | 289 | 206 | 0 |
| KIC8462852 | 472 | 463 | 9 | 294 | 168 | 1 |
| Kepler-992b | 531 | 526 | 5 | 302 | 223 | 1 |
| B0329+54 | 450 | 448 | 2 | 300 | 147 | 1 |

### Changes made while doing this run (classifier labels only, never data)
* The spliced gpuspec files have no `nfpc` attribute, so coarse-channel DC spikes were being reported
  dark. For GBT files, `nfpc` is now inferred from the 2.9296875 MHz coarse-channel width.
* Added the bands 960–1215 MHz (aeronautical DME/TACAN) and 1675–1710 MHz (meteorological-satellite downlink).
* Added a natural Galactic HI rule: emission at least 50 kHz wide within ±1 MHz of 1420.406 MHz is lit.
  A Wow!-like single 10 kHz channel stays dark, and a test enforces this.

## Dark hits (unexplained by our catalog; left untouched)

| target | freq (MHz) | SNR | width (kHz) | drift fit (Hz/s) | dark in N of 4 targets (±0.05 MHz) | classifier reason |
|---|---|---|---|---|---|---|
| 3C295 | 1641.211510 | 147.8 | 5.7 | -42 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1373.914719 | 64.5 | 28.6 | 42 (res 24.0) | 2 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1375.368118 | 61.4 | 2.9 | -1.9e+02 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1303.596497 | 57.1 | 22.9 | 56 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1373.745918 | 24.1 | 17.2 | 80 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1373.582840 | 20.2 | 2.9 | 66 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1907.798767 | 19.8 | 8.6 | -60 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1375.659943 | 18.3 | 2.9 | 1.4e+02 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1627.429962 | 14.2 | 5.7 | -1.3e+02 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1907.787323 | 12.7 | 2.9 | -77 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1375.617027 | 10.7 | 5.7 | 81 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1373.734474 | 10.7 | 2.9 | -56 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1913.426399 | 10.4 | 2.9 | -33 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1800.001144 | 10.4 | 2.9 | 9e-11 (res 24.0) | 4 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| 3C295 | 1380.077362 | 10.3 | 2.9 | -12 (res 24.0) | 1 | drift resolution 24.00 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1615.734100 | 70.6 | 20.0 | 32 (res 9.6) | 1 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1800.001144 | 48.2 | 5.7 | 2.2e-11 (res 9.6) | 4 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1909.987450 | 30.9 | 25.7 | 40 (res 9.6) | 1 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1646.615982 | 19.8 | 2.9 | -24 (res 9.6) | 1 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1393.452644 | 18.9 | 2.9 | -4.4e-10 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1921.540260 | 16.6 | 22.9 | -8.1 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1646.593094 | 13.2 | 2.9 | 1.6 (res 9.6) | 1 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1360.276222 | 13.1 | 2.9 | 0.57 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| KIC8462852 | 1373.903275 | 12.7 | 2.9 | -40 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| kepler992b | 1800.001144 | 53.5 | 5.7 | 2.2e-11 (res 9.6) | 4 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| kepler992b | 1360.276222 | 17.5 | 2.9 | -0.39 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| kepler992b | 1921.528816 | 17.5 | 20.0 | -3 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| kepler992b | 1426.629066 | 16.7 | 2.9 | 6.1e-11 (res 9.6) | 1 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; inside 1400-1427 MHz radio-astronomy band (transmissions prohibited); no known source matched |
| kepler992b | 1393.452644 | 14.2 | 2.9 | 5.7 (res 9.6) | 2 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| B0329+54 | 1800.001144 | 46.8 | 5.7 | 2.2e-11 (res 9.6) | 4 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |
| B0329+54 | 1924.996376 | 14.5 | 8.6 | 0.59 (res 9.6) | 1 | drift resolution 9.55 Hz/s too coarse to apply Earth-frame test; no known source matched |

### Reading these honestly
* **None of these is a technosignature candidate.** At 2.86 kHz resolution and 2–5 minute scans,
  the drift resolution is 9.6–24 Hz/s, so the Earth-frame test cannot run.
  These files also contain no ON/OFF cadence (each target was observed once).
* **1800.001 MHz is dark in all four targets**, which were in different sky positions and observed hours apart.
  That is the classic signature of local RFI. `scan-set` (below) now rejects hits like this.
  1360.28, 1393.45, 1921.5 and 1373.9 MHz each recur in two targets. The 1373–1375 and 1907–1925 MHz clusters fall
  near L-band radar and cellular/PCS allocations that are not yet in our band list.
* The tool keeps all of them dark, as designed. Labeling them would need a cited source or a cadence
  test, not a guess.
* The pulsar rule did not fire on B0329+54. Its broadband hits land inside the DME band first, and the
  pulsar's own signal needs folding, which the tool doesn't do.

## Multi-target rejection (`signal-lights scan-set`)

Command: `signal-lights scan-set data/spliced_*.h5`. The match tolerance is 3 fine channels (8.58 kHz).
A dark hit is relabeled lit (`multi-target`) if any hit lies within that tolerance in an observation of a *different*
sky target. Only labels change, and every input sha256 was the same before and after the scan.

**Dark hits: 31 → 23.** 8 were relabeled, including 1800.001 MHz, which appeared in all four targets, plus 1360.28 and 1393.45 MHz.

| target | hits | lit | dark |
|---|---|---|---|
| 3C295 | 510 | 496 | 14 |
| KIC8462852 | 472 | 466 | 6 |
| kepler992b | 531 | 529 | 2 |
| B0329+54 | 450 | 449 | 1 |

### Remaining dark hits

| target | freq (MHz) | SNR | width (kHz) | drift fit (Hz/s, resolution) | note |
|---|---|---|---|---|---|
| 3C295 | 1641.211510 | 147.8 | 5.7 | -42 (24.0) |  |
| 3C295 | 1373.914719 | 64.5 | 28.6 | 42 (24.0) |  |
| 3C295 | 1375.368118 | 61.4 | 2.9 | -1.9e+02 (24.0) |  |
| 3C295 | 1303.596497 | 57.1 | 22.9 | 56 (24.0) |  |
| 3C295 | 1373.745918 | 24.1 | 17.2 | 80 (24.0) |  |
| 3C295 | 1373.582840 | 20.2 | 2.9 | 66 (24.0) |  |
| 3C295 | 1907.798767 | 19.8 | 8.6 | -60 (24.0) |  |
| 3C295 | 1375.659943 | 18.3 | 2.9 | 1.4e+02 (24.0) |  |
| 3C295 | 1627.429962 | 14.2 | 5.7 | -1.3e+02 (24.0) |  |
| 3C295 | 1907.787323 | 12.7 | 2.9 | -77 (24.0) |  |
| 3C295 | 1375.617027 | 10.7 | 5.7 | 81 (24.0) |  |
| 3C295 | 1373.734474 | 10.7 | 2.9 | -56 (24.0) |  |
| 3C295 | 1913.426399 | 10.4 | 2.9 | -33 (24.0) |  |
| 3C295 | 1380.077362 | 10.3 | 2.9 | -12 (24.0) |  |
| KIC8462852 | 1615.734100 | 70.6 | 20.0 | 32 (9.6) |  |
| KIC8462852 | 1909.987450 | 30.9 | 25.7 | 40 (9.6) |  |
| KIC8462852 | 1646.615982 | 19.8 | 2.9 | -24 (9.6) |  |
| KIC8462852 | 1921.540260 | 16.6 | 22.9 | -8.1 (9.6) |  |
| KIC8462852 | 1646.593094 | 13.2 | 2.9 | 1.6 (9.6) |  |
| KIC8462852 | 1373.903275 | 12.7 | 2.9 | -40 (9.6) |  |
| kepler992b | 1921.528816 | 17.5 | 20.0 | -3 (9.6) |  |
| kepler992b | 1426.629066 | 16.7 | 2.9 | 6.1e-11 (9.6) | in 1400-1427 MHz protected band |
| B0329+54 | 1924.996376 | 14.5 | 8.6 | 0.59 (9.6) |  |

Near misses that stay dark under the 8.58 kHz tolerance: 1921.540 (KIC8462852) vs 1921.529 (Kepler-992b) are
11.4 kHz apart, and 1373.903 (KIC8462852) vs 1373.915 (3C295) are 11.4 kHz apart. These probably come from the same transmitters,
but the rule is deliberately strict. A wider `--tol-chans` would light them, at the cost of rejecting more real signals.
