#!/usr/bin/env python3
"""Download real Breakthrough Listen GBT files and verify their sha256 checksums.

Default: the 20 MB Ku-band sample. `--lband` also fetches four GBT L-band files (~830 MB total)
from https://bldata.berkeley.edu/kepler-transits/ (see docs/results-lband.md). The archive does not
publish checksums; the values below were computed after download and the sizes match the
server's Content-Length.
"""
import hashlib, os, sys, urllib.request

URL = ("https://bldata.berkeley.edu/pipeline/AGBT22B_999_44/blc52_blp12/"
       "blc52_guppi_60070_45462_3C295_0007.rawspec.0002.h5")
SHA256 = "c498d51fb01b6a8d96fede547535fb1f167f6a93cf783773f102c0998961278c"
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
KB = "https://bldata.berkeley.edu/kepler-transits/spliced_blc1011121314151617_guppi_58202_"
LBAND = [
    (KB + "41100_3C295_0006.gpuspec.0002.h5", "4450e0d0306e2654f0c1c75b96357a5b74eb6113b6c1c2e5d6558ffe73dadf01"),
    (KB + "42383_KIC8462852_0009.gpuspec.0002.h5", "f0fdb644741f4f553e9b261eaf76ac9a14602808588fb73b49604478c6d5ce95"),
    (KB + "43003_kepler992b_0010.gpuspec.0002.h5", "6d889e4d477f0d2a4c12c4ba94364b2da9268ee124c87366a9a5f2e5ff314f21"),
    (KB + "60970_B0329%2B54_0059.gpuspec.0002.h5", "b1c07c897e90988f45da9f393107948f89b10361657b36357738cd769cdf7e5b"),
]


def fetch(url, sha):
    os.makedirs(DATA, exist_ok=True)
    dest = os.path.join(DATA, os.path.basename(url).replace("%2B", "+"))
    if not os.path.exists(dest):
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, dest)
    h = hashlib.sha256()
    with open(dest, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != sha:
        sys.exit(f"checksum mismatch for {dest}: {h.hexdigest()}")
    print(f"ok {dest} sha256={sha}")


def main():
    fetch(URL, SHA256)
    if "--lband" in sys.argv:
        for url, sha in LBAND:
            fetch(url, sha)


if __name__ == "__main__":
    main()
