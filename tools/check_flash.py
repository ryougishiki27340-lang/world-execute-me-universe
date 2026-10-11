"""Photosensitivity check (WCAG 2.3.1 approximation), adapted for this film.

Budget: within any one second, no more than 3 large-area luminance round trips.
Usage:  python tools/check_flash.py out/chk.mp4
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FF = "D:/aicode/.toolchain/ffmpeg.exe"
W, H, AREA = 64, 36, 0.25


def transitions(value, thresh, dark_limit=None):
    n = value.shape[0]
    ext = value[0].copy()
    direction = np.zeros(value.shape[1], dtype=np.int8)
    marks = np.zeros(value.shape, dtype=np.int16)
    for i in range(1, n):
        v = value[i]
        rise = (v - ext >= thresh) & (direction <= 0)
        fall = (ext - v >= thresh) & (direction >= 0)
        if dark_limit is not None:
            rise &= ext < dark_limit
            fall &= v < dark_limit
        marks[i] = rise | fall
        direction[rise], direction[fall] = 1, -1
        ext[rise], ext[fall] = v[rise], v[fall]
        ext = np.where(direction > 0, np.maximum(ext, v),
                       np.where(direction < 0, np.minimum(ext, v), ext))
    return marks


def flashes_per_second(marks, fps):
    win = int(round(fps))
    cum = np.cumsum(marks, axis=0, dtype=np.int32)
    counts = cum[win:] - cum[:-win]
    level = np.percentile(counts, 100 * (1 - AREA), axis=1)
    at = int(np.argmax(level))
    return float(level[at]) / 2, at


def main():
    mp4 = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "film.mp4")
    probe = subprocess.run([FF, "-i", str(mp4)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stderr
    fps = float(next(p for p in probe.split(",") if " fps" in p).split()[0])
    raw = subprocess.run([FF, "-v", "error", "-i", str(mp4),
                          "-vf", f"scale={W}:{H}:flags=area,format=rgb24",
                          "-f", "rawvideo", "-"], capture_output=True,
                         check=True).stdout
    rgb = np.frombuffer(raw, dtype=np.uint8).reshape(-1, W * H, 3).astype(np.float32) / 255
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    worst, at = flashes_per_second(transitions(lum, 0.10, dark_limit=0.80), fps)
    ok = worst <= 3
    print(f"[flash] {mp4.name}: {rgb.shape[0]} frames @ {fps:g} fps; "
          f"worst 1s window = {worst:.1f} flashes (from frame {at}) -> "
          f"{'PASS' if ok else 'FAIL'} (limit 3)")


if __name__ == "__main__":
    main()
