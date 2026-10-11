"""v10 delivery report for batch B (S05-S08) + S04 helix recheck.

Runs without writing anything except out/report_batchb.txt:
  1. 64x36 structure maps for every review frame
  2. double-helix quantitative metrics at 55.3 / 57.3 s
  3. red-element scan (error-red only; S06 tomato spot color is reported
     separately and is sanctioned by STORYBOARD S06)
  4. two-render determinism digests
  5. layout adjacency (audit.main)
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np

import film
from audit import structure_map
from verify import digest

HELIX_FRAMES = {
    "S04@55.3": (55.3, (1160, 160, 1840, 640)),
    "S04@57.3": (57.3, (1160, 160, 1840, 640)),
}
BATCH_FRAMES = [
    (62.0, "S05"), (66.0, "S05"), (69.5, "S05"), (70.5, "S05"),
    (75.0, "S06"), (78.5, "S06"), (82.0, "S06"), (86.0, "S06"),
    (90.8, "S07"), (95.5, "S07"), (99.5, "S07"),
    (104.0, "S08"), (106.0, "S08"), (108.9, "S08"), (109.9, "S08"),
]
TOMATO_BBOX = (840, 110, 1520, 430)  # tomato morph card in S06 (spot color sanctioned)


def lum_array(img):
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2], a


def helix_metrics(img, x0, y0, x1, y1):
    """Two cyan/gold strands until L23; one merged bright line at 57.3."""
    lum, a = lum_array(img)
    band = lum[y0:y1, x0:x1]
    band_a = a[y0:y1, x0:x1]
    bright = (band > 0.45).astype(np.int16)
    band_px = int(bright.sum())
    two_track = 0
    for c in range(band.shape[1]):
        col = bright[:, c]
        runs = np.diff(np.concatenate(([0], col, [0])))
        starts = np.where(runs == 1)[0]
        ends = np.where(runs == -1)[0]
        if len([1 for s, e in zip(starts, ends) if e - s >= 3]) >= 2:
            two_track += 1
    merged = 0
    for r in range(band.shape[0]):
        col = bright[r, :]
        best = run = 0
        for v in col:
            run = run + 1 if v else 0
            best = max(best, run)
        merged = max(merged, best)
    # merged line is the diagonal (700,920)->(1900,120): measure continuity
    # along its own direction instead of row-wise runs
    diag_run = diag_best = 0
    for i in range(1201):
        x, y = int(700 + i), int(920 - i * 800 / 1200)
        local = lum[max(0, y - 1):y + 2, max(0, x - 1):x + 2]
        diag_run = diag_run + 1 if local.max() > 140 / 255 else 0
        diag_best = max(diag_best, diag_run)
    return band_px, two_track, diag_best


def red_scan(img):
    _, a = lum_array(img)
    r, g, b = a[..., 0] * 255, a[..., 1] * 255, a[..., 2] * 255
    red_dom = (r > 140) & (r - g > 60) & (r - b > 100)
    return int(red_dom.sum())


def main():
    lines = ["# v10 batch B delivery report", ""]
    # 1) structure maps
    lines += ["## 64x36 structure maps", ""]
    for tag, (t, bbox) in HELIX_FRAMES.items():
        img = film.frame(t)
        lines.append(f"### {tag} ({t}s)")
        lines += structure_map(img)
        lines.append("")
    for t, sec in BATCH_FRAMES:
        img = film.frame(t)
        lines.append(f"### {sec}@{t}s")
        lines += structure_map(img)
        lines.append("")
    # 2) helix metrics
    lines += ["## double helix (S04 recheck)", ""]
    for tag, (t, bbox) in HELIX_FRAMES.items():
        band_px, two_track, merged = helix_metrics(film.frame(t), *bbox)
        lines.append(f"{tag}: band_bright_px={band_px} (>=3000), two_track_cols={two_track} (>=12), "
                     f"merged_line_along_diag={merged}px (>=200 at 57.3s)")
    lines.append("")
    # 3) red scan
    lines += ["## red-element scan (error red = R>140 & R-G>60 & R-B>100)", ""]
    for t, sec in BATCH_FRAMES:
        n = red_scan(film.frame(t))
        note = ""
        if sec == "S06" and n:
            _, a = lum_array(film.frame(t))
            r, g, b = a[..., 0] * 255, a[..., 1] * 255, a[..., 2] * 255
            red = (r > 140) & (r - g > 60) & (r - b > 100)
            inside = int(red[TOMATO_BBOX[1]:TOMATO_BBOX[3],
                             TOMATO_BBOX[0]:TOMATO_BBOX[2]].sum())
            note = f" (all {n}px inside tomato spot-color card: {inside})" if inside == n else \
                   f" (tomato card {inside}/{n}, others outside: CHECK)"
        lines.append(f"{sec}@{t}s: red_px={n}{note}")
    lines.append("")
    # 4) determinism
    lines += ["## determinism (two renders, sha256)", ""]
    for t, sec in [(55.3, "S04"), (57.3, "S04"), (62.0, "S05"), (66.0, "S05"),
                   (69.5, "S05"), (70.5, "S05"), (78.5, "S06"), (86.0, "S06"),
                   (90.8, "S07"), (95.5, "S07"), (99.5, "S07"), (104.0, "S08"),
                   (106.0, "S08"), (108.9, "S08"), (109.9, "S08")]:
        a, b = digest(film.frame(t)), digest(film.frame(t))
        lines.append(f"t={t:7.3f}s ({sec}): {a[:16]} {'IDENTICAL' if a == b else 'DIFFER'}")
    lines.append("")
    # 5) layout adjacency
    import audit
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit.main()
    lines += ["## layout adjacency", "", buf.getvalue().strip(), ""]
    out = ROOT / "out" / "report_batchb.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nreport saved: {out}")


if __name__ == "__main__":
    main()
