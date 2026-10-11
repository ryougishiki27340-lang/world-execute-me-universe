"""Determinism check: two renders of the same frames must be byte-identical."""
from __future__ import annotations

import hashlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import film  # noqa: E402


def digest(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return hashlib.sha256(buf.getvalue()).hexdigest()


def main():
    times = [16.04, 30.5, 192.3]
    for t in times:
        a = digest(film.frame(t))
        b = digest(film.frame(t))
        print(f"t={t:7.3f}s  first={a[:16]}  second={b[:16]}  "
              f"{'IDENTICAL' if a == b else 'DIFFER'}")
    print("verify: done")


if __name__ == "__main__":
    main()
