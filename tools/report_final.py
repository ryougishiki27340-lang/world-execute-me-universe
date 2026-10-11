"""v15 final verification package (v14 3.3): decode checks, whole-film flash
test, brightness finale (S14 = brightest non-flash frame), layer census,
subtitle alignment and regression. Writes out/final_report.txt."""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
FF = "D:/aicode/.toolchain/ffmpeg.exe"


def run(args):
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def decode_ok(path):
    r = run([FF, "-v", "error", "-i", str(path), "-f", "null", "-"])
    return r.returncode == 0


def main():
    lines = ["# final verification package (v15)", ""]
    files = ["film_master.mkv", "film_1080p_audio.mp4",
             "film_4k_audio.mp4", "film_4k_silent.mp4"]
    lines.append("## 1. decode checks (exit 0)")
    for f in files:
        p = ROOT / "out" / f
        ok = p.exists() and decode_ok(p)
        lines.append(f"{f}: {'OK' if ok else 'MISSING/FAIL'} ({p.stat().st_size if p.exists() else 0} bytes)")
    # 2. flash
    lines.append("")
    lines.append("## 2. tools/check_flash.py on the full 1080p film")
    r = run([sys.executable, str(ROOT / "tools" / "check_flash.py"),
             str(ROOT / "out" / "film_1080p_audio.mp4")])
    lines.append(r.stdout.strip() or r.stderr.strip())
    # 3. brightness finale on the encoded film
    lines.append("")
    lines.append("## 3. brightness finale (S14 = brightest non-flash frame)")
    probe = run([FF, "-i", str(ROOT / "out" / "film_1080p_audio.mp4")]).stderr
    fps = float(next(p for p in probe.split(",") if " fps" in p).split()[0])
    raw = subprocess.run([FF, "-v", "error", "-i", str(ROOT / "out" / "film_1080p_audio.mp4"),
                          "-vf", "scale=64:36:flags=area,format=rgb24",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    rgb = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 36, 64, 3).astype(np.float32) / 255
    # brightness record excludes the framework subtitle band (y>=1000),
    # same convention as the S13 light-ratchet curve
    rgb = rgb[:, :34, :, :]
    luma = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).mean(axis=(1, 2))
    mask = np.ones(len(luma), bool)
    for t0, t1 in ((162.59, 163.05), (209.83, 209.92)):
        mask[int(t0 * fps):int(t1 * fps)] = False
    peak = int(np.argmax(luma[mask]))
    lines.append(f"peak non-flash frame: {peak} @ {peak / fps:.3f}s (luma {luma[mask][peak]:.4f})")
    lines.append(f"S14 192.3s luma = {luma[int(192.3 * fps)]:.4f}; "
                 f"white-burst 162.59s = {luma[int(162.59 * fps)]:.4f} (transition, not counted)")
    lines.append("verdict: " + ("OK" if abs(peak / fps - 192.3) < 0.5 else "FAIL"))
    # 4. census + subtitle alignment
    lines.append("")
    lines.append("## 4. whole-film census + subtitle alignment")
    import audit
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit.check_whole_film()
    lines.append(buf.getvalue().strip())
    r = run([sys.executable, str(ROOT / "tools" / "subtitle_check.py")])
    lines.append(r.stdout.strip() or r.stderr.strip())
    # 5. determinism spot check
    lines.append("")
    lines.append("## 5. determinism spot check (tools/verify.py)")
    r = run([sys.executable, str(ROOT / "tools" / "verify.py")])
    lines.append(r.stdout.strip())
    out = ROOT / "out" / "final_report.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nreport saved: {out}")


if __name__ == "__main__":
    main()
