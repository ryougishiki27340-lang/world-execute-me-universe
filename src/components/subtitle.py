"""The lyric band: word-by-word typing, flicker, keyword colouring, Chinese line."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from engine.prng import prng
from engine.draw import font, text

ROOT = Path(__file__).resolve().parents[2]
TIMELINE = json.loads((ROOT / "data" / "lyric_timing.json").read_text(encoding="utf-8"))
ZH = json.loads((ROOT / "data" / "zh_subtitles.json").read_text(encoding="utf-8")) \
    if (ROOT / "data" / "zh_subtitles.json").exists() else {}
LINES = {line["id"]: line for line in TIMELINE["lines"]}

KEYWORDS = {"world", "execute", "execution", "you", "me", "love", "simulation",
            "dimension", "circumference", "tangent", "infinity", "limitations",
            "current", "travel", "unite", "satisfaction", "happy", "eggplant",
            "tomato", "cat", "god", "proof", "gender", "am", "pm", "role",
            "trance", "vibrations", "completion", "isolation", "fragments",
            "disheartened", "illegal", "arguments", "free", "trapped"}
GLYPHS = "!<>-_\\/[]{}=+*^?#%$&@01|~"


def active_line(t):
    import bisect
    starts = sorted(LINES, key=lambda i: LINES[i]["start"])
    k = bisect.bisect_right([LINES[i]["start"] for i in starts], t) - 1
    if k < 0:
        return None
    ln = LINES[starts[k]]
    return ln if ln["start"] <= t < ln["end"] + 0.6 else None


def band(img, cfg, t):
    """Fixed position: English word-by-word + Chinese whole line, per film rules."""
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1000, 1920, 1080], fill=(8, 9, 13))
    d.line([(48, 1002), (1872, 1002)], fill=(45, 52, 70), width=2)
    ln = active_line(t)
    if ln is None:
        return
    mono = font(cfg["fonts"]["mono_bold"], 34)
    x = 72
    for word in ln.get("words", []):
        if t < word["start"]:
            break
        shown = word["text"]
        age = t - word["start"]
        if age < 0.08:
            rng = prng(31, word["start"])
            shown = "".join(rng.choice(GLYPHS) if ch != " " else " " for ch in shown)
        key = word["text"].strip(".,!?;'").lower()
        col = (232, 199, 107) if key in KEYWORDS else (232, 230, 223)
        ImageDraw.Draw(img).text((x, 1018), shown, font=mono, fill=col)
        x += mono.getlength(shown) + mono.getlength(" ")
    zh = ZH.get(str(ln["id"]))
    if zh and t >= ln["start"] + 0.05:
        ImageDraw.Draw(img).text((72, 1062), zh, font=font(cfg["fonts"]["cjk"], 26),
                                 fill=(150, 156, 170))
