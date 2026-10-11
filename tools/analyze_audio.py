"""Measure the beat grid and audio features of input/song.mp3.

Decoding uses ffmpeg (PCM), analysis uses librosa on the raw samples -
soundfile is not required. Output: data/beats.json, data/audio_features.npy
(onset strength envelope, hop 512 @ 22050 Hz).

The beat grid is THE source of B(bar)/Bt(beat); the 129 BPM prior is only a
sanity reference and is never hard-coded into scenes.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

# librosa.core.audio imports soundfile at module import time; this tool
# decodes with ffmpeg instead, so give librosa a harmless stand-in module.
# (The sandbox has no libsndfile.dll; a real soundfile install is unnecessary
# for beat/onset analysis and is intentionally not used.)
import sys
import types

_sf_stub = types.ModuleType("soundfile")
_sf_stub.__version__ = "stand-in (decode via ffmpeg)"
sys.modules["soundfile"] = _sf_stub

ROOT = Path(__file__).resolve().parents[1]
SR = 22050


def ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    cand = Path("D:/aicode/.toolchain/ffmpeg.exe")
    if cand.exists():
        return str(cand)
    raise SystemExit("ffmpeg not found on PATH or in D:/aicode/.toolchain")


def decode_mp3(mp3: Path) -> np.ndarray:
    raw = subprocess.run(
        [ffmpeg(), "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main() -> None:
    import librosa
    mp3 = ROOT / "input" / "song.mp3"
    y = decode_mp3(mp3)
    print(f"decoded: {len(y) / SR:.3f} s @ {SR} Hz (mono float32)")
    tempo, beats = librosa.beat.beat_track(y=y, sr=SR, units="time")
    onset = librosa.onset.onset_strength(y=y, sr=SR, hop_length=512)
    beats = np.asarray(beats, dtype=float)
    out = {
        "sr": SR,
        "duration": round(float(len(y) / SR), 4),
        "tempo": round(float(np.atleast_1d(tempo)[0]), 3),
        "n_beats": int(len(beats)),
        "beat_first": round(float(beats[0]), 4),
        "beat_len": round(float(np.mean(np.diff(beats))), 4),
        "beats": [round(float(b), 4) for b in beats],
    }
    (ROOT / "data" / "beats.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    np.save(ROOT / "data" / "audio_features.npy", onset.astype(np.float32))
    print(f"tempo={out['tempo']} BPM, {out['n_beats']} beats, beat_len={out['beat_len']}s, "
          f"first={out['beat_first']}s -> data/beats.json + data/audio_features.npy")


if __name__ == "__main__":
    main()
