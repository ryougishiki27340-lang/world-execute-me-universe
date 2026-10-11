"""Subtitle-to-audio alignment check (v14 3.1): cross-correlate each lyric
line onset with the audio's onset-energy peak inside a +-0.4s window and
report the offsets. Declared onsets come from data/lyric_timing.json
(AUTOMATIC_DRAFT - this tool is the listening-review aid)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FF = "D:/aicode/.toolchain/ffmpeg.exe"
SR = 22050


def load_mono(path: Path) -> np.ndarray:
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True,
                         check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main():
    audio = load_mono(ROOT / "input" / "song.mp3")
    hop = int(SR * 0.01)
    n = len(audio) // hop
    env = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    env = np.convolve(env, np.ones(8) / 8, mode="same")
    onset = np.diff(env, prepend=env[0])
    lines = json.loads((ROOT / "data" / "lyric_timing.json").read_text(encoding="utf-8"))["lines"]
    offsets, used = [], 0
    for line in lines:
        t0 = line["start"]
        if t0 < 0.2 or t0 > len(env) / 100 - 0.4:
            continue
        lo = int((t0 - 0.4) * 100)
        hi = int((t0 + 0.4) * 100)
        seg = onset[max(0, lo):min(len(onset), hi)]
        if seg.max() < 1e-4:
            continue
        peak = lo + int(np.argmax(seg))
        offsets.append((peak / 100) - t0)
        used += 1
    if not offsets:
        print("错误：未找到任何可对齐的歌词行。")
        sys.exit(1)
    arr = np.array(offsets)
    print(f"[subtitle] {used}/{len(lines)} lines correlated; "
          f"mean offset={arr.mean() * 1000:+.1f}ms, median={np.median(arr) * 1000:+.1f}ms, "
          f"p90|off|={np.percentile(np.abs(arr), 90) * 1000:.1f}ms, "
          f"range=[{arr.min() * 1000:+.0f}, {arr.max() * 1000:+.0f}]ms")
    print("[subtitle] within +-150ms: "
          f"{int((np.abs(arr) < 0.15).mean() * 100)}% -> "
          f"{'OK' if np.median(arr) * 1000 > -80 else 'CHECK (systematic lead)'}")


if __name__ == "__main__":
    main()
