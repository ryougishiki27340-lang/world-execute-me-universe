"""Mean brightness per frame (the light ratchet's own meter)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FF = "D:/aicode/.toolchain/ffmpeg.exe"


def main():
    mp4 = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "film.mp4")
    probe = subprocess.run([FF, "-i", str(mp4)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stderr
    fps = float(next(p for p in probe.split(",") if " fps" in p).split()[0])
    raw = subprocess.run([FF, "-v", "error", "-i", str(mp4),
                          "-vf", "scale=96:54:flags=area,format=rgb24",
                          "-f", "rawvideo", "-"], capture_output=True,
                         check=True).stdout
    rgb = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 54, 96, 3).astype(np.float32) / 255
    luma = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).mean(axis=(1, 2))
    peak = int(np.argmax(luma))
    print(f"[luma] {mp4.name}: {len(luma)} frames @ {fps:g} fps; "
          f"brightest frame {peak} at {peak / fps:.3f}s (luma {luma[peak]:.3f})")


if __name__ == "__main__":
    main()
