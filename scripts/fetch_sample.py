#!/usr/bin/env python3
"""Download a real Breakthrough Listen GBT file (20 MB) and verify its checksum."""
import hashlib, os, sys, urllib.request

URL = ("https://bldata.berkeley.edu/pipeline/AGBT22B_999_44/blc52_blp12/"
       "blc52_guppi_60070_45462_3C295_0007.rawspec.0002.h5")
SHA256 = "c498d51fb01b6a8d96fede547535fb1f167f6a93cf783773f102c0998961278c"
DEST = os.path.join(os.path.dirname(__file__), "..", "data", os.path.basename(URL))


def main():
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    if not os.path.exists(DEST):
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, DEST)
    h = hashlib.sha256(open(DEST, "rb").read()).hexdigest()
    if h != SHA256:
        sys.exit(f"checksum mismatch: {h}")
    print(f"ok {DEST} sha256={h}")


if __name__ == "__main__":
    main()
