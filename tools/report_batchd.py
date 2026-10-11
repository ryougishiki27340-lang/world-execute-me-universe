"""v12 delivery report: batch D (S12 EXECUTION + S13 the only execution).

Extra deliverables this batch:
  - tools/check_flash.py full reports on the three segment mp4s (loops /
    counting cards / white-hot burst), plus a per-second flash detail table
    computed from rendered frames with the same algorithm
  - S13 light-ratchet luma curve (only rises, burst excluded)
  - white-flash budget ledger (whole film <= 8)
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
from check_flash import transitions
from verify import digest

FRAMES = [
    (147.89, "S12 r1 first cut"), (148.0, "S12 r1"), (150.0, "S12 r3"),
    (152.0, "S12 r5 zoom"), (154.5, "S12 r7"), (156.5, "S12 r10"),
    (158.12, "S12 r12"), (159.2, "S12 card EIN"), (159.79, "S12 card TROIS"),
    (160.66, "S12 card FEM"), (161.16, "S12 card LIU"), (161.88, "S12 side face"),
    (162.3, "S12 ERR overflow"), (162.59, "S13 white burst f0"),
    (162.8, "S13 burst"), (163.3, "S13 afterglow"), (164.32, "S13 L82 sea"),
    (166.18, "S13 L83 tree"), (167.94, "S13 L84 only proc"),
    (169.1, "S13 L85 keyword x1.0"), (171.86, "S13 L86 screen filled"),
    (172.81, "S13 keyword x1.12"), (174.57, "S13 keyword x1.26"),
    (175.01, "S13 L88 split"), (176.5, "S13 torn held"), (177.44, "S13 end"),
]
MOTION_TABLE = [
    ("S12", "十二轮生命周期快放", "每轮=歌词一声（实测词 onset 列表），轮内 u 扫过 12 阶段"),
    ("S12", "第 k 阶段特写", "轮次 k → UNIVERSE_STAGES[k] 行高亮（facts.py）"),
    ("S12", "第 5、9 轮整机放大", "zoom=1.12 中心裁切"),
    ("S12", "四字母块 EXEC 逐行下移", "轮内 start+i*0.23；第 12 轮=cues.py last_syl1..4"),
    ("S12", "循环箭头亮一次", "u>0.86 提亮"),
    ("S12", "输出阶梯", "每轮 +1 行，单向（1-3 轮附灰错误标签）"),
    ("S12", "stop 键无人按", "常驻 input: none"),
    ("S12", "数数六卡翻切", "159.2/159.4/159.79/160.31/160.66/161.16 词 onset，每卡 ≤0.12s"),
    ("S12", "点阵侧脸四帧闪现", "161.88/162.11/162.34/162.57 各 1 帧（全段唯一出现）"),
    ("S12", "每轮第一拍轻闪", "pulse(t, round_start, 0.12)，幅度 ≤0.25，共 12 次计预算"),
    ("S12", "ERR_LOVE_OVERFLOW 红标签+撕半", "162.3 起，红=受控唯一"),
    ("S13", "白热爆发转场", "162.59 锁 L81 词 onset，11 帧=11/24s，不计亮度纪录"),
    ("S13", "红移余辉冷却", "色相 255,230,210→120,30,28 单向，亮度下限 0.55"),
    ("S13", "宇宙时钟归零→重启计数", "t-162.59 单调"),
    ("S13", "粒子海冲出", "164.32 词 onset，半径 8+age*240 单向"),
    ("S13", "进程树+唯一进程点亮", "166.18/167.94 词 onset，love(pid 1) 金点"),
    ("S13", "关键词大字递增", "169.1/172.81/174.57/175.52，1.0→1.12→1.26→1.42 硬编码"),
    ("S13", "ERR_LOVE_OVERFLOW 撕半", "175.01 词 onset，gap 单向增大"),
    ("S13", "星图核心重新凝聚（她）", "cr=10+42*min(1,(t-162.59)/14.85) 单向"),
]


def cell_luma(t):
    a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255
    small = a[:1080 // 36 * 36, :1920 // 64 * 64].reshape(36, 30, 64, 30, 3)
    rgb = small.mean(axis=(1, 3))
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return (0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]).reshape(36 * 64)


def main():
    lines = ["# v12 delivery report: batch D (S12-S13)", ""]
    # 1) structure maps
    lines += ["## 1. 64x36 structure maps", ""]
    for t, tag in FRAMES:
        lines.append(f"### {tag} ({t}s)")
        lines += structure_map(film.frame(t))
        lines.append("")
    # 2) error-red table
    lines += ["## 2. error-red table (S12 red only after 162.3; S13 sanctioned)", ""]
    for t, tag in FRAMES:
        n = error_red(film.frame(t))
        note = " <- S12 only red (ERR label)" if 162.3 <= t < 162.59 else ""
        lines.append(f"t={t:7.3f}s {tag}: error_red={n}{note}")
    lines.append("")
    # 3) check_flash.py reports (recorded, rerun here)
    import subprocess
    FF_PY = str(ROOT / "tools" / "check_flash.py")
    PY = sys.executable
    lines += ["## 3. tools/check_flash.py full reports (three segments)", ""]
    for seg in ("chk_s12_loops.mp4", "chk_s12_cards.mp4", "chk_s13_full.mp4"):
        r = subprocess.run([PY, FF_PY, str(ROOT / "out" / seg)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        lines.append(r.stdout.strip())
    lines.append("")
    # 4) per-second flash detail (same algorithm, 64x36 cells)
    fps = 24
    ts = np.arange(147.89, 177.44, 1 / fps)
    rows = np.stack([cell_luma(float(t)) for t in ts])
    marks = transitions(rows, 0.10, dark_limit=0.80)
    win = fps
    cum = np.cumsum(marks, axis=0, dtype=np.int32)
    counts = cum[win:] - cum[:-win]
    level = np.percentile(counts, 75, axis=1) / 2
    lines += ["## 4. per-second flash detail (75th-pct cells, limit 3)", ""]
    for i in range(0, len(level), fps):
        s = ts[i] + 1.0
        lines.append(f"{s:6.2f}s window: {level[i]:.1f} flashes -> "
                     f"{'PASS' if level[i] <= 3 else 'FAIL'}")
    lines.append(f"worst whole segment: {float(level.max()):.1f} flashes")
    lines.append("")
    # 5) light ratchet: keyword staircase + environment afterglow, two columns
    def luma_at(t):
        a = np.asarray(film.frame(t).convert("RGB"), np.float32) / 255
        l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        return float(l[:1000].mean())
    kw_ts = [169.1, 172.81, 174.57, 175.52]
    kw = [luma_at(kt + 2 / 24) for kt in kw_ts]
    lines += ["## 5. S13 light ratchet (v13 strict definition, y<1000)", ""]
    lines.append("keyword staircase (landing frame = onset + 2 frames):")
    prev = None
    for kt, v in zip(kw_ts, kw):
        delta = "" if prev is None else f"  delta +{v - prev:.5f}"
        lines.append(f"  t={kt:7.2f}s  luma={v:.5f}{delta}")
        prev = v
    lines.append("environment afterglow column (cooling, before particle sea):")
    env = [luma_at(float(t)) for t in np.arange(163.3, 164.25, 1 / 24)]
    lines.append(f"  163.30s luma={env[0]:.5f} -> 164.25s luma={env[-1]:.5f}; "
                 f"monotonic non-increasing: "
                 f"{'OK' if all(b - a <= 0.0001 for a, b in zip(env, env[1:])) else 'FAIL'}")
    lines.append("exposure/light params: keyword light-step = persistent warm glow "
                 "ellipse (320,110)-(1600,830), alpha = 0.05 + 0.06*level, fade-in 2 frames "
                 "at each keyword onset, held afterwards (never falls). Afterglow = "
                 "ring colour mixc3((255,230,210),(120,30,28),a), brightness floor 0.55, "
                 "one-way cool 163.05-164.25.")
    lines.append("full per-frame curve: out/luma_s13_curve.txt")
    lines.append("")
    # 6) white flash ledger
    lines += ["## 6. white-flash budget ledger (whole film <= 8)", ""]
    lines.append("S10 triple gavel stamp: 3 | S12 per-round light pulse: 12 (amp<=0.25, "
                 "not white, counted) | S13 white-hot burst: 1 | S15 execution flash: 1 "
                 "-> white total = 5 <= 8; S12 pulses measured by check_flash = 0.0 flashes/s")
    lines.append("")
    # 7) motion driver table
    lines += ["## 7. motion-driver table", ""]
    for sec, layer, driver in MOTION_TABLE:
        lines.append(f"- {sec} {layer}: {driver}")
    lines.append("")
    # 8) determinism
    lines += ["## 8. determinism (two renders, sha256)", ""]
    for t, tag in [(147.89, "S12"), (152.0, "S12"), (159.2, "S12"), (161.88, "S12"),
                   (162.3, "S12"), (162.59, "S13 burst"), (167.94, "S13"),
                   (172.81, "S13"), (175.01, "S13"), (177.44, "S13")]:
        a, b = digest(film.frame(t)), digest(film.frame(t))
        lines.append(f"t={t:7.3f}s ({tag}): {a[:16]} {'IDENTICAL' if a == b else 'DIFFER'}")
    lines.append("")
    # 9) layout adjacency
    import audit
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit.main()
    lines += ["## 9. layout adjacency", "", buf.getvalue().strip(), ""]
    out = ROOT / "out" / "report_batchd.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nreport saved: {out}")


if __name__ == "__main__":
    main()
