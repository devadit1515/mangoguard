"""Download the public mango dry-matter dataset and verify its checksum.

The dataset is Anderson, Walsh and Subedi (2020), 'Mango DMC and NIR spectra',
Mendeley Data doi:10.17632/46htwnp833, released under CC BY 4.0. It is ~34 MB, so it
is fetched here rather than stored in the repository; the SHA-256 below pins the exact
copy every result was computed on.

Run:  python scripts/fetch_data.py
"""

from __future__ import annotations

import hashlib
import ssl
import sys
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "mango_dmc_nir.csv"
SHA256 = "20330fdd05d6c7c6d1ee948f765e7fb32a16b471f40ec04c3cba64ea418b25c5"
URL = (
    "https://raw.githubusercontent.com/dario-passos/DeepLearning_for_VIS-NIR_Spectra/"
    "master/notebooks/Deep-Tuttifrutti_I/data/NAnderson2020MendeleyMangoNIRData.csv"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    if DEST.exists() and sha256(DEST) == SHA256:
        print(f"already present and verified: {DEST}")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading dataset to {DEST} ...")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=120) as r:
        DEST.write_bytes(r.read())
    got = sha256(DEST)
    if got != SHA256:
        print(f"CHECKSUM MISMATCH\n expected {SHA256}\n got      {got}", file=sys.stderr)
        return 1
    print(f"downloaded and verified ({DEST.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
