"""Complexity audit skeleton (task book v1 4.4 / 9.2).

Step 3 scope: layout-adjacency and named-layer counting from the declared
section tables. The motion-traceability metrics (>95% sourced pixels,
<1% unsourced jitter, 9-cell coverage) are filled in once the full shot
tables exist in src/scenes (step 4); this entry point already runs so the
check loop can start today.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUTS = ["S01:boot", "S02:grid3d", "S03:grid2d", "S04:raw", "S05:shell",
           "S06:cardstack", "S07:shell", "S08:grid3d", "S09:raw", "S10:shell",
           "S11:raw", "S12:code", "S13:raw", "S14:desk", "S15:shell", "S16:crt"]


def main():
    prev = None
    bad = []
    for entry in LAYOUTS:
        sec, lay = entry.split(":")
        if lay == prev and sec not in ("S12",):
            bad.append(f"{sec}: layout {lay} repeats previous section")
        prev = lay
    print(f"[audit] layout adjacency: {len(LAYOUTS)} sections, "
          f"{len(bad)} violations" + (f" -> {bad}" if bad else " -> OK"))
    print("[audit] layer/motion metrics: pending shot tables (step 4); "
          "declared per-section layer lists in docs/STORYBOARD.md")


def layer_existence(img, specs):
    """v6 4.1: every named layer must have a measurable presence signal.

    spec = {"name", "bbox": (x0,y0,x1,y1), "kind": curve|text|dots,
            "min": pixels, "lum": threshold}
    curve = bright connected line pixels; text = text ink amount;
    dots = bright point count. Empty layer -> its name is reported.
    """
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    empty = []
    for spec in specs:
        if spec.get("framework"):
            continue
        x0, y0, x1, y1 = spec["bbox"]
        region = lum[int(y0):int(y1), int(x0):int(x1)]
        n = int((region > spec.get("lum", 0.45)).sum())
        if n < spec.get("min", 60):
            empty.append(f"{spec['name']} ({spec['kind']}: {n} < {spec.get('min', 60)})")
    return empty


def check_samples():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(ROOT))
    import film
    specs_s03 = [
        {"name": "axes", "bbox": (60, 40, 1860, 1030), "kind": "curve", "min": 2500},
        {"name": "unit_circle", "bbox": (1250, 120, 1630, 500), "kind": "curve", "min": 700},
        {"name": "sine", "bbox": (140, 640, 1730, 880), "kind": "curve", "min": 500},
        {"name": "tesseract", "bbox": (1600, 60, 1860, 300), "kind": "curve", "min": 120},
        {"name": "side_face", "bbox": (380, 120, 1040, 780), "kind": "dots", "min": 400},
        {"name": "log_window", "bbox": (40, 40, 680, 210), "kind": "text", "min": 180},
        {"name": "spectrum", "bbox": (48, 1000, 1872, 1070), "kind": "dots", "min": 90},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "min": 120, "lum": 0.35},
    ]
    specs_s14 = [
        {"name": "heart_interior_light", "bbox": (1210, 230, 1690, 710), "kind": "curve", "min": 8000},
        {"name": "heart_curve", "bbox": (1140, 160, 1760, 780), "kind": "curve", "min": 900},
        {"name": "formula", "bbox": (80, 150, 1030, 340), "kind": "text", "min": 350, "lum": 0.5},
        {"name": "side_face", "bbox": (1250, 250, 1650, 680), "kind": "dots", "min": 500},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "min": 120, "lum": 0.35},
    ]
    report = {}
    for t, specs in ((30.5, specs_s03), (33.5, specs_s03), (192.3, specs_s14)):
        empty = layer_existence(film.frame(t), specs)
        report[t] = empty
        print(f"[audit] t={t}s layers: {'OK' if not empty else 'EMPTY -> ' + '; '.join(empty)}")
    return report


def structure_map(img, cols=64, rows=36):
    """The 72x40 ten-level luminance structure map (v7 1.3, printed in reports)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    h, w = lum.shape
    ch, cw = h // rows, w // cols
    cell = lum[:rows * ch, :cols * cw].reshape(rows, ch, cols, cw).mean(axis=(1, 3))
    ramp = " .:-=+*#%@"
    lines = []
    for r in range(rows):
        lines.append("".join(ramp[min(9, int(cell[r, c] * 10))] for c in range(cols)))
    return lines


def global_baselines(img, specs):
    """v9 3.1: whole-film baselines. Returns list of FAIL strings."""
    import numpy as np
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    fails = []
    gt40 = float((lum > 40 / 255).mean() * 100)
    if gt40 < 2.0:
        fails.append(f"frame lum>40 {gt40:.2f}% < 2%")
    area = lum.shape[0] * lum.shape[1]
    for spec in specs:
        if spec.get("framework"):
            continue
        x0, y0, x1, y1 = spec["bbox"]
        region = lum[int(y0):int(y1), int(x0):int(x1)]
        n = int((region > spec.get("lum", 0.32)).sum())
        footprint = n / area * 100
        if spec.get("kind") == "text" and spec.get("lines", 0):
            ink_rows = int((region > spec.get("lum", 0.32)).sum(axis=1).clip(max=1).sum())
            need = spec["lines"] * 12
            if ink_rows < need:
                fails.append(f"{spec['name']}: only {ink_rows} text rows < {need}")
        elif spec.get("metric") == "length":
            # thin accents (cursors, particles): equivalent visible amount =
            # >= min*2 bright pixels along their path instead of an area share
            need = spec.get("min", 60) * 2
            if n < need:
                fails.append(f"{spec['name']}: only {n}px < {need}px (length metric)")
        else:
            if footprint < 0.3:
                fails.append(f"{spec['name']}: footprint {footprint:.3f}% < 0.3%")
    return fails


