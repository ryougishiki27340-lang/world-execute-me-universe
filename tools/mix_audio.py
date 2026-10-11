"""Mix the chime (two tones, peak -10 dBFS) under the song at 207.873s.

Deterministic: the chime is synthesised with numpy (no assets); the song file
itself is never modified or redistributed. Output: out/audio_mix.wav (PCM).
"""
from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FF = "D:/aicode/.toolchain/ffmpeg.exe"
SR = 44100


def synth_chime(path: Path, dur: float = 211.886):
    n = int(SR * 0.7)
    t = np.arange(n) / SR
    env = np.exp(-t / 0.18)
    tone = (0.5 * np.sin(2 * np.pi * 659.25 * t) +
            0.5 * np.sin(2 * np.pi * 987.77 * t)) * env
    tone *= 0.316                                   # -10 dBFS peak
    stereo = np.stack([tone, tone], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((stereo * 32767).astype("<i2").tobytes())


def main():
    chime = ROOT / "out" / "chime.wav"
    synth_chime(chime)
    out = ROOT / "out" / "audio_mix.wav"
    cmd = [FF, "-y", "-i", str(ROOT / "input" / "song.mp3"), "-i", str(chime),
           "-filter_complex",
           "[1:a]adelay=207873|207873[ch];"
           "[0:a][ch]amix=inputs=2:duration=first:normalize=0[aout]",
           "-map", "[aout]", "-c:a", "pcm_s16le", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        print("错误：ffmpeg 混音失败：")
        print(r.stderr[-2000:])
        sys.exit(1)
    print(f"audio mix: {out} ({out.stat().st_size} bytes)" +
          (f", chime delay=207873ms" if True else ""))


if __name__ == "__main__":
    main()
