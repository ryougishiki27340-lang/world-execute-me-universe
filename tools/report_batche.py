"""v15 delivery report: batch E (S14-S16) + the S14 tangent-trace resubmit."""
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
from verify import digest

FRAMES = [
    (178.5, "S14 board"), (181.5, "S14 Q"), (184.7, "S14 expansion"),
    (187.0, "S14 LOVE"), (188.5, "S14 heart opens"), (189.5, "S14 trace"),
    (190.5, "S14 peak held"), (192.3, "S14 THE PEAK"),
    (193.2, "S14->S15 dissolve"), (194.0, "S15 heart forms"), (200.0, "S15 wait"),
    (204.0, "S15 still"), (205.37, "S15 block E"), (206.4, "S15 blocks"),
    (207.873, "S15 chime"), (208.5, "S15 last gaze"), (209.5, "S15 held"),
    (209.87, "WHITE FLASH 1f"), (209.9, "S16 black"), (210.3, "S16 heart"),
    (210.8, "S16 complete"), (211.2, "S16 collapse"), (211.6, "S16 closing"),
    (211.9, "S16 end"),
]
MOTION_TABLE = [
    ("S14", "黑板展开", "177.44 词 onset，0.6s smoothstep"),
    ("S14", "公式第一行打印", "179.2 词 onset，逐字 0.5s"),
    ("S14", "Q/A 落下", "181.02/182.75 词 onset"),
    ("S14", "代数式写全+宇宙重合", "184.6 词 onset（段内模式转换动机），星场 0.5s 重合"),
    ("S14", "LOVE 三块按音节印入", "184.21/184.51/184.81（lo/o/ove→L/O/VE，冲击≤6帧）"),
    ("S14", "心形求根逐点描出", "188.29 起，0.26s 描完，闭合锁重拍 188.55"),
    ("S14", "金光线光棘轮", "188.55 起 36 条逐条点亮只升不降 + 曝光棘轮 0.90→1.10"),
    ("S14", "游标沿切线离开", "188.29-189.58 单向（you are free），轨迹残留至段末"),
    ("S14", "她在心形边界内", "189.58 trapped 词 onset，align 0→1"),
    ("S14", "峰值静止", "190.5-192.94 字节级冻结（≥1.2s）"),
    ("S15", "心脏 h(t) 成形", "193.5 起 2.5s 成形 + 每拍搏动（204.5 停止）"),
    ("S15", "ECG 波形", "锁拍，随频谱衰减"),
    ("S15", "命令卡+提示符", "常驻；提示符 205.37 前 0.5Hz 闪烁后熄灭"),
    ("S15", "EXECUTION 四块", "205.37 实测 / 205.96 / 206.19 / 206.42 初值（cues.py）"),
    ("S15", "青金心搏三下", "207.873/208.373/208.873（提示音实测时刻），环半径 240"),
    ("S15", "最后凝视特写", "207.873 起 0.4s 单向放大后静止（starry）"),
    ("S15", "白闪 1 帧", "209.87 锁拍（cues.py s16_flash），画面 luma=1.000、邻帧 0.123"),
    ("S16", "心脏余搏三下", "210.2/210.75/211.3，幅度递减"),
    ("S16", "完成日志逐字", "210.0 起 32 字符×0.05s"),
    ("S16", "内存回收 hex 流", "210.3 起滚动（确定性 prng）"),
    ("S16", "CRT 收束", "210.9 起背景压缩成带，心脏留在中央"),
    ("S16", "关机扫描线", "211.0 起单向自上而下"),
    ("S16", "shy 立绘渐隐", "210.6-211.7 单向"),
    ("S16", "结束语淡入", "211.35 起 `exit 0 · world executed · heart remains`"),
]


def main():
    lines = ["# v15 delivery report: batch E (S14-S16)", ""]
    lines += ["## 1. 64x36 structure maps", ""]
    for t, tag in FRAMES:
        lines.append(f"### {tag} ({t}s)")
        lines += structure_map(film.frame(t))
        lines.append("")
    lines += ["## 2. error-red table", ""]
    for t, tag in FRAMES:
        lines.append(f"t={t:7.3f}s {tag}: error_red={error_red(film.frame(t))}")
    lines.append("")
    lines += ["## 3. motion-driver table", ""]
    for sec, layer, driver in MOTION_TABLE:
        lines.append(f"- {sec} {layer}: {driver}")
    lines.append("")
    lines += ["## 4. determinism (two renders, sha256)", ""]
    for t, tag in [(178.5, "S14"), (188.5, "S14"), (192.3, "S14 peak"),
                   (205.37, "S15"), (207.873, "S15 chime"), (209.87, "flash"),
                   (210.8, "S16"), (211.9, "S16 end")]:
        a, b = digest(film.frame(t)), digest(film.frame(t))
        lines.append(f"t={t:7.3f}s ({tag}): {a[:16]} {'IDENTICAL' if a == b else 'DIFFER'}")
    lines.append("")
    import audit
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit.main()
    lines += ["## 5. layout adjacency", "", buf.getvalue().strip(), ""]
    out = ROOT / "out" / "report_batche.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("report saved:", out)


if __name__ == "__main__":
    main()