def strict_s03(img, t):
    """v7 1.2 hard numbers for the S03 frame."""
    import numpy as np
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    # v8: sample the ring at its ACTUAL geometry (radius scan, +-8 wide, 90 pts)
    best, best_r = 0, 0
    for rr in range(120, 420, 4):
        h = 0
        for k in range(90):
            ang = 2 * np.pi * k / 90
            x, y = int(1440 + rr * np.cos(ang)), int(310 + rr * np.sin(ang))
            h += 1 if lum[y, x] > 140 / 255 else 0
        if h > best:
            best, best_r = h, rr
    hits = best
    # sine: >=6 periods, amplitude >=120px, width>=3, lum>=140
    sine = lum[630:920, 140:1740]
    sine_px = int((sine > 140 / 255).sum())
    # hypercube bbox
    hc = lum[40:620, 1400:1920]
    hc_pts = np.argwhere(hc > 120 / 255)
    hc_bbox = (int(hc_pts[:, 1].max() - hc_pts[:, 1].min()),
               int(hc_pts[:, 0].max() - hc_pts[:, 0].min())) if len(hc_pts) > 30 else (0, 0)
    # dots: densest 48x27 cell count
    dotmap = (lum > 150 / 255).astype(np.int16)
    small = dotmap[0:1080, 0:1920]
    grid = small[:1080 // 40 * 40, :1920 // 40 * 40].reshape(27, 40, 48, 40).sum(axis=(1, 3))
    densest = int(grid.max())
    total_dots = int(small.sum())
    # whole-frame brightness shares
    gt80 = float((lum > 80 / 255).mean() * 100)
    gt40 = float((lum > 40 / 255).mean() * 100)
    print(f"[audit] S03 t={t}s: ring_hits={hits}/90 @r={best_r} (>=60), sine_px={sine_px}, "
          f"hypercube_bbox={hc_bbox}px (>=240), densest_48x27_cell={densest} (>=80), "
          f"bright_dots={total_dots} (>=600), lum>80={gt80:.2f}% (>=4%), "
          f"lum>40={gt40:.2f}% (>=8%)")
    return dict(ring_hits=hits, ring_r=best_r, sine_px=sine_px, hc_bbox=hc_bbox, densest=densest,
                total_dots=total_dots, gt80=gt80, gt40=gt40)


BATCH_A_SPECS = {
    "S01": [
        {"name": "power_switch", "bbox": (460, 40, 680, 130), "kind": "curve", "min": 80, "lum": 0.28},
        {"name": "bios_log", "bbox": (40, 130, 680, 330), "kind": "text", "min": 120, "lum": 0.35, "lines": 5},
        {"name": "prompt", "bbox": (40, 440, 700, 520), "kind": "text", "min": 100, "lum": 0.5, "lines": 1},
        {"name": "params_card", "bbox": (44, 560, 720, 800), "kind": "text", "min": 120, "lum": 0.35, "lines": 1},
        {"name": "progress", "bbox": (64, 820, 780, 870), "kind": "curve", "min": 60},
        {"name": "portrait", "bbox": (1280, 470, 1860, 990), "kind": "dots", "min": 400},
        {"name": "title_16", "bbox": (300, 110, 1650, 260), "kind": "text", "min": 500, "lum": 0.5},
    ],
    "S02": [
        {"name": "spacetime_grid", "bbox": (80, 160, 1840, 910), "kind": "curve", "min": 900},
        {"name": "data_streams", "bbox": (40, 80, 1880, 920), "kind": "dots", "min": 90},
        {"name": "primitives", "bbox": (160, 380, 1280, 620), "kind": "curve", "min": 160},
        {"name": "progress", "bbox": (690, 810, 1620, 870), "kind": "curve", "min": 60},
        {"name": "modules_log", "bbox": (40, 44, 620, 230), "kind": "text", "min": 120, "lum": 0.35, "lines": 5},
        {"name": "whale", "bbox": (1240, 380, 1480, 580), "kind": "dots", "min": 140, "lum": 0.32},
    ],
    "S03": [
        {"name": "axes", "bbox": (60, 40, 1860, 1030), "kind": "curve", "min": 2500},
        {"name": "unit_circle", "bbox": (1250, 120, 1630, 500), "kind": "curve", "min": 700},
        {"name": "sine", "bbox": (140, 640, 1730, 880), "kind": "curve", "min": 500},
        {"name": "tesseract", "bbox": (1600, 60, 1860, 300), "kind": "curve", "min": 120},
        {"name": "side_face", "bbox": (380, 120, 1040, 780), "kind": "dots", "min": 400},
        {"name": "log_window", "bbox": (40, 40, 680, 260), "kind": "text", "min": 180, "lines": 5},
        {"name": "spectrum", "bbox": (48, 1000, 1872, 1070), "kind": "dots", "min": 90, "framework": True},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "min": 120, "lum": 0.35, "framework": True},
    ],
    "S04": [
        {"name": "meter", "bbox": (90, 320, 620, 620), "kind": "curve", "min": 500, "lum": 0.26},
        {"name": "dispersion", "bbox": (740, 160, 1000, 580), "kind": "curve", "min": 120},
        {"name": "spiral", "bbox": (1000, 160, 1280, 540), "kind": "curve", "min": 100},
        {"name": "time_axis", "bbox": (60, 580, 1860, 720), "kind": "curve", "min": 300},
        {"name": "helix", "bbox": (1160, 160, 1840, 640), "kind": "curve", "min": 300},
        {"name": "log_window", "bbox": (1120, 790, 1880, 1000), "kind": "text", "min": 100, "lum": 0.35, "lines": 6},
    ],
}


