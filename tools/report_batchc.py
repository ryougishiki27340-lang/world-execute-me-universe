"""v11 delivery report: S05 red-cluster recheck + batch C (S09-S11).

Sections:
  1. S05 error-red rescan (59.3/59.5/59.8/60.0 + every batch-B audit frame)
  2. 64x36 structure maps for batch C
  3. batch C error-red table (red locked to L64 = 131.21; S11 red ground is
     the sanctioned black-red palette)
  4. triple gavel-stamp flash budget (same algorithm as tools/check_flash.py)
  5. motion-driver table (every moving layer -> its driver)
  6. data-space portrait-reference check (S09/S11 must not touch char assets)
  7. two-render determinism
  8. layout adjacency
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
from audit import error_red, structure_map
from check_flash import transitions, flashes_per_second
from verify import digest

BATCH_B_RECHECK = [59.3, 59.5, 59.8, 60.0,
                   62.0, 66.0, 69.5, 70.5, 75.0, 78.5, 82.0, 86.0,
                   90.8, 95.5, 99.5, 104.0, 106.0, 108.9, 109.9]
BATCH_C_FRAMES = [
    (110.41, "S09 fade-in"), (111.0, "S09"), (111.5, "S09"), (112.2, "S09 L53"),
    (113.25, "S09 L54"), (114.76, "S09 L56"), (116.01, "S09 L57"),
    (117.5, "S09 grey"), (118.24, "S09->S10 winpop"), (119.0, "S10 L58"),
    (120.21, "S10 L59"), (122.01, "S10 L60"), (123.83, "S10 L61"),
    (125.58, "S10 L62"), (128.87, "S10 L63"), (131.0, "S10 pre-red"),
    (131.21, "S10 L64 FIRST RED"), (132.5, "S10 stamp x2"),
    (133.5, "S10 verdict held"), (133.95, "S10->S11 push"),
    (135.0, "S11"), (137.0, "S11"), (140.0, "S11"), (143.0, "S11"),
    (145.5, "S11"), (147.8, "S11"), (147.89, "S11 singularity"),
]
MOTION_TABLE = [
    ("S09", "恒星熄灭", "五句「离开」词 onset（112.2/113.25/113.93/114.76/116.01，瞬时硬切）"),
    ("S09", "链路崩断", "同上五词 onset（断点=每次离开）"),
    ("S09", "游标离场→淡出→残影", "段内线性 110.41→116.01；116.01 词 onset 起淡出 0.7s；残影=进程状态"),
    ("S09", "去饱和加灰", "单调 u=(t-110.41)/7.83 + 116.01 起 0.44 斜率（进程状态）"),
    ("S09", "核心信号闪烁", "116.01 起 prng(61,t)（frightened=信号不稳，确定性）"),
    ("S09", "粒子迸发", "实测拍点 ±0.08s"),
    ("S09", "ping/timeout/you have left", "词 onset 116.01/116.6/117.3（她发出）"),
    ("S10", "GC 橡皮擦扫过", "118.24→120.21 线性（L58→L59 词 onset 锁定完成）"),
    ("S10", "DISHEARTENED 下落", "122.01 起 0.8s 落下；125.0（disheartened 词 onset）提亮"),
    ("S10", "清理进度归零", "123.83 词 onset 归零（进程状态，0.3% 抖动=prng(82,t)）"),
    ("S10", "神庭展开", "125.58（Challenging your God 词 onset）0.6s smoothstep"),
    ("S10", "错误栈滚出（灰白/黑）", "125.58 起逐行 0.55s；131.21 末行转红（首红）"),
    ("S10", "参数行逐字键入", "128.87 词 onset，每字 35ms"),
    ("S10", "审判锤落下（灰）", "128.87 词 onset，0.5s 旋转"),
    ("S10", "红色判决盖下", "131.21（cues.py first_red=实测）0.15s 出现"),
    ("S10", "三连章白闪 ×3", "132.05/132.5/132.95，各 0.18s（全片白闪预算 4 次中的 3 次）"),
    ("S11", "星系内落", "每拍一级（floor((t-133.95)/beat_len) 步进，单向）"),
    ("S11", "曼德博放大", "zoom=1+4k 单向"),
    ("S11", "波函数塌缩", "sigma=500(1-k)+45 单向"),
    ("S11", "奇点能量积聚", "每拍一圈同心环累积（进程状态）"),
    ("S11", "t_singularity 倒计时", "147.89-t 单调递减，与奇点成形同帧归零"),
    ("S11", "粒子吸入", "实测拍点 ±0.08s"),
]


def main():
    lines = ["# v11 delivery report: S05 red recheck + batch C (S09-S11)", ""]
    # 1) S05 + batch B error-red rescan
    lines += ["## 1. error-red rescan (R>140 & R-G>60 & R-B>100)", ""]
    for t in BATCH_B_RECHECK:
        note = " (S06 tomato spot color, sanctioned)" if t in (78.5, 82.0, 86.0) else ""
        lines.append(f"t={t:7.3f}s: error_red={error_red(film.frame(t))}{note}")
    lines.append("")
    # 2) structure maps
    lines += ["## 2. 64x36 structure maps (batch C)", ""]
    for t, tag in BATCH_C_FRAMES:
        lines.append(f"### {tag} ({t}s)")
        lines += structure_map(film.frame(t))
        lines.append("")
    # 3) batch C red table
    lines += ["## 3. batch C error-red table (first red locked to 131.21)", ""]
    for t, tag in BATCH_C_FRAMES:
        n = error_red(film.frame(t))
        if t == 131.21:
            note = " <- FIRST RED"
        elif t < 131.21:
            note = ""
        elif t <= 133.95:
            note = " (verdict red held after L64, sanctioned)"
        else:
            note = " (S11 black-red palette, sanctioned)"
        lines.append(f"t={t:7.3f}s {tag}: error_red={n}{note}")
    lines.append("")
    # 4) gavel stamp flash budget
    fps = 24
    ts = np.arange(130.5, 134.6, 1 / fps)
    rows = []
    for t in ts:
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255
        small = a[:1080 // 36 * 36, :1920 // 64 * 64].reshape(36, 30, 64, 30, 3)
        rgb = small.mean(axis=(1, 3))
        lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
        rows.append(lum.reshape(36 * 64))
    lum = np.stack(rows)
    worst, at = flashes_per_second(transitions(lum, 0.10, dark_limit=0.80), fps)
    lines += ["## 4. triple gavel stamp flash budget (same algo as check_flash.py)", ""]
    lines.append(f"window 130.5-134.6s @ {fps}fps: worst 1s window = {worst:.1f} flashes "
                 f"(from frame {at}) -> {'PASS' if worst <= 3 else 'FAIL'} (limit 3)")
    lines.append("stamps are localized r<=52px (not full-frame); whole-film white "
                 "flash budget: 3 (S10) + 1 (S15) = 4 <= 8")
    lines.append("")
    # 5) motion driver table
    lines += ["## 5. motion-driver table (every moving layer -> driver)", ""]
    for sec, layer, driver in MOTION_TABLE:
        lines.append(f"- {sec} {layer}: {driver}")
    lines.append("")
    # 6) data-space portrait check
    src = (ROOT / "film.py").read_text(encoding="utf-8")
    import re
    s09 = src[src.index("def render_s09"):src.index("def render_s10")]
    s11 = src[src.index("def render_s11"):src.index("def _mandel_mask")]
    bodies = {"render_s09": s09, "render_s11": s11}
    hits = [fn for fn, body in bodies.items()
            if re.search(r"char_mod\.|portrait_window|whale-", body)]
    lines += ["## 6. data-space portrait-reference check (S09/S11)", ""]
    lines.append(f"render_s09 refs char assets: {'NO' if 'render_s09' not in hits else 'YES'}")
    lines.append(f"render_s11 refs char assets: {'NO' if 'render_s11' not in hits else 'YES'}")
    lines.append("")
    # 7) determinism
    lines += ["## 7. determinism (two renders, sha256)", ""]
    for t, tag in [(110.41, "S09"), (112.2, "S09"), (117.5, "S09"), (120.21, "S10"),
                   (125.58, "S10"), (131.21, "S10"), (132.5, "S10"), (135.0, "S11"),
                   (140.0, "S11"), (147.89, "S11")]:
        a, b = digest(film.frame(t)), digest(film.frame(t))
        lines.append(f"t={t:7.3f}s ({tag}): {a[:16]} {'IDENTICAL' if a == b else 'DIFFER'}")
    lines.append("")
    # 8) layout adjacency
    import audit
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit.main()
    lines += ["## 8. layout adjacency", "", buf.getvalue().strip(), ""]
    out = ROOT / "out" / "report_batchc.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nreport saved: {out}")


if __name__ == "__main__":
    main()