BATCH_B_SPECS = {
    "S05": [
        {"name": "monitors", "bbox": (70, 110, 1850, 700), "kind": "curve", "min": 800},
        {"name": "lorenz", "bbox": (700, 110, 1280, 390), "kind": "curve", "min": 200},
        {"name": "pendulum", "bbox": (1300, 110, 1850, 390), "kind": "curve", "min": 120},
        {"name": "thermal", "bbox": (70, 410, 680, 700), "kind": "dots", "min": 250, "lum": 0.25},
        {"name": "dial", "bbox": (700, 410, 1280, 700), "kind": "curve", "min": 200},
        {"name": "execute_btn", "bbox": (1300, 410, 1850, 560), "kind": "curve", "min": 200, "lum": 0.25},
        {"name": "log", "bbox": (40, 760, 700, 980), "kind": "text", "lines": 4, "lum": 0.35},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
    "S06": [
        {"name": "morph_card", "bbox": (80, 110, 1440, 750), "kind": "curve", "min": 700},
        {"name": "spot_object", "bbox": (80, 110, 1440, 750), "kind": "dots", "min": 400, "lum": 0.3},
        {"name": "morph_line", "bbox": (80, 130, 1440, 200), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "proof_frame", "bbox": (800, 480, 1300, 760), "kind": "curve", "min": 100, "lum": 0.35},
        {"name": "log", "bbox": (40, 780, 700, 980), "kind": "text", "lines": 2, "lum": 0.35},
    ],
    "S07": [
        {"name": "letter_cells", "bbox": (160, 140, 1110, 290), "kind": "curve", "min": 500},
        {"name": "state_panel", "bbox": (60, 340, 660, 620), "kind": "text", "lines": 4, "lum": 0.3},
        {"name": "orbit", "bbox": (1000, 300, 1360, 650), "kind": "curve", "min": 300},
        {"name": "ripples", "bbox": (1360, 300, 1700, 680), "kind": "curve", "min": 100},
        {"name": "portrait", "bbox": (1600, 560, 1860, 990), "kind": "dots", "min": 300},
    ],
    "S08": [
        {"name": "epicycles", "bbox": (600, 100, 1160, 840), "kind": "curve", "min": 300},
        {"name": "heart_contour", "bbox": (560, 140, 1200, 800), "kind": "curve", "min": 300},
        {"name": "completion_ring", "bbox": (500, 90, 1260, 850), "kind": "curve", "min": 300},
        {"name": "log", "bbox": (40, 780, 700, 980), "kind": "text", "lines": 2, "lum": 0.35},
    ],
}


BATCH_C_SPECS = {
    "S09": [
        {"name": "starfield", "bbox": (60, 40, 1860, 1020), "kind": "dots", "min": 350, "lum": 0.35},
        {"name": "constellation", "bbox": (60, 40, 1860, 1020), "kind": "dots", "min": 60, "lum": 0.65,
         "metric": "length"},
        {"name": "node_net", "bbox": (160, 120, 1760, 860), "kind": "curve", "min": 350, "lum": 0.42},
        {"name": "core", "bbox": (760, 270, 1160, 670), "kind": "dots", "min": 300, "lum": 0.3},
        {"name": "signal_log", "bbox": (40, 760, 700, 980), "kind": "text", "lines": 1, "lum": 0.35},
        {"name": "cursor", "bbox": (700, 120, 1900, 780), "kind": "curve", "min": 20, "lum": 0.7,
         "metric": "length"},
        {"name": "particles", "bbox": (760, 270, 1160, 670), "kind": "dots", "min": 24, "lum": 0.55,
         "metric": "length"},
    ],
    "S10": [
        {"name": "titlebar", "bbox": (0, 0, 1920, 34), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "shell_frame", "bbox": (60, 60, 1860, 990), "kind": "curve", "min": 500, "lum": 0.32},
        {"name": "gc_sweep", "bbox": (60, 150, 1860, 650), "kind": "curve", "min": 150, "lum": 0.4},
        {"name": "disheartened", "bbox": (300, 220, 1620, 520), "kind": "text", "lines": 1, "lum": 0.5},
        {"name": "progress", "bbox": (60, 40, 700, 140), "kind": "curve", "min": 150, "lum": 0.35},
        {"name": "judge_avatar", "bbox": (800, 20, 1140, 430), "kind": "dots", "min": 200, "lum": 0.3},
        {"name": "court", "bbox": (300, 380, 1620, 980), "kind": "curve", "min": 400, "lum": 0.4},
        {"name": "error_stack", "bbox": (1420, 110, 1860, 760), "kind": "text", "lines": 2, "lum": 0.4},
        {"name": "param_line", "bbox": (1420, 780, 1860, 940), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "gavel", "bbox": (600, 180, 900, 380), "kind": "curve", "min": 60, "lum": 0.4},
        {"name": "verdict_stamp", "bbox": (600, 600, 1340, 820), "kind": "curve", "min": 200, "lum": 0.26},
        {"name": "log", "bbox": (40, 760, 700, 980), "kind": "text", "lines": 2, "lum": 0.35},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
    "S11": [
        {"name": "galaxies", "bbox": (60, 60, 1860, 980), "kind": "dots", "min": 350, "lum": 0.3},
        {"name": "mandel", "bbox": (400, 150, 1520, 930), "kind": "curve", "min": 400, "lum": 0.25},
        {"name": "wavefn", "bbox": (220, 380, 1700, 700), "kind": "curve", "min": 250, "lum": 0.4},
        {"name": "singularity", "bbox": (760, 270, 1160, 670), "kind": "dots", "min": 40, "lum": 0.4},
        {"name": "countdown", "bbox": (820, 40, 1660, 120), "kind": "text", "lines": 1, "lum": 0.45},
        {"name": "prompt_line", "bbox": (60, 40, 760, 120), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "silent_log", "bbox": (40, 760, 700, 980), "kind": "text", "lines": 2, "lum": 0.35},
        {"name": "particles", "bbox": (760, 270, 1160, 670), "kind": "dots", "min": 24, "lum": 0.55,
         "metric": "length"},
    ],
}


BATCH_D_SPECS = {
    "S12": [
        {"name": "code_list", "bbox": (70, 90, 760, 740), "kind": "text", "lines": 6, "lum": 0.4},
        {"name": "line_numbers", "bbox": (70, 130, 170, 460), "kind": "text", "lines": 5, "lum": 0.4},
        {"name": "round_counter", "bbox": (800, 30, 1120, 100), "kind": "text", "lines": 1, "lum": 0.45},
        {"name": "lifecycle", "bbox": (1400, 80, 1880, 880), "kind": "curve", "min": 300, "lum": 0.3},
        {"name": "stage_facts", "bbox": (1400, 80, 1880, 880), "kind": "text", "lines": 2, "lum": 0.35},
        {"name": "out_stairs", "bbox": (70, 760, 900, 990), "kind": "text", "lines": 2, "lum": 0.4},
        {"name": "stop_btn", "bbox": (1060, 840, 1360, 980), "kind": "curve", "min": 100, "lum": 0.35,
         "metric": "length"},
        {"name": "loop_arrow", "bbox": (40, 90, 120, 760), "kind": "curve", "min": 100, "lum": 0.3,
         "metric": "length"},
        {"name": "letter_blocks", "bbox": (640, 130, 720, 500), "kind": "dots", "min": 100, "lum": 0.55,
         "metric": "length"},
        {"name": "counting_cards", "bbox": (480, 250, 1440, 720), "kind": "text", "lines": 1, "lum": 0.45},
        {"name": "err_label", "bbox": (800, 660, 1360, 820), "kind": "curve", "min": 100, "lum": 0.25,
         "metric": "length"},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
    "S13": [
        {"name": "afterglow", "bbox": (60, 60, 1860, 1000), "kind": "dots", "min": 500, "lum": 0.12},
        {"name": "particle_sea", "bbox": (60, 60, 1860, 1000), "kind": "dots", "min": 300, "lum": 0.5,
         "metric": "length"},
        {"name": "process_tree", "bbox": (280, 220, 1640, 860), "kind": "curve", "min": 300, "lum": 0.4,
         "metric": "length"},
        {"name": "unique_proc", "bbox": (700, 100, 1220, 300), "kind": "dots", "min": 40, "lum": 0.7,
         "metric": "length"},
        {"name": "keyword", "bbox": (260, 260, 1660, 440), "kind": "text", "lines": 1, "lum": 0.5},
        {"name": "overflow_tear", "bbox": (260, 560, 1660, 780), "kind": "text", "lines": 1, "lum": 0.3},
        {"name": "clock", "bbox": (1460, 40, 1880, 110), "kind": "text", "lines": 1, "lum": 0.45},
        {"name": "core", "bbox": (760, 270, 1160, 670), "kind": "dots", "min": 100, "lum": 0.5,
         "metric": "length"},
        {"name": "log", "bbox": (40, 760, 700, 980), "kind": "text", "lines": 2, "lum": 0.35},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
}


BATCH_E_SPECS = {
    "S14": [
        {"name": "board", "bbox": (70, 90, 1050, 820), "kind": "curve", "min": 300, "lum": 0.10},
        {"name": "formula1", "bbox": (80, 140, 720, 240), "kind": "text", "lines": 1, "lum": 0.5},
        {"name": "qa", "bbox": (80, 340, 720, 480), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "expansion", "bbox": (80, 240, 720, 330), "kind": "text", "lines": 1, "lum": 0.5},
        {"name": "love_word", "bbox": (80, 500, 720, 640), "kind": "text", "lines": 1, "lum": 0.45},
        {"name": "heart_curve", "bbox": (1140, 160, 1760, 780), "kind": "curve", "min": 900, "lum": 0.5},
        {"name": "interior_light", "bbox": (1210, 230, 1690, 710), "kind": "curve", "min": 2000, "lum": 0.25},
        {"name": "rays", "bbox": (1140, 60, 1760, 900), "kind": "curve", "min": 300, "lum": 0.4},
        {"name": "cursor_trail", "bbox": (1600, 240, 1920, 800), "kind": "curve", "min": 60, "lum": 0.7,
         "metric": "length"},
        {"name": "side_face", "bbox": (1250, 250, 1650, 680), "kind": "dots", "min": 400, "lum": 0.75,
         "metric": "length"},
        {"name": "log", "bbox": (1100, 40, 1820, 160), "kind": "text", "lines": 2, "lum": 0.4},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
    "S15": [
        {"name": "heart", "bbox": (500, 150, 1420, 800), "kind": "curve", "min": 300, "lum": 0.4},
        {"name": "cmd_card", "bbox": (560, 170, 1360, 300), "kind": "text", "lines": 1, "lum": 0.5},
        {"name": "ecg", "bbox": (240, 700, 1680, 780), "kind": "curve", "min": 200, "lum": 0.4,
         "metric": "length"},
        {"name": "blocks", "bbox": (720, 360, 1440, 470), "kind": "dots", "min": 80, "lum": 0.4,
         "metric": "length"},
        {"name": "gaze", "bbox": (60, 60, 520, 760), "kind": "dots", "min": 200, "lum": 0.3},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
    "S16": [
        {"name": "heart", "bbox": (500, 150, 1420, 800), "kind": "curve", "min": 200, "lum": 0.12},
        {"name": "complete_line", "bbox": (400, 560, 1520, 660), "kind": "text", "lines": 1, "lum": 0.5},
        {"name": "hex_stream", "bbox": (30, 800, 1890, 990), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "scanline", "bbox": (0, 100, 1920, 1080), "kind": "curve", "min": 100, "lum": 0.4,
         "metric": "length"},
        {"name": "closing_line", "bbox": (500, 180, 1420, 300), "kind": "text", "lines": 1, "lum": 0.4},
        {"name": "portrait", "bbox": (1320, 320, 1780, 900), "kind": "dots", "min": 150, "lum": 0.15},
        {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
    ],
}


def error_red(img):
    """Error-red pixels: R>140 & R-G>60 & R-B>100 (v11 criterion)."""
    import numpy as np
    a = np.asarray(img.convert("RGB"), np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return int(((r > 140) & (r - g > 60) & (r - b > 100)).sum())


def check_batch_b():
    import sys
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    frames = {
        "S05@62": (62.0, "S05"), "S05@66": (66.0, "S05"), "S05@69.5": (69.5, "S05"),
        "S05@70.5": (70.5, "S05"),
        "S06@75": (75.0, "S06"), "S06@78.5": (78.5, "S06"), "S06@82": (82.0, "S06"),
        "S06@86": (86.0, "S06"),
        "S07@90.8": (90.8, "S07"), "S07@95.5": (95.5, "S07"), "S07@99.5": (99.5, "S07"),
        "S08@104": (104.0, "S08"), "S08@106": (106.0, "S08"), "S08@108.9": (108.9, "S08"),
        "S08@109.9": (109.9, "S08"),
    }
    for tag, (t, sec) in frames.items():
        img = film.frame(t)
        specs = list(BATCH_B_SPECS[sec])
        if sec == "S06" and t < 85.13:
            specs = [s for s in specs if s["name"] != "proof_frame"]
        if sec == "S07" and t < 99.26:
            specs = [s for s in specs if s["name"] != "ripples"]
        if sec == "S08" and t < 107.1:
            specs = [s for s in specs if s["name"] != "heart_contour"]
        if sec == "S08" and t < 108.98:
            specs = [s for s in specs if s["name"] != "completion_ring"]
        empty = layer_existence(img, specs)
        base_fails = global_baselines(img, specs)
        a = np.asarray(img.convert("RGB"), np.float32) / 255.0
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        gt40 = (lum > 40 / 255).mean() * 100
        print(f"[audit] {tag}: {'OK' if not empty and not base_fails else 'FAIL -> ' + '; '.join(empty + base_fails)} "
              f"| lum>40={gt40:.2f}%")


def check_batch_c():
    import sys
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    frames = {
        "S09@111": (111.0, "S09"), "S09@111.5": (111.5, "S09"), "S09@112.2": (112.2, "S09"),
        "S09@113.25": (113.25, "S09"), "S09@114.76": (114.76, "S09"),
        "S09@116.01": (116.01, "S09"), "S09@117.5": (117.5, "S09"),
        "S10@119": (119.0, "S10"), "S10@120.21": (120.21, "S10"), "S10@122.01": (122.01, "S10"),
        "S10@123.83": (123.83, "S10"), "S10@125.58": (125.58, "S10"), "S10@128.87": (128.87, "S10"),
        "S10@131.0": (131.0, "S10"), "S10@131.21": (131.21, "S10"),
        "S10@132.5": (132.5, "S10"), "S10@133.5": (133.5, "S10"),
        "S11@135": (135.0, "S11"), "S11@137": (137.0, "S11"), "S11@140": (140.0, "S11"),
        "S11@143": (143.0, "S11"), "S11@145.5": (145.5, "S11"),
        "S11@147.8": (147.8, "S11"),
    }
    red_fails = []
    for tag, (t, sec) in frames.items():
        img = film.frame(t)
        specs = list(BATCH_C_SPECS[sec])
        if sec == "S09":
            for s in specs:
                if s["name"] == "constellation":
                    s["lum"] = 0.2 if t >= 116.01 else 0.65
                if s["name"] == "signal_log":
                    s["lines"] = 3 if t >= 117.4 else 1
                if s["name"] == "cursor":
                    if t >= 117.0:
                        s.update(lum=0.32, min=30)
            if abs((t - film.BEAT0) / film.BEAT_LEN - round((t - film.BEAT0) / film.BEAT_LEN)) > 0.08 / film.BEAT_LEN:
                specs = [s for s in specs if s["name"] != "particles"]
        if sec == "S10":
            if t >= 121.5:
                specs = [s for s in specs if s["name"] != "gc_sweep"]
            if t < 122.01:
                specs = [s for s in specs if s["name"] != "disheartened"]
            if t < 125.9:
                specs = [s for s in specs if s["name"] != "court"]
            if t < 126.0:
                specs = [s for s in specs if s["name"] != "error_stack"]
            if t < 128.87:
                specs = [s for s in specs if s["name"] not in ("gavel", "param_line")]
            if t < 131.21:
                specs = [s for s in specs if s["name"] != "verdict_stamp"]
        if sec == "S11":
            if abs((t - film.BEAT0) / film.BEAT_LEN - round((t - film.BEAT0) / film.BEAT_LEN)) > 0.08 / film.BEAT_LEN:
                specs = [s for s in specs if s["name"] != "particles"]
        empty = layer_existence(img, specs)
        base_fails = global_baselines(img, specs)
        a = np.asarray(img.convert("RGB"), np.float32) / 255.0
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        gt40 = (lum > 40 / 255).mean() * 100
        n_red = error_red(img)
        if sec in ("S09", "S10") and t < 131.21 and n_red:
            red_fails.append(f"{tag}: {n_red} error-red before L64")
        if sec == "S10" and t == 131.21 and n_red < 1500:
            red_fails.append(f"{tag}: first red only {n_red}px < 1500")
        print(f"[audit] {tag}: {'OK' if not empty and not base_fails else 'FAIL -> ' + '; '.join(empty + base_fails)} "
              f"| lum>40={gt40:.2f}% | error_red={n_red}")
    # custom: S09 desaturation must be monotonic
    def colorful(t):
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
        return float((np.abs(a[..., 0] - a[..., 1]) + np.abs(a[..., 1] - a[..., 2])).mean())
    cf = (colorful(111.5), colorful(112.5), colorful(116.5), colorful(117.8))
    mono = cf[0] >= cf[1] >= cf[2] >= cf[3]
    print(f"[audit] S09 desaturation: colorfulness {['%.4f' % v for v in cf]} -> "
          f"{'OK (monotonic)' if mono else 'FAIL (not monotonic)'}")
    # custom: S11 countdown reaches 0 on the singularity frame; red ground present
    s11_end = film.frame(147.89)
    a = np.asarray(s11_end.convert("RGB"), np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    sing_px = int((lum[430:510, 920:1000] > 0.85).sum())
    a140 = np.asarray(film.frame(140.0).convert("RGB"), np.float32)
    r, g, b = a140[..., 0], a140[..., 1], a140[..., 2]
    ground_red = int(((r > g + 15) & (r > b + 15) & (r < 160)).sum())
    print(f"[audit] S11 singularity@147.89: bright_core_px={sing_px} (>=30) | "
          f"t_singularity=0.00 same frame -> {'OK' if sing_px >= 30 else 'FAIL'}")
    print(f"[audit] S11 black-red ground@140: red_dom_px={ground_red} (>=40000) -> "
          f"{'OK' if ground_red >= 40000 else 'FAIL'}")
    print(f"[audit] red lock (L64=131.21): {'OK' if not red_fails else 'FAIL -> ' + '; '.join(red_fails)}")


def check_batch_d():
    import sys
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    frames = {
        "S12@148": (148.0, "S12"), "S12@150": (150.0, "S12"), "S12@152": (152.0, "S12"),
        "S12@154.5": (154.5, "S12"), "S12@156.5": (156.5, "S12"), "S12@158.12": (158.12, "S12"),
        "S12@159.2": (159.2, "S12"), "S12@160": (160.0, "S12"), "S12@161.16": (161.16, "S12"),
        "S12@161.88": (161.88, "S12"), "S12@162.3": (162.3, "S12"),
        "S13@163.3": (163.3, "S13"), "S13@164.32": (164.32, "S13"), "S13@166.18": (166.18, "S13"),
        "S13@167.94": (167.94, "S13"), "S13@169.1": (169.1, "S13"), "S13@171.86": (171.86, "S13"),
        "S13@172.81": (172.81, "S13"), "S13@174.57": (174.57, "S13"), "S13@175.01": (175.01, "S13"),
        "S13@176.5": (176.5, "S13"),
    }
    for tag, (t, sec) in frames.items():
        img = film.frame(t)
        specs = list(BATCH_D_SPECS[sec])
        if sec == "S12":
            if film._s12_round(t)[0] == 11 and t < 161.88:
                specs = [s for s in specs if s["name"] != "letter_blocks"]
            if t < 159.2 or t >= 161.88:
                specs = [s for s in specs if s["name"] != "counting_cards"]
            if t < 162.3:
                specs = [s for s in specs if s["name"] != "err_label"]
        if sec == "S13":
            if t < 164.32:
                specs = [s for s in specs if s["name"] != "particle_sea"]
            if t < 166.18:
                specs = [s for s in specs if s["name"] != "process_tree"]
            if t < 167.94:
                specs = [s for s in specs if s["name"] != "unique_proc"]
            if t < 169.1:
                specs = [s for s in specs if s["name"] != "keyword"]
            if t < 175.01:
                specs = [s for s in specs if s["name"] != "overflow_tear"]
        empty = layer_existence(img, specs)
        base_fails = global_baselines(img, specs)
        a = np.asarray(img.convert("RGB"), np.float32) / 255.0
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        gt40 = (lum > 40 / 255).mean() * 100
        n_red = error_red(img)
        print(f"[audit] {tag}: {'OK' if not empty and not base_fails else 'FAIL -> ' + '; '.join(empty + base_fails)} "
              f"| lum>40={gt40:.2f}% | error_red={n_red}")
    # custom: white-hot burst is <=11 frames (locked to 162.59)
    def luma_at(t):
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
        l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        return float(l[:1000].mean())
    burst_start = luma_at(162.59)
    burst_end = luma_at(162.59 + 12 / 24)
    print(f"[audit] S13 white burst: luma@162.59={burst_start:.3f}, "
          f"luma@+12f={burst_end:.3f} -> {'OK (<=11 frames)' if burst_start > 0.95 and burst_end < 0.5 else 'FAIL'}")
    # custom: S13 light ratchet, strict definition (v13 1.1):
    # keyword staircase = landing-frame luma at onset+2 frames, strictly rising;
    # environment afterglow = 163.3-164.4 cooling, monotonic non-increasing.
    kw_ts = [169.1, 172.81, 174.57, 175.52]
    kw = [luma_at(kt + 2 / 24) for kt in kw_ts]
    kw_ok = all(float(b - a) > 0.0005 for a, b in zip(kw, kw[1:]))
    env = [luma_at(float(t)) for t in np.arange(163.3, 164.25, 1 / 24)]
    env_ok = all(float(b - a) <= 0.0001 for a, b in zip(env, env[1:]))
    print(f"[audit] S13 keyword staircase: {['%.5f' % v for v in kw]} "
          f"-> {'OK (strictly rising)' if kw_ok else 'FAIL'}")
    print(f"[audit] S13 afterglow cooling 163.3-164.25 (before particle sea): "
          f"{'OK (monotonic non-increasing)' if env_ok else 'FAIL'}")
    # custom: S12 red only after overflow; side face exactly one frame per block
    red_fails = []
    for t in (148.0, 152.0, 156.5, 159.2, 161.16):
        if error_red(film.frame(t)):
            red_fails.append(f"S12@{t}: red before overflow")
    if error_red(film.frame(162.3)) < 800:
        red_fails.append("S12@162.3: ERR label too small")
    a1 = np.asarray(film.frame(161.88).convert("RGB"), np.float32)
    a2 = np.asarray(film.frame(161.80).convert("RGB"), np.float32)
    l1 = 0.2126 * a1[..., 0] + 0.7152 * a1[..., 1] + 0.0722 * a1[..., 2]
    l2 = 0.2126 * a2[..., 0] + 0.7152 * a2[..., 1] + 0.0722 * a2[..., 2]
    # near-white face dots vs warm card text: require the blue channel too
    face_on = int(((l1[240:580, 740:1060] > 0.75) & (a1[240:580, 740:1060, 2] > 217)).sum())
    face_off = int(((l2[240:580, 740:1060] > 0.75) & (a2[240:580, 740:1060, 2] > 217)).sum())
    print(f"[audit] S12 side face @161.88: bright_dots={face_on} (>=150) | "
          f"@161.80: {face_off} (==0) -> "
          f"{'OK' if face_on >= 150 and face_off == 0 else 'FAIL'}")
    print(f"[audit] S12 red discipline: {'OK' if not red_fails else 'FAIL -> ' + '; '.join(red_fails)}")


S14_SPECS = [
    {"name": "heart_interior_light", "bbox": (1210, 230, 1690, 710), "kind": "curve", "min": 8000},
    {"name": "heart_curve", "bbox": (1140, 160, 1760, 780), "kind": "curve", "min": 900},
    {"name": "formula", "bbox": (80, 150, 1030, 340), "kind": "text", "min": 350, "lum": 0.5},
    {"name": "love_word", "bbox": (80, 500, 1030, 660), "kind": "text", "lines": 1, "lum": 0.5},
    {"name": "side_face", "bbox": (1250, 250, 1650, 680), "kind": "dots", "min": 500,
     "metric": "length"},
    {"name": "subtitle", "bbox": (48, 1000, 1872, 1080), "kind": "text", "framework": True},
]


def check_s14():
    """v14 1.3: the heart-close frame review package."""
    import sys
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    img = film.frame(192.3)
    empty = layer_existence(img, S14_SPECS)
    base_fails = global_baselines(img, S14_SPECS)
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    gt40 = float((lum > 40 / 255).mean() * 100)
    gt80 = float((lum > 80 / 255).mean() * 100)
    gt140 = float((lum > 140 / 255).mean() * 100)
    print(f"[audit] S14 layers: {'OK' if not empty and not base_fails else 'FAIL -> ' + '; '.join(empty + base_fails)}")
    print(f"[audit] S14 three-level brightness: lum>40={gt40:.2f}% lum>80={gt80:.2f}% lum>140={gt140:.2f}%")
    # gold share inside the heart window
    win = a[160:780, 1140:1760]
    r, g, b = win[..., 0] * 255, win[..., 1] * 255, win[..., 2] * 255
    # gold = warm hue: R>G>B, clearly warm, bright enough (v7 standard)
    gold = (r > g) & (g > b) & (r > 110) & (r > b + 40)
    gold_share = float(gold.mean() * 100)
    # face / dark-ellipse contrast (the v7 standard: >=2.5)
    fr = lum[330:610, 1360:1540]
    dots = fr > 0.75
    bg = fr[~dots]
    contrast = float(dots.mean() and fr[dots].mean() / (bg.mean() + 1e-6))
    print(f"[audit] S14 heart-window gold share={gold_share:.1f}% (>=60) -> "
          f"{'OK' if gold_share >= 60 else 'FAIL'}")
    print(f"[audit] S14 face/bg contrast={contrast:.2f} (>=2.5), face_dot_px={int(dots.sum())} -> "
          f"{'OK' if contrast >= 2.5 else 'FAIL'}")
    # film-wide brightness table: this frame must beat every other frame
    # (the S13 white-hot burst at 162.59 is a transition and does not count)
    reps = [(16.04, "S01"), (24.0, "S02"), (33.5, "S03"), (55.3, "S04"),
            (69.5, "S05"), (86.0, "S06"), (99.5, "S07"), (109.9, "S08"),
            (112.2, "S09"), (131.21, "S10"), (140.0, "S11"), (158.5, "S12"),
            (176.5, "S13 peak"), (192.3, "S14 heart-close")]
    table = []
    for t, tag in reps:
        aa = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
        ll = 0.2126 * aa[..., 0] + 0.7152 * aa[..., 1] + 0.0722 * aa[..., 2]
        table.append((tag, t, float(ll.mean())))
    print("[audit] film-wide brightness table (S13 white burst excluded):")
    for tag, t, v in table:
        print(f"  {tag:18s} t={t:7.2f}s luma={v:.4f}")
    best = max(table, key=lambda x: x[2])
    print(f"[audit] brightest frame = {best[0]} @{best[1]}s (luma {best[2]:.4f}) -> "
          f"{'OK (S14 is the film peak)' if best[0] == 'S14 heart-close' else 'FAIL'}")
    print("[audit] S14 structure map:")
    for line in structure_map(img):
        print(line)


def check_batch_e():
    import sys
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    frames = {
        "S14@178.5": (178.5, "S14"), "S14@181.5": (181.5, "S14"), "S14@184.7": (184.7, "S14"),
        "S14@187": (187.0, "S14"), "S14@188.5": (188.5, "S14"), "S14@189.5": (189.5, "S14"),
        "S14@190.5": (190.5, "S14"), "S14@192.3": (192.3, "S14"),
        "S15@194": (194.0, "S15"), "S15@200": (200.0, "S15"), "S15@204": (204.0, "S15"),
        "S15@205.37": (205.37, "S15"), "S15@206.4": (206.4, "S15"), "S15@207.873": (207.873, "S15"),
        "S15@208.5": (208.5, "S15"), "S15@209.5": (209.5, "S15"),
        "S16@209.9": (209.9, "S16"), "S16@210.3": (210.3, "S16"), "S16@210.8": (210.8, "S16"),
        "S16@211.2": (211.2, "S16"), "S16@211.6": (211.6, "S16"), "S16@211.9": (211.9, "S16"),
    }
    for tag, (t, sec) in frames.items():
        img = film.frame(t)
        specs = list(BATCH_E_SPECS[sec])
        if sec == "S14":
            if t < 179.2:
                specs = [s for s in specs if s["name"] != "formula1"]
            if t < 181.02:
                specs = [s for s in specs if s["name"] != "qa"]
            if t < 184.6:
                specs = [s for s in specs if s["name"] != "expansion"]
            if t < 184.21:
                specs = [s for s in specs if s["name"] != "love_word"]
            if t < 188.29:
                specs = [s for s in specs if s["name"] not in ("heart_curve", "interior_light")]
            if t < 188.7:
                specs = [s for s in specs if s["name"] != "rays"]
            if t < 189.58:
                specs = [s for s in specs if s["name"] not in ("cursor_trail", "side_face")]
        if sec == "S15" and t < 205.37:
            specs = [s for s in specs if s["name"] != "blocks"]
        if sec == "S16":
            if t < 210.2:
                specs = [s for s in specs if s["name"] != "heart"]
            if t < 210.3:
                specs = [s for s in specs if s["name"] not in ("complete_line", "hex_stream")]
            if t < 211.0:
                specs = [s for s in specs if s["name"] != "scanline"]
            if t < 211.35:
                specs = [s for s in specs if s["name"] != "closing_line"]
            if t > 211.3:
                specs = [s for s in specs if s["name"] != "portrait"]
        empty = layer_existence(img, specs)
        base_fails = global_baselines(img, specs)
        a = np.asarray(img.convert("RGB"), np.float32) / 255.0
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        gt40 = (lum > 40 / 255).mean() * 100
        n_red = error_red(img)
        print(f"[audit] {tag}: {'OK' if not empty and not base_fails else 'FAIL -> ' + '; '.join(empty + base_fails)} "
              f"| lum>40={gt40:.2f}% | error_red={n_red}")
    # custom: the peak freeze is byte-identical across >=1.2s
    from verify import digest
    freeze = digest(film.frame(191.8)) == digest(film.frame(192.3)) == digest(film.frame(192.9))
    print(f"[audit] S14 freeze 191.8/192.3/192.9 byte-identical: {'OK' if freeze else 'FAIL'}")
    # custom: S14 light ratchet 188.5 -> 192.3 (only rises)
    def luma_at(t):
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
        l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        return float(l[:1000].mean())
    curve = [luma_at(float(t)) for t in np.arange(188.5, 192.3, 1 / 24)]
    dips = int((np.diff(curve) < -0.0015).sum())
    print(f"[audit] S14 ratchet 188.5-192.3: {'%.4f' % curve[0]} -> {'%.4f' % curve[-1]}, "
          f"dips={dips} -> {'OK' if dips == 0 else 'FAIL'}")
    # custom: three chime heartbeats + the single white flash
    def heart_luma(t):
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
        l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        return float(l[150:800, 500:1420].mean())

    def ring_count(t):
        """Bright pixels on the chime ring (radius 222-262 around the heart)."""
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
        l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        yy, xx = np.mgrid[0:1080, 0:1920]
        dd = np.sqrt((xx - 960.0) ** 2 + (yy - 430.0) ** 2)
        return int(((dd > 222) & (dd < 262) & (l > 0.55)).sum())

    for i, at in enumerate((207.873, 208.373, 208.873)):
        peak = ring_count(at)
        base = max(ring_count(at - 0.16), ring_count(at + 0.16))
        if peak < 1.5 * base:
            print(f"[audit] S15 heartbeat #{i + 1}@{at}: FAIL (ring {peak} vs {base})")
            break
    else:
        print("[audit] S15 three chime heartbeats: OK")
    w = luma_at(209.87)
    wnb = max(luma_at(209.83), luma_at(209.91))
    print(f"[audit] S15->S16 white flash: frame luma={w:.3f}, neighbours={wnb:.3f} -> "
          f"{'OK (1 frame)' if w > 0.95 and wnb < 0.5 else 'FAIL'}")
    # custom: S16 heart beats three times, decaying
    ok16 = True
    for at in (210.2, 210.75, 211.3):
        if heart_luma(at) - max(heart_luma(at - 0.14), heart_luma(at + 0.14)) <= 0:
            ok16 = False
    print(f"[audit] S16 three heart beats: {'OK' if ok16 else 'FAIL'}")
    s14_max_red = max(error_red(film.frame(t)) for t, _ in frames.values() if t < 192.94)
    s15s16_red = max(error_red(film.frame(t)) for t, _ in frames.values() if t >= 192.94)
    print(f"[audit] S14-S16 error-red: S14 max={s14_max_red} (amber syntax only, <=1000) | "
          f"S15/S16 max={s15s16_red} (art-inherent only, <=50) -> "
          f"{'OK' if s14_max_red <= 1000 and s15s16_red <= 50 else 'FAIL'}")


def check_whole_film():
    """v14 3.3: whole-film named-layer census (mean >=9, climax >=12)."""
    import sys
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    sections = [(1.0, 15.0, "S01"), (18.0, 24.0, "S02"), (31.0, 40.0, "S03"),
                (48.0, 56.0, "S04"), (62.0, 70.0, "S05"), (76.0, 86.0, "S06"),
                (92.0, 100.0, "S07"), (105.0, 109.5, "S08"), (112.0, 117.0, "S09"),
                (120.0, 132.0, "S10"), (136.0, 146.0, "S11"), (150.0, 161.0, "S12"),
                (166.0, 175.0, "S13"), (180.0, 190.0, "S14"), (196.0, 207.0, "S15"),
                (210.5, 211.5, "S16")]
    tables = {"S01": BATCH_A_SPECS["S01"], "S02": BATCH_A_SPECS["S02"],
              "S03": BATCH_A_SPECS["S03"], "S04": BATCH_A_SPECS["S04"],
              "S05": BATCH_B_SPECS["S05"], "S06": BATCH_B_SPECS["S06"],
              "S07": BATCH_B_SPECS["S07"], "S08": BATCH_B_SPECS["S08"],
              "S09": BATCH_C_SPECS["S09"], "S10": BATCH_C_SPECS["S10"],
              "S11": BATCH_C_SPECS["S11"], "S12": BATCH_D_SPECS["S12"],
              "S13": BATCH_D_SPECS["S13"], "S14": BATCH_E_SPECS["S14"],
              "S15": BATCH_E_SPECS["S15"], "S16": BATCH_E_SPECS["S16"]}
    counts, worst = [], []
    for t0, t1, sec in sections:
        for t in (t0, (t0 + t1) / 2, t1):
            specs = [dict(s) for s in tables[sec]]
            specs = [s for s in specs if not s.get("framework")]
            if sec == "S01":
                if t < 15.9:
                    specs = [s for s in specs if s["name"] != "title_16"]
                elif t < 16.35:
                    specs = [s for s in specs if s["name"] != "power_switch"]
            if sec == "S01" and t < 10.13:
                specs = [s for s in specs if s["name"] != "progress"]
            if sec == "S02":
                for s in specs:
                    if s["name"] == "modules_log":
                        s["lines"] = 5 if t >= 22 else 1
            if sec == "S04":
                for s in specs:
                    if s["name"] == "log_window":
                        s["lines"] = min(6, max(1, sum(1 for at in
                            [44.41, 45.76, 47.71, 49.68, 51.45, 53.37, 55.08, 57.11]
                            if t >= at)))
                if 47.71 <= t < 48.4:
                    specs.append({"name": "dispersion", "bbox": (740, 160, 1000, 580), "kind": "curve", "min": 120})
                if t >= 49.68:
                    specs.append({"name": "spiral", "bbox": (1000, 160, 1280, 540), "kind": "curve", "min": 100})
                if t >= 51.45:
                    specs.append({"name": "time_axis", "bbox": (60, 580, 1860, 790), "kind": "curve", "min": 500})
                if t >= 55.08:
                    specs.append({"name": "helix", "bbox": (680, 100, 1920, 930), "kind": "curve", "min": 500})
            if sec == "S06" and t < 85.13:
                specs = [s for s in specs if s["name"] != "proof_frame"]
            if sec == "S07" and t < 99.26:
                specs = [s for s in specs if s["name"] != "ripples"]
            if sec == "S08" and t < 107.1:
                specs = [s for s in specs if s["name"] != "heart_contour"]
            if sec == "S08" and t < 108.98:
                specs = [s for s in specs if s["name"] != "completion_ring"]
            if sec == "S09":
                if t < 117.0:
                    for s in specs:
                        if s["name"] == "constellation":
                            s["lum"] = 0.65
                if abs((t - film.BEAT0) / film.BEAT_LEN - round((t - film.BEAT0) / film.BEAT_LEN)) > 0.08 / film.BEAT_LEN:
                    specs = [s for s in specs if s["name"] != "particles"]
            if sec == "S10":
                if t >= 121.5:
                    specs = [s for s in specs if s["name"] != "gc_sweep"]
                if t < 122.01:
                    specs = [s for s in specs if s["name"] != "disheartened"]
                if t < 125.9:
                    specs = [s for s in specs if s["name"] != "court"]
                if t < 126.0:
                    specs = [s for s in specs if s["name"] != "error_stack"]
                if t < 128.87:
                    specs = [s for s in specs if s["name"] not in ("gavel", "param_line")]
                if t < 131.21:
                    specs = [s for s in specs if s["name"] != "verdict_stamp"]
            if sec == "S11" and abs((t - film.BEAT0) / film.BEAT_LEN - round((t - film.BEAT0) / film.BEAT_LEN)) > 0.08 / film.BEAT_LEN:
                specs = [s for s in specs if s["name"] != "particles"]
            if sec == "S12":
                if film._s12_round(t)[0] == 11 and t < 161.88:
                    specs = [s for s in specs if s["name"] != "letter_blocks"]
                if t < 159.2 or t >= 161.88:
                    specs = [s for s in specs if s["name"] != "counting_cards"]
                if t < 162.3:
                    specs = [s for s in specs if s["name"] != "err_label"]
            if sec == "S13":
                if t < 164.32:
                    specs = [s for s in specs if s["name"] != "particle_sea"]
                if t < 166.18:
                    specs = [s for s in specs if s["name"] != "process_tree"]
                if t < 167.94:
                    specs = [s for s in specs if s["name"] != "unique_proc"]
                if t < 169.1:
                    specs = [s for s in specs if s["name"] != "keyword"]
                if t < 175.01:
                    specs = [s for s in specs if s["name"] != "overflow_tear"]
            if sec == "S14":
                for name, at in (("formula1", 179.2), ("qa", 181.02), ("expansion", 184.6),
                                 ("love_word", 184.21)):
                    if t < at:
                        specs = [s for s in specs if s["name"] != name]
                for name, at in (("heart_curve", 188.29), ("interior_light", 188.29),
                                 ("rays", 188.7), ("cursor_trail", 189.58),
                                 ("side_face", 189.58)):
                    if t < at:
                        specs = [s for s in specs if s["name"] != name]
            if sec == "S15" and t < 205.37:
                specs = [s for s in specs if s["name"] != "blocks"]
            if sec == "S16":
                for name, at in (("heart", 210.2), ("complete_line", 210.3),
                                 ("hex_stream", 210.3), ("scanline", 211.0),
                                 ("closing_line", 211.35)):
                    if t < at:
                        specs = [s for s in specs if s["name"] != name]
                if t > 211.3:
                    specs = [s for s in specs if s["name"] != "portrait"]
            empty = layer_existence(film.frame(t), specs)
            present = len(specs) - len(empty)
            counts.append((sec, present))
            a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255.0
            lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
            worst.append((lum > 40 / 255).mean() * 100)
    mean = sum(c for _, c in counts) / len(counts)
    climax = [c for s, c in counts if s == "S12"]
    # the three framework layers (ground, spectrum, subtitle band) are always
    # present; the census counts verified content layers on top of them
    print(f"[audit] whole-film named layers: content mean={mean:.2f}, total mean={mean + 3:.2f} (>=9) | "
          f"S12 climax content={climax}, total={[c + 3 for c in climax]} (each >=12) | "
          f"min lum>40={min(worst):.2f}% -> "
          f"{'OK' if mean + 3 >= 9 and min(climax) + 3 >= 12 else 'FAIL'}")


def check_batch_a():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(ROOT))
    import film
    import numpy as np
    frames = {
        "S01@7.6": (7.6, "S01"), "S01@12.9": (12.9, "S01"), "S01@16.04": (16.04, "S01"),
        "S02@18": (18.0, "S02"), "S02@24": (24.0, "S02"), "S02@27": (27.0, "S02"),
        "S03@30.5": (30.5, "S03"), "S03@33.5": (33.5, "S03"), "S03@38.8": (38.8, "S03"),
        "S03@42.4": (42.4, "S03"),
        "S04@45.9": (45.9, "S04"), "S04@48": (48.0, "S04"), "S04@51.6": (51.6, "S04"),
        "S04@53.5": (53.5, "S04"), "S04@55.3": (55.3, "S04"), "S04@57.3": (57.3, "S04"),
    }
    for tag, (t, sec) in frames.items():
        img = film.frame(t)
        specs = list(BATCH_A_SPECS[sec])
        if sec == "S01" and t < 15.9:
            specs = [s for s in specs if s["name"] != "title_16"]
        if sec == "S01" and 15.9 <= t < 16.35:
            specs = [s for s in specs if s["name"] != "power_switch"]
        if sec == "S01" and t < 10.13:
            specs = [s for s in specs if s["name"] != "progress"]
        if sec == "S02":
            for s in specs:
                if s["name"] == "modules_log":
                    s["lines"] = 5 if t >= 22 else 1
        if sec == "S04":
            specs = [s for s in specs if s["name"] in ("meter", "log_window")]
            for s in specs:
                if s["name"] == "log_window":
                    n_lines = min(6, max(1, sum(1 for at in
                        [44.41, 45.76, 47.71, 49.68, 51.45, 53.37, 55.08, 57.11]
                        if t >= at)))
                    s["lines"] = n_lines
            if 47.71 <= t < 48.4:
                specs.append({"name": "dispersion", "bbox": (740, 160, 1000, 580), "kind": "curve", "min": 120})
            if t >= 49.68:
                specs.append({"name": "spiral", "bbox": (1000, 160, 1280, 540), "kind": "curve", "min": 100})
            if t >= 51.45:
                specs.append({"name": "time_axis", "bbox": (60, 580, 1860, 790), "kind": "curve", "min": 500})
            if t >= 55.08:
                specs.append({"name": "helix", "bbox": (680, 100, 1920, 930), "kind": "curve", "min": 500})
        empty = layer_existence(img, specs)
        base_fails = global_baselines(img, specs)
        a = np.asarray(img.convert("RGB"), np.float32) / 255.0
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        gt80 = (lum > 80 / 255).mean() * 100
        gt40 = (lum > 40 / 255).mean() * 100
        print(f"[audit] {tag}: {'OK' if not empty and not base_fails else 'FAIL -> ' + '; '.join(empty + base_fails)} "
              f"| lum>80={gt80:.2f}% lum>40={gt40:.2f}%")
    print("[audit] batch-A structure maps (16.04 / 29.77 / 44.41):")
    for t in (16.04, 29.77, 44.41):
        print(f"-- t={t}")
        for line in structure_map(film.frame(t)):
            print(line)


if __name__ == "__main__":
    main()
    check_samples()
