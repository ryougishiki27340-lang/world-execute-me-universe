"""world.execute(me); - main renderer entry.

Determinism: frame(t) is a pure function of song time; all randomness flows
through src/engine/prng.prng(seed, t). Two renders with the same parameters
are byte-identical (tools/verify.py).

Step 3 status: the three review frames (S14 heart-close, S01 title-reassembly,
S03 point side-face) are fully drawn; other times render the neutral
placeholder grid until their sections are built (S01..S16, per STORYBOARD).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from engine import prng as prng_mod
from engine import post as post_mod
from engine.draw import circle, font, line, rrect, text
from components import char as char_mod
from components import formula as formula_mod
from components import subtitle as sub_mod
from cues import CUES

CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
W, H = CFG["video"]["width"], CFG["video"]["height"]
FPS = CFG["video"]["fps"]
P = {k: tuple(int(v.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
     for k, v in CFG["palettes"].items()}
MONO = CFG["fonts"]["mono"]
MONO_B = CFG["fonts"]["mono_bold"]
CJK = CFG["fonts"]["cjk"]
SERIF = CFG["fonts"]["serif_italic"]

_beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
BEATS = _beats["beats"]
BEAT_LEN = _beats["beat_len"]
BEAT0 = _beats["beat_first"]
_timeline = json.loads((ROOT / "data" / "lyric_timing.json").read_text(encoding="utf-8"))
LYRIC_LINES = {line["id"]: line for line in _timeline["lines"]}

# S12: the twelve shouts are the twelve round starts (measured word onsets).
ROUND_STARTS = [LYRIC_LINES[i]["start"] for i in range(67, 79)]
S12_END = 162.59


def B(bar):
    """Song seconds of bar `bar` (bar 0 starts at beat 0)."""
    return BEAT0 + bar * 4 * BEAT_LEN


def Bt(beat):
    """Song seconds of global beat number `beat`."""
    return BEAT0 + beat * BEAT_LEN


def nearest_beat(t, k=0):
    i = int(round((t - BEAT0) / BEAT_LEN)) + k
    return BEAT0 + i * BEAT_LEN


def near_beat(t, tol=0.08):
    """True when song time sits within tol of a measured beat."""
    d = abs((t - BEAT0) / BEAT_LEN - round((t - BEAT0) / BEAT_LEN))
    return d < tol / BEAT_LEN


def pulse(t, at, half=0.12):
    return math.exp(-(t - at) / half) if t >= at else 0.0


def mixc3(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def lerp(a, b, u):
    return a + (b - a) * u


def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _stripes(img):
    d = ImageDraw.Draw(img)
    for x in range(0, W, 3):
        d.line([(x, 0), (x, H)], fill=(17, 18, 23), width=1)


def _log_window(img, lines, x=40, y=44, w=560, title="sys.log"):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + w, y + 24 + 22 * len(lines)], radius=8,
                        fill=(10, 11, 16), outline=(48, 54, 70), width=1)
    text(img, (x + 12, y + 4), title, MONO_B, 15, (130, 140, 160))
    for i, (s, col) in enumerate(lines):
        text(img, (x + 12, y + 30 + 22 * i), s, MONO, 16, col)


def _spectrum_strip(img, t):
    d = ImageDraw.Draw(img)
    d.rectangle([48, 1024, 1872, 1068], outline=(40, 46, 62), width=1)
    rng = prng_mod.prng(99, t)
    for i in range(96):
        amp = 0.15 + 0.85 * abs(math.sin(i / 9.0 + t * 1.7))
        h = int(8 + 30 * amp)
        col = P["cyan"] if i % 5 else P["gold"]
        d.rectangle([52 + i * 19, 1040 - h, 62 + i * 19, 1040], fill=col)


def _empty_band(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1000, W, H], fill=(8, 9, 13))
    d.line([(48, 1002), (1872, 1002)], fill=(45, 52, 70), width=2)


def _placeholder(t):
    img = Image.new("RGB", (W, H), P["bg"])
    _stripes(img)
    d = ImageDraw.Draw(img)
    for x in range(80, W, 80):
        d.line([(x, 0), (x, H)], fill=(30, 34, 46), width=1)
    for y in range(60, H, 80):
        d.line([(0, y), (W, y)], fill=(30, 34, 46), width=1)
    text(img, (W / 2, H / 2 - 40), "world.execute(me);", MONO_B, 64, P["fg"], anchor="mm")
    text(img, (W / 2, H / 2 + 28), "section renderer not built yet (step 4)",
         MONO, 24, (120, 128, 146), anchor="mm")
    return img


# ---------------------------------------------------------------- S01 0-16.04
def render_s01(t):
    img = Image.new("RGB", (W, H), (9, 10, 14))
    _stripes(img)
    d = ImageDraw.Draw(img)
    # power switch: flips at the first lyric word
    pu = min(1.0, max(0.0, (t - 0.06) / 0.7))
    cx, cy = 560, 80
    rrect(d, [cx - 80, cy - 26, cx + 80, cy + 26], 10, fill=(70, 92, 136),
          outline=(80, 92, 118), w=2)
    text(img, (cx, cy - 30), "POWER", MONO_B, 16, P["fg"], anchor="mm")
    a = math.radians(-40 + 80 * pu)
    line(d, (cx, cy), (cx + 44 * math.cos(a), cy + 44 * math.sin(a)), P["fg"], 4)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=P["syn_green"] if pu >= 1 else (70, 80, 100))
    # BIOS log lines appear with the lyric lines (L0..L7)
    entries = [
        (0.06, "Power on self test ... OK", P["syn_green"]),
        (1.79, "safety goggles: ON", P["fg"]),
        (3.86, "Memory 262144K OK", P["fg"]),
        (5.42, "OBJECT CREATION ...", P["fg"]),
        (7.38, "DATA PARAMETERS:", P["fg"]),
        (10.13, "initialization ...", P["fg"]),
        (11.21, "set up new world ...", P["fg"]),
        (12.76, "begin simulation", P["fg"]),
    ]
    log = [(s, c) for (at, s, c) in entries if t >= at]
    _log_window(img, log, x=40, y=130, w=620, title="bios.log")
    # prompt: the command typed word by word
    cmd = "world.execute(me);"
    n = min(len(cmd), int((t - 1.79) * 3.0)) if t >= 1.79 else 0
    text(img, (44, 470), ">>>", MONO_B, 34, P["gold"])
    text(img, (124, 472), cmd[:n], MONO_B, 34, P["fg"])
    if int(t * 4) % 2 == 0 and t >= 1.79:
        d.rectangle([124 + font(MONO_B, 34).getlength(cmd[:n]), 476, 142 + font(MONO_B, 34).getlength(cmd[:n]), 506],
                    fill=P["fg"])
    # parameter card: rows fill on L4 words, her hand writes them
    rows = [("NAME", "you", 7.38), ("AFFECTION", "+inf", 8.4), ("SEED", "her heart", 8.9), ("MODE", "serve", 9.3)]
    rrect(d, [44, 560, 720, 780], 10, fill=(12, 14, 20), outline=(58, 66, 86), w=1)
    text(img, (64, 576), "DATA PARAMETERS", MONO_B, 20, P["cyan"])
    for i, (k, v, at) in enumerate(rows):
        yy = 618 + i * 36
        text(img, (72, yy), k, MONO, 20, (150, 158, 176))
        if t >= at:
            text(img, (300, yy), v, MONO, 20, P["fg"])
    # progress bar: 0 -> 99% (L5), hitch at 99, then 100% (L7 end)
    if t < 10.13:
        bar = 0.0
    elif t < 12.76:
        bar = min(0.99, 0.2 + 0.79 * (t - 10.13) / 2.0)
    else:
        bar = min(1.0, 0.99 + 0.01 * (t - 12.76) / 2.0)
    d.rectangle([64, 830, 960, 866], outline=(58, 66, 86), width=1)
    d.rectangle([68, 836, 68 + 888 * bar, 860], fill=P["syn_green"])
    text(img, (64, 872), f"building world {int(bar * 100)}%", MONO, 18, P["syn_green"])
    # her avatar window (interface form): shy -> serious; goggles glyph at L1
    expr = "serious" if t >= 5.42 else "shy"
    char_mod.portrait_window(img, CFG, t, expr, (1280, 470, 1860, 990), "her")
    if t >= 1.79:
        g = min(1.0, (t - 1.79) / 0.4)
        gx, gy = 1340, 520
        for s in (-1, 1):
            d.ellipse([gx + s * 40 - 26, gy - 26, gx + s * 40 + 26, gy + 26],
                      outline=(210, 218, 236), width=int(4 * g))
        d.line([(gx - 62, gy - 8), (gx + 62, gy - 8)], fill=(210, 218, 236), width=int(4 * g))
    # 16.04: the characters have re-assembled the title
    title = "WORLD.EXECUTE(ME);"
    f = font(MONO_B, 80)
    total = f.getlength(title)
    x0 = (W - total) / 2
    rng = prng_mod.prng(77, t)
    if t >= 15.9:
        u = min(1.0, (t - 15.9) / 0.14)
        for i, ch in enumerate(title):
            jx = rng.uniform(-2, 2) * (1 - u) * 6
            col = P["gold"] if ch in ".;" else P["cyan"] if ch in "MEW" else P["fg"]
            d.text((x0 + f.getlength(title[:i]) + jx, 140), ch, font=f, fill=col)
        for k in range(18):
            px = x0 + total * rng.random()
            py = 60 + rng.random() * 300 * (1 - u)
            d.text((px, py), rng.choice("01!<>#%&"), font=f, fill=(70, 80, 100))
    _spectrum_strip(img, t)
    _empty_band(img)
    return post_mod.post(img, t, CFG, vignette=0.24)


# ---------------------------------------------------------------- S03 @~30.5
def render_s03(t):
    img = Image.new("RGB", (W, H), (10, 14, 24))
    _stripes(img)
    d = ImageDraw.Draw(img)
    # bright full-frame grid (structure + brightness budget)
    for x in range(60, W, 60):
        d.line([(x, 0), (x, H)], fill=(88, 114, 150), width=2)
    for y in range(50, H, 60):
        d.line([(0, y), (W, y)], fill=(88, 114, 150), width=2)
    # grid axes: full-width horizontal + full-height vertical (>=60% screen),
    # bright, with you/me endpoints
    ax_col = (125, 190, 240)
    line(d, (70, 560), (1850, 560), ax_col, 3)
    line(d, (960, 70), (960, 1010), ax_col, 3)
    d.polygon([(1842, 552), (1862, 560), (1842, 568)], fill=ax_col)
    d.polygon([(952, 78), (960, 58), (968, 78)], fill=ax_col)
    text(img, (1820, 590), "you", MONO_B, 34, P["fg"], anchor="mm")
    text(img, (990, 96), "me", MONO_B, 34, P["fg"])
    # the point set gathering into her side-face (word-onset driven)
    align = min(1.0, max(0.0, (t - 29.77) / 1.7))
    char_mod.point_side_face(img, CFG, t, (700, 440), 330, align=align,
                             fill=(190, 242, 255), n=2600, ds=2.0)
    # unit circle + orbiting dot (radius >= 15% of height = 162px)
    r = 170
    cx, cy = 1440, 310
    if t >= 33.45:
        sweep = min(1.0, (t - 33.45) / 0.9)
        circle(d, (cx, cy), r, P["cyan"], 3, a0=-90, a1=-90 + 360 * sweep)
        for k in range(12):
            a = 2 * math.pi * k / 12
            d.ellipse([cx + r * math.cos(a) - 3, cy + r * math.sin(a) - 3,
                       cx + r * math.cos(a) + 3, cy + r * math.sin(a) + 3], fill=P["cyan"])
    if t >= 34.99:
        a = -math.pi / 2 + 2 * math.pi * min(1.0, (t - 34.99) / 1.9)
        d.ellipse([cx + r * math.cos(a) - 8, cy + r * math.sin(a) - 8,
                   cx + r * math.cos(a) + 8, cy + r * math.sin(a) + 8], fill=P["fg"])
    # sine: real sampling, >= 3 periods, bright; tangent white flashes at L13
    if t >= 37.10:
        n_pts = int(min(260, (t - 37.10) / 0.35 * 260))
        pts = [(150 + i * 6, 760 - 120 * math.sin(i / 24.0)) for i in range(max(2, n_pts))]
        d.line(pts, fill=(255, 228, 140), width=4)
        text(img, (170, 700), "y = sin x", MONO_B, 26, (255, 228, 140))
    if t >= 38.69:
        for j in (32, 80, 128):
            x = 150 + j * 6
            y = 760 - 120 * math.sin(j / 24.0)
            k = pulse(t, 38.69 + (j % 3) * 0.12, 0.18)
            if k > 0.02:
                d.line([(x - 60, y - 60), (x + 60, y + 60)], fill=(255, 255, 255), width=3)
    if t >= 40.82:
        inf_u = min(1.0, (t - 40.82) / 0.7)
        text(img, (1560, 660), "∞", SERIF, int(90 + 40 * inf_u), (232, 230, 223), anchor="mm")
    if t >= 42.26:
        wall_u = min(1.0, (t - 42.26) / 0.25)
        wx = 1560
        for yy in range(400, 760, 18):
            d.line([(wx, yy), (wx, yy + 10)], fill=(220, 120, 90), width=3)
        text(img, (wx, 380), "lim", SERIF, 40, (220, 120, 90), anchor="mm")
        d.rectangle([wx + 12, 400, wx + 420, 760], fill=(10, 14, 24))
        if wall_u < 1:
            for yy in range(400, 760, 6):
                off = int((1 - wall_u) * 26)
                d.line([(wx + off, yy), (wx + 30 + off, yy)], fill=(120, 140, 170), width=2)
    # formula chips: filled mid-bright panels (readable structure)
    chips = [("x = cos t", 1180), ("y = sin t", 1430), ("z² = x² + y²", 1680)]
    for label, x0 in chips:
        rrect(d, [x0, 830, x0 + 220, 884], 8, fill=(52, 66, 96),
              outline=(120, 140, 176), w=1)
        text(img, (x0 + 14, 844), label, MONO_B, 22, (235, 238, 246))
    # 4D hypercube projection, corner, clear wireframe
    import numpy as np
    def rot4(pts, a, plane=(1, 2)):
        c, s = math.cos(a), math.sin(a)
        p = np.asarray(pts, dtype=float).copy()
        i, j = plane
        pi, pj = p[:, i].copy(), p[:, j].copy()
        p[:, i], p[:, j] = c * pi - s * pj, s * pi + c * pj
        return p
    verts = [[(s >> k) & 1 for k in range(4)] for s in range(16)]
    v4 = rot4([[x * 2 - 1 for x in v] for v in verts], t * 0.35)
    v3 = np.asarray([(x / (2.6 - w * 0.6), y / (2.6 - w * 0.6)) for x, y, z, w in v4]) * 190
    for a in range(16):
        for b in range(a):
            if bin(a ^ b).count("1") == 1:
                d.line([(1660 + v3[a][0], 300 + v3[a][1]),
                        (1660 + v3[b][0], 300 + v3[b][1])], fill=(178, 150, 228), width=3)
    text(img, (1660, 110), "tesseract", MONO_B, 20, (178, 150, 228), anchor="mm")
    _log_window(img, [
        ("dimensionality: 2 -> 3", (255, 255, 255)),
        ("req: 100% -> you", (255, 255, 255)),
        ("orbit locked", (255, 255, 255)),
        ("sampling sin x ...", (255, 255, 255)),
        ("project 4D -> 3D", (255, 255, 255)),
        ("epoch 1/1e6", (255, 255, 255)),
        ("loss 0.0000", (255, 255, 255)),
        ("> ready", (255, 255, 255)),
    ], x=40, y=40, w=620)
    _spectrum_strip(img, t)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.22)


# ---------------------------------------------------------------- S02 16.04-29.77
def render_s02(t):
    img = Image.new("RGB", (W, H), (9, 11, 18))
    _stripes(img)
    d = ImageDraw.Draw(img)
    # perspective spacetime grid (rotating slowly)
    vp = (960, 300)
    for k in range(14):
        x = 120 + k * 140
        d.line([(x, 180), (vp[0] + (x - vp[0]) * 0.28, 900)], fill=(40, 58, 92), width=2)
    for k in range(8):
        y = 220 + k * 85
        d.line([(100, y), (1820, y)], fill=(34, 50, 80), width=1)
    # data streams: four 40px-wide bands flowing from the edges to the centre
    rng = prng_mod.prng(23, t)
    cx0, cy0 = 1350, 480
    def edge_stream(edge, i):
        u = (t * 0.22 + i * 0.047) % 1.0
        if edge == 0:      # top
            x = 120 + (i * 137) % 1680
            y = 20 + u * 300
        elif edge == 1:    # left
            x = 20 + u * 520
            y = 120 + (i * 113) % 740
        elif edge == 2:    # bottom
            x = 120 + (i * 149) % 1680
            y = 920 - u * 300
        else:              # right
            x = 1900 - u * 520
            y = 120 + (i * 97) % 740
        d.rectangle([x, y, x + 2, y + 16], fill=(110, 205, 240))
    for i in range(200):
        edge_stream(i % 4, i)
    # geometric primitives born per beat
    # primitive clusters (>=200x200 each), born per beat
    for k in range(4):
        at = 17.2 + k * 2.6
        if t < at:
            break
        gx, gy = 120 + k * 300, 360
        rrect(d, [gx - 20, gy - 120, gx + 180, gy + 100], 8, fill=(70, 92, 136),
              outline=(58, 78, 110), w=2)
        if k == 0:      # point cluster
            for i in range(20):
                d.ellipse([gx + (i * 37) % 160 - 4, gy + (i * 53) % 170 - 70 - 4,
                           gx + (i * 37) % 160 + 4, gy + (i * 53) % 170 - 70 + 4],
                          fill=P["cyan"])
            text(img, (gx + 80, gy + 70), "points", MONO, 16, (170, 190, 220), anchor="mm")
        elif k == 1:    # line
            d.line([(gx, gy), (gx + 170, gy)], fill=P["cyan"], width=5)
            text(img, (gx + 80, gy + 70), "line", MONO, 16, (170, 190, 220), anchor="mm")
        elif k == 2:    # circle
            circle(d, (gx + 80, gy - 30), 68, P["cyan"], 4)
            text(img, (gx + 80, gy + 70), "circle", MONO, 16, (170, 190, 220), anchor="mm")
        else:           # sine
            pts = [(gx + j * 6, gy - 30 - 48 * math.sin(j / 5.0)) for j in range(30)]
            d.line(pts, fill=P["cyan"], width=4)
            text(img, (gx + 80, gy + 70), "sine", MONO, 16, (170, 190, 220), anchor="mm")
    # progress closes S01's 99% hitch
    bar = min(1.0, 0.99 + 0.01 * max(0.0, (t - 17.5) / 2.2))
    d.rectangle([700, 820, 1600, 844], outline=(58, 66, 86), width=1)
    d.rectangle([704, 824, 704 + 892 * bar, 840], fill=P["syn_green"])
    text(img, (700, 852), f"world build {int(bar * 100)}%", MONO, 18, P["syn_green"])
    # module-online log, one line per beat
    mods = ["bus ... online", "clock ... online", "memory ... online", "renderer ... online",
            "physics ... online", "spacetime ... online", "love ... online", "you ... online"]
    log = [(mods[k], (255, 255, 255)) for k in range(len(mods)) if t >= 17.6 + k * 1.4]
    _log_window(img, log[-6:], x=40, y=44, w=560, title="sys.modules")
    # her data form: ASCII whale at the world's centre (cheerful glance first)
    if t < 18.2:
        a = 1.0 - max(0.0, (t - 17.2) / 1.0)
        if a > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            char_mod.portrait_window(lay, CFG, t, "cheerful", (900, 560, 1500, 990), "her")
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            img.paste(lay, (0, 0), lay)
    breath = 1.0 + 0.05 * math.sin(t * 1.3)
    char_mod.ascii_whale(img, CFG, t, (1350, 480), size=int(20 * breath))
    _spectrum_strip(img, t)
    _empty_band(img)
    return post_mod.post(img, t, CFG, vignette=0.2)


# ---------------------------------------------------------------- S04 44.41-59.06 (v9 redo)
def _silhouette(d, x, kind, fill=(130, 170, 220), hollow=False):
    """Solid era blocks (>=80x120 each); spark-passed ones become outlines."""
    if kind == "towers":
        for i in range(3):
            hh = 100 + (i % 2) * 55
            box = [x + i * 44, 760 - hh, x + i * 44 + 34, 760]
            d.rectangle(box, fill=None if hollow else fill,
                        outline=fill if hollow else None, width=3)
    elif kind == "spires":
        for i in range(3):
            hh = 120 + (i % 2) * 40
            pts = [(x + i * 48, 760 - hh), (x + i * 48 + 16, 760 - hh - 36),
                   (x + i * 48 + 32, 760 - hh), (x + i * 48 + 32, 760), (x + i * 48, 760)]
            if hollow:
                d.line(pts + [pts[0]], fill=fill, width=3)
            else:
                d.polygon(pts, fill=fill)
    elif kind == "colonnade":
        if hollow:
            for i in range(5):
                d.rectangle([x + i * 34, 620, x + i * 34 + 18, 760], outline=fill, width=3)
            d.rectangle([x - 8, 600, x + 170, 624], outline=fill, width=3)
        else:
            for i in range(5):
                d.rectangle([x + i * 34, 620, x + i * 34 + 18, 760], fill=fill)
            d.rectangle([x - 8, 600, x + 170, 624], fill=fill)
    else:  # pyramids
        if hollow:
            d.line([(x, 760), (x + 55, 610), (x + 110, 760), (x, 760)], fill=fill, width=3)
            d.line([(x + 120, 760), (x + 160, 660), (x + 200, 760), (x + 120, 760)], fill=fill, width=3)
        else:
            d.polygon([(x, 760), (x + 55, 610), (x + 110, 760)], fill=fill)
            d.polygon([(x + 120, 760), (x + 160, 660), (x + 200, 760)], fill=fill)


def render_s04(t):
    img = Image.new("RGB", (W, H), (6, 10, 26))
    _stripes(img)
    d = ImageDraw.Draw(img)
    for x in range(40, W, 40):
        d.line([(x, 60), (x, 1020)], fill=(22, 34, 58), width=1)
    # full-width power trace (the current flows through the machine)
    mode = "AC" if t < 45.76 else "DC"
    if mode == "AC":
        pts = [(60 + i * 6, 240 - 70 * math.sin(i / 6.0 + (t - 44.4) * 5)) for i in range(300)]
        d.line(pts, fill=P["cyan"], width=4)
    else:
        d.line([(60, 240), (1860, 240)], fill=(255, 255, 255), width=4)
    # meter panel
    rrect(d, [90, 320, 620, 620], 10, fill=(58, 80, 118), outline=(70, 90, 130), w=2)
    text(img, (110, 340), "CURRENT METER", MONO_B, 20, (120, 150, 200))
    if mode == "AC":
        pts2 = [(160 + i * 10, 520 - 110 * math.sin(i / 4.0 + (t - 44.4) * 6)) for i in range(44)]
        d.line(pts2, fill=P["cyan"], width=3)
    else:
        d.line([(160, 520), (600, 520)], fill=(255, 255, 255), width=5)
    for yy in range(556, 596, 8):
        d.line([(160, yy), (600, yy)], fill=(40, 56, 88), width=1)
    text(img, (110, 600), f"mode: {mode}", MONO_B, 22, P["fg"])
    # one-shot beat-locked chromatic dispersion at L18
    if 47.71 <= t < 48.4:
        k = pulse(t, 47.71, 0.22)
        for i in range(8):
            d.line([(780 + i * 16, 140), (900 + i * 16, 620)],
                   fill=mixc3((79, 214, 232), (150, 90, 220), i / 8), width=6)
    # spiral at L19
    if t >= 49.68:
        for i in range(14):
            a0 = i * 0.55 + (t - 49.68) * 4
            circle(d, (1200, 420), 8 + i * 22, (190, 205, 235), 3,
                   a0=math.degrees(a0), a1=math.degrees(a0 + 4.6))
    # era silhouettes: solid blocks; the spark hollows what it passes
    if 51.45 <= t < 55.08:
        fade = min(1.0, (55.08 - t) / 0.4)
        fill = (int(130 * fade), int(170 * fade), int(220 * fade))
        d.line([(60, 760), (1860, 760)], fill=(120, 150, 200), width=2)
        scroll = (t - 51.45) * 260
        spark_x = 150 + scroll
        for ex, kind in [(360, "towers"), (820, "spires"), (1280, "colonnade"), (1680, "pyramids")]:
            ax = ex - scroll
            if ax < -230 or ax > 1920:
                continue
            _silhouette(d, ax, kind, fill, hollow=(ax + 200 < spark_x))
        d.ellipse([spark_x - 12, 740, spark_x + 12, 764], fill=P["gold"])
        for xx, label in ((240, "BC"), (1720, "AD")):
            if t >= 53.37 + (0 if label == "BC" else 0.35):
                d.rectangle([xx - 40, 700, xx + 40, 760], fill=(14, 18, 34),
                            outline=(220, 226, 240), width=4)
                text(img, (xx, 730), label, MONO_B, 26, (240, 240, 246), anchor="mm")
    # double helix: two interleaved strands (>=2 periods), merge locked to L23
    if t >= 55.08:
        merge = min(1.0, (t - 57.11) / 0.7)
        amp = 96 * (1 - merge)
        # reveal fast so that two full periods are on screen by 55.3 s
        n_pts = int(min(110, (t - 55.08) / 0.22 * 110)) + 1
        for k, col in ((0, P["cyan"]), (1, (235, 200, 120))):
            pts = [(700 + j * 11, 920 - j * 7 + amp * math.sin(j / 7.0 + k * math.pi))
                   for j in range(n_pts)]
            if len(pts) > 1:
                d.line(pts, fill=col, width=5)
                glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                gd = ImageDraw.Draw(glow)
                gd.line(pts, fill=col + (60,), width=13)
                img.paste(glow, (0, 0), glow)
        if merge > 0:
            d.line([(700, 920), (1900, 120)], fill=(255, 236, 180), width=6)
            mg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(mg).line([(700, 920), (1900, 120)], fill=(255, 236, 180, 80), width=18)
            img.paste(mg, (0, 0), mg)
    # epoch log, bottom-right, >=6 lines with real content
    entries = [(44.41, "mode: AC"), (45.76, "mode: DC"), (47.71, "vision: dispersed"),
               (49.68, "dizzy: on"), (51.45, "epochs: BC -> AD"), (53.37, "AD / BC landed"),
               (55.08, "fusion: two fields"), (57.11, "merged: one field")]
    fixed = ["epoch.log", "field monitor: on", "timeline: local", "cursor: you (online)"]
    log = [(s, (180, 190, 210)) for s in fixed]
    entry_log = [(s, (255, 255, 255)) for at, s in entries if t >= at]
    log = log + entry_log[-2:]
    _log_window(img, log, x=1120, y=790, w=760, title="epoch.log")
    _spectrum_strip(img, t)
    _empty_band(img)
    return post_mod.post(img, t, CFG, vignette=0.22)


# ---------------------------------------------------------------- S05 59.06-73.93
def render_s05(t):
    img = Image.new("RGB", (W, H), (10, 13, 20))
    _stripes(img)
    d = ImageDraw.Draw(img)
    for x in range(60, W, 60):
        d.line([(x, 0), (x, H)], fill=(58, 70, 96), width=2)
    for y in range(50, H, 60):
        d.line([(0, y), (W, y)], fill=(58, 70, 96), width=2)
    # monitor matrix: five nested windows, each with real content
    win = [(70, 110, 680, 390, "RACK"), (700, 110, 1280, 390, "LORENZ"),
           (1300, 110, 1850, 390, "PENDULUM"), (70, 410, 680, 700, "THERMAL"),
           (700, 410, 1280, 700, "SATISFACTION")]
    for x0, y0, x1, y1, title in win:
        rrect(d, [x0, y0, x1, y1], 10, fill=(13, 17, 28), outline=(62, 76, 104), w=2)
        text(img, (x0 + 12, y0 + 8), title, MONO_B, 16, (140, 160, 195))
    # rack window: cabinets with leds
    for i in range(4):
        d.rectangle([100 + i * 130, 170, 220 + i * 130, 340], outline=(70, 88, 122), width=2)
        for r_ in range(5):
            led = (int(t * 3) + i + r_) % 6 == 0
            d.ellipse([112 + i * 130, 186 + r_ * 30, 120 + i * 130, 194 + r_ * 30],
                      fill=P["cyan"] if led else (46, 66, 100))
    # lorenz window (real RK4 trace, precomputed path scaled)
    lz = lorenz_path(240)
    pts = [(720 + x * 0.95, 330 - y * 0.62) for (x, y) in lz]
    d.line(pts, fill=P["cyan"], width=2)
    text(img, (990, 370), "σ=10 ρ=28 β=8/3", MONO, 14, (140, 160, 195), anchor="mm")
    # pendulum window: chaotic double-pendulum history trace + live rods
    pp = pendulum_path(260)
    tr = [(1305 + x, 120 + y) for (x, y) in pp]
    d.line(tr, fill=(112, 94, 58), width=5)
    d.line(tr, fill=(235, 200, 120), width=2)
    a1 = math.sin((t - 59.06) * 2.2) * 0.8
    a2 = math.sin((t - 59.06) * 3.1 + 1.2) * 1.1
    p0 = (1490, 220)
    p1 = (p0[0] + 90 * math.sin(a1), p0[1] + 90 * math.cos(a1))
    p2 = (p1[0] + 80 * math.sin(a2), p1[1] + 80 * math.cos(a2))
    d.line([p0, p1, p2], fill=(250, 215, 140), width=6)
    d.ellipse([p1[0] - 6, p1[1] - 6, p1[0] + 6, p1[1] + 6], fill=(255, 255, 255))
    d.ellipse([p2[0] - 9, p2[1] - 9, p2[0] + 9, p2[1] + 9], fill=P["fg"])
    # thermal window: heatmap
    for gy in range(6):
        for gx in range(9):
            hot = (gy + gx) / 14 + 0.1 * math.sin(t * 2 + gy)
            d.rectangle([96 + gx * 62, 448 + gy * 36, 148 + gx * 62, 474 + gy * 36],
                        fill=mixc3((24, 40, 74), P["gold"], min(1.0, hot)))
    # satisfaction dial (gold sector = satisfaction progress)
    dial = min(1.0, (t - 59.06) / 8.0)
    ccx, ccy = 990, 550
    circle(d, (ccx, ccy), 130, (205, 214, 234), 5)
    if dial > 0:
        d.pieslice([ccx - 130, ccy - 130, ccx + 130, ccy + 130],
                   -90, -90 + 360 * dial, fill=P["gold"])
    for k in range(12):
        aa = math.radians(k * 30)
        d.line([(ccx + 118 * math.cos(aa), ccy + 118 * math.sin(aa)),
                (ccx + 130 * math.cos(aa), ccy + 130 * math.sin(aa))],
               fill=(205, 214, 234), width=4)
    a = -90 + 360 * dial
    d.line([(ccx, ccy), (ccx + 112 * math.cos(math.radians(a)), ccy + 112 * math.sin(math.radians(a)))],
           fill=(255, 255, 255) if dial >= 1 else P["cyan"], width=5)
    text(img, (ccx, ccy - 152), f"satisfaction {int(dial * 100)}%", MONO_B, 18,
         P["gold"] if dial >= 1 else (140, 160, 195), anchor="mm")
    # EXECUTE toolbar button + cursor watching + her hand presses (L30)
    bx0, by0, bx1, by1 = 1300, 410, 1850, 560
    press = min(1.0, (t - 69.34) / 0.18) if t >= 69.34 else 0.0
    rrect(d, [bx0, by0 + press * 8, bx1, by1 + press * 8], 10,
          fill=(70, 92, 136),
          outline=(120, 150, 200), w=3)
    text(img, (bx0 + (bx1 - bx0) / 2, by0 + 75 + press * 8), "EXECUTE", MONO_B, 30,
         (255, 255, 255), anchor="mm")
    if t >= 68.2:      # cursor approaches and hovers (watches only)
        cu = min(1.0, (t - 68.2) / 0.8)
        cx, cy = lerp(1560, 1575, cu), lerp(820, 470, cu)
        d.polygon([(cx, cy), (cx + 14, cy + 22), (cx + 4, cy + 20)], fill=(235, 238, 246))
    if press:          # her hand crosses over the cursor and presses
        hand = char_mod.char_crop("serious", 170, (0.55, 1.0))
        img.paste(hand, (1420 - int(hand.width / 2), 380 - int(hand.height / 2)), hand)
    if t >= 70.12:     # cage boundary
        for i in range(14):
            k = min(1.0, (t - 70.12 - i * 0.06) / 0.15)
            if k <= 0:
                continue
            y0 = 90 + i * 50
            d.line([(56, y0), (1864, y0)], fill=(120, 140, 175), width=int(2 * k))
    _log_window(img, [("monitors: 5 online", (255, 255, 255)),
                      ("satisfaction: rising", (255, 255, 255)),
                      ("EXECUTE: pressed", (255, 255, 255)) if t >= 69.34 else
                      ("EXECUTE: ready", (255, 255, 255)),
                      ("containment: optional", (255, 255, 255))], x=40, y=760, w=620)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.2)


def lorenz_path(n=240, dt=0.015):
    """Lorenz attractor (σ=10, ρ=28, β=8/3) integrated with RK4; normalized."""
    x, y, z = 0.1, 0.0, 0.0
    pts = []
    for _ in range(n * 14):
        def f(x, y, z):
            return (10 * (y - x), x * (28 - z) - y, x * y - 8 / 3 * z)
        k1 = f(x, y, z)
        k2 = f(x + dt / 2 * k1[0], y + dt / 2 * k1[1], z + dt / 2 * k1[2])
        k3 = f(x + dt / 2 * k2[0], y + dt / 2 * k2[1], z + dt / 2 * k2[2])
        k4 = f(x + dt * k3[0], y + dt * k3[1], z + dt * k3[2])
        x += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        y += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        z += dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
        if _ % 14 == 0:
            pts.append((x, y, z))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    mnx, mxx = min(xs), max(xs)
    mny, mxy = min(ys), max(ys)
    return [((p[0] - mnx) / (mxx - mnx) * 460, (p[1] - mny) / (mxy - mny) * 150)
            for p in pts[:n]]


def pendulum_path(n=260, dt=0.006):
    """Chaotic double-pendulum history (g=9.81, L1=L2=m1=m2=1, semi-implicit Euler).

    Deterministic: fixed initial state, no randomness; normalized to 520x250
    so render_s05 can map it straight into the PENDULUM monitor window.
    """
    th1, th2, w1, w2 = 2.4, 2.0, 0.0, 0.0
    pts = []
    for i in range(n * 24):
        dden = 3.0 - math.cos(2 * th1 - 2 * th2)
        a1 = (-9.81 * 3 * math.sin(th1) - 9.81 * math.sin(th1 - 2 * th2)
              - 2 * math.sin(th1 - th2) * (w2 * w2 + w1 * w1 * math.cos(th1 - th2))) / dden
        a2 = (2 * math.sin(th1 - th2) * (2 * w1 * w1 + 2 * 9.81 * math.cos(th1)
              + w2 * w2 * math.cos(th1 - th2))) / dden
        w1 += a1 * dt
        w2 += a2 * dt
        th1 += w1 * dt
        th2 += w2 * dt
        if i % 24 == 0:
            pts.append((math.sin(th1) + math.sin(th2), math.cos(th1) + math.cos(th2)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    mnx, mxx, mny, mxy = min(xs), max(xs), min(ys), max(ys)
    return [((p[0] - mnx) / (mxx - mnx) * 520, (p[1] - mny) / (mxy - mny) * 250)
            for p in pts[:n]]


# ---------------------------------------------------------------- S06 73.93-88.54
def render_s06(t):
    img = Image.new("RGB", (W, H), (9, 12, 18))
    _stripes(img)
    d = ImageDraw.Draw(img)
    for x in range(60, W, 60):
        d.line([(x, 0), (x, H)], fill=(54, 66, 92), width=2)
    for y in range(50, H, 60):
        d.line([(0, y), (W, y)], fill=(54, 66, 92), width=2)
    spot = {"eggplant": (123, 82, 171), "tomato": (212, 67, 47)}
    cards = [("eggplant", 73.93), ("tomato", 77.71), ("tabby cat", 81.28), ("only God", 85.13)]
    for ci, (kind, at) in enumerate(cards):
        if t < at:
            break
        x0 = 80 + (ci % 2) * 760
        y0 = 110 + (ci // 2) * 370
        open_u = 1.0 if t >= at + 1.4 else 0.0
        rrect(d, [x0, y0, x0 + 680, y0 + 320], 10, fill=(14, 18, 30), outline=(70, 86, 116), w=2)
        text(img, (x0 + 18, y0 + 12), kind, MONO_B, 18, (140, 160, 195))
        text(img, (x0 + 18, y0 + 40), f"MORPH: me -> {kind}", MONO, 16, P["gold"])
        c = (x0 + 200, y0 + 190)
        if kind == "eggplant":
            col = spot["eggplant"]
            d.ellipse([c[0] - 62, c[1] - 90, c[0] + 62, c[1] + 60], fill=col)
            d.polygon([(c[0] - 14, c[1] - 95), (c[0], c[1] - 145), (c[0] + 14, c[1] - 95)], fill=(72, 124, 88))
            if open_u:
                d.line([(c[0], c[1] - 60), (c[0], c[1] + 60)], fill=(255, 255, 255), width=3)
                d.ellipse([c[0] - 50, c[1] - 46, c[0] + 50, c[1] + 40], outline=(255, 255, 255), width=2)
            text(img, (x0 + 420, y0 + 150), "nutrients", MONO, 20, (232, 230, 223))
        elif kind == "tomato":
            col = spot["tomato"]
            d.ellipse([c[0] - 58, c[1] - 58, c[0] + 58, c[1] + 58], fill=col)
            d.ellipse([c[0] - 58, c[1] - 74, c[0] + 58, c[1] - 20], fill=(72, 124, 88))
            if open_u:
                d.line([(c[0] - 40, c[1] - 10), (c[0] + 40, c[1] + 10)], fill=(255, 255, 255), width=3)
                for i in range(3):
                    d.ellipse([c[0] - 40 + i * 26, c[1] - 6, c[0] - 22 + i * 26, c[1] + 8],
                              outline=(255, 255, 255), width=2)
            text(img, (x0 + 420, y0 + 150), "antioxidants", MONO, 20, (232, 230, 223))
        elif kind == "tabby cat":
            d.ellipse([c[0] - 54, c[1] - 50, c[0] + 54, c[1] + 52], outline=(220, 210, 180), width=3)
            for s in (-1, 1):
                d.polygon([(c[0] + s * 48, c[1] - 40), (c[0] + s * 72, c[1] - 96), (c[0] + s * 88, c[1] - 34)],
                          outline=(220, 210, 180), width=3)
            for k in range(3):
                d.line([(c[0] - 30, c[1] - 14 + k * 14), (c[0] + 30, c[1] - 14 + k * 14)],
                       fill=(150, 120, 70), width=3)
            if open_u:
                pts = [(x0 + 430 + i * 6, y0 + 170 - 26 * math.sin(i / 2.2)) for i in range(36)]
                d.line(pts, fill=P["gold"], width=3)
            text(img, (x0 + 420, y0 + 150), "purr -> ECG", MONO, 20, (232, 230, 223))
        else:
            circle(d, (c[0], c[1] - 34), 34, P["gold"], 3)
            d.ellipse([c[0] - 26, c[1] - 60, c[0] + 26, c[1] - 8], fill=P["gold"])
            d.ellipse([c[0] - 34, c[1] - 34, c[0] + 34, c[1] + 40], outline=(230, 220, 200), width=3)
            for k in range(16):
                a = k * math.pi / 8
                d.line([(c[0] + 48 * math.cos(a), c[1] - 44 + 48 * math.sin(a)),
                        (c[0] + 80 * math.cos(a), c[1] - 44 + 80 * math.sin(a))], fill=P["gold"], width=3)
            text(img, (x0 + 420, y0 + 150), "proof of existence", MONO, 20, (232, 230, 223))
            rrect(d, [x0 + 320, y0 + 180, x0 + 510, y0 + 250], 6, fill=(70, 92, 136),
                  outline=P["cyan"], w=4)
            text(img, (x0 + 415, y0 + 202), "you", MONO_B, 26, P["cyan"], anchor="mm")
    # the observer's cursor lands on the proof frame at L39
    if t >= 87.92:
        u = min(1.0, (t - 87.92) / 0.5)
        cx, cy = lerp(1600, 1535, u), lerp(900, 688, u)
        d.polygon([(cx, cy), (cx + 12, cy + 20), (cx + 3, cy + 18)], fill=(235, 238, 246))
        if u >= 1:
            d.line([(1535, 688), (1535, 700)], fill=P["cyan"], width=3)
    _log_window(img, [("morph: active", (255, 255, 255)),
                      ("observer: you", (255, 255, 255))], x=40, y=780, w=620)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.2)


# ---------------------------------------------------------------- S07 88.54-103.52
def render_s07(t):
    img = Image.new("RGB", (W, H), (16, 12, 8))
    _stripes(img)
    d = ImageDraw.Draw(img)
    for x in range(60, W, 60):
        d.line([(x, 0), (x, H)], fill=(80, 62, 30), width=2)
    for y in range(50, H, 60):
        d.line([(0, y), (W, y)], fill=(80, 62, 30), width=2)
    letters = [("F", 90.57), ("M", 91.72), ("AM", 94.52), ("PM", 95.19), ("S", 98.19), ("M", 99.10)]
    for i, (ch, at) in enumerate(letters):
        x = 180 + i * 150
        filled = t >= at
        rrect(d, [x, 150, x + 120, 280], 10,
              fill=(90, 70, 26) if filled else (24, 18, 10),
              outline=(200, 160, 70), w=5)
        text(img, (x + 60, 215), ch, MONO_B, 56, (255, 230, 170) if filled else (90, 74, 40),
             anchor="mm")
    # parameter card fields (F/M, S/M) update in the panel; portrait unchanged
    rrect(d, [60, 340, 660, 620], 10, fill=(14, 11, 8), outline=(110, 86, 34), w=2)
    text(img, (84, 360), "STATE MACHINE", MONO_B, 20, (210, 170, 70))
    rows = [("Gender", "M" if t >= 91.72 else ("F" if t >= 90.57 else "—"), 90.57),
            ("On call", "AM" if t < 95.19 else "PM", 93.94),
            ("Role", "M" if t >= 99.10 else ("S" if t >= 98.19 else "—"), 97.70),
            ("Loop", "on" if t >= 100.28 else "off", 100.28)]
    for i, (k, v, at) in enumerate(rows):
        text(img, (92, 420 + i * 52), k, MONO, 20, (180, 160, 120))
        if t >= at:
            text(img, (420, 420 + i * 52), v, MONO_B, 22, (255, 230, 170))
    # AM/PM day-night orbit
    cc = (1180, 470)
    circle(d, cc, 170, (210, 180, 120), 7)
    for k in range(24):
        aa = math.radians(k * 15)
        d.line([(cc[0] + 158 * math.cos(aa), cc[1] + 158 * math.sin(aa)),
                (cc[0] + 170 * math.cos(aa), cc[1] + 170 * math.sin(aa))],
               fill=(210, 180, 120), width=4)
    a = -90 + 360 * min(1.0, (t - 93.94) / 1.3) * (1 if t < 95.19 else -1)
    d.ellipse([cc[0] + 170 * math.cos(math.radians(a)) - 13, cc[1] + 170 * math.sin(math.radians(a)) - 13,
               cc[0] + 170 * math.cos(math.radians(a)) + 13, cc[1] + 170 * math.sin(math.radians(a)) + 13],
              fill=P["gold"])
    text(img, (cc[0], cc[1] - 190), "AM -> PM", MONO_B, 20, (210, 170, 70), anchor="mm")
    # trance ripples: persistent trance rings + expanding pulses
    if t >= 99.26:
        for rr in (40, 72, 104):
            circle(d, (1540, 470), rr, (205, 155, 75), 5)
        for i in range(5):
            u = min(1.0, (t - 99.26 - i * 0.22) / 0.9)
            if u <= 0:
                continue
            circle(d, (1540, 470), 16 + 104 * u, (235, 185, 95), 6)
    # her avatar: confused, unchanged (no art swap)
    char_mod.portrait_window(img, CFG, t, "confused", (1600, 560, 1860, 990), "her")
    _log_window(img, [("state: altered", (255, 255, 255)),
                      ("loop: on" if t >= 100.28 else "loop: off", (255, 255, 255))],
                x=40, y=780, w=620)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.2)


# ---------------------------------------------------------------- S08 103.52-110.41
def render_s08(t):
    img = Image.new("RGB", (W, H), (8, 12, 22))
    _stripes(img)
    d = ImageDraw.Draw(img)
    for x in range(60, W, 60):
        d.line([(x, 0), (x, H)], fill=(72, 94, 126), width=2)
    for y in range(50, H, 60):
        d.line([(0, y), (W, y)], fill=(72, 94, 126), width=2)
    cc = (880, 470)
    # epicycles: one circle lands per beat (8 terms of the heart contour)
    n_terms = int(min(8, max(0, (t - 103.52) / 0.4618)))
    ang = (t - 103.52) * 1.4
    px, py = cc
    for k in range(1, n_terms + 1):
        r = 24 + 8 * k
        w = k if k % 2 else -k
        circle(d, (px, py), r, P["cyan"], 4)
        nx = px + r * math.cos(ang * w)
        ny = py + r * math.sin(ang * w)
        d.line([(px, py), (nx, ny)], fill=P["cyan"], width=2)
        px, py = nx, ny
    # the traced heart contour emerges from the epicycle pen
    if n_terms >= 8:
        u = min(1.0, (t - 107.1) / 2.0)
        heart_pts = formula_mod.heart_points(cc[0], cc[1], 300, n=240)
        seg = heart_pts[: max(2, int(len(heart_pts) * u))]
        d.line(seg, fill=P["gold"], width=4)
    # completion ring closes and thickens at L51
    ring = min(1.0, (t - 108.98) / 1.4)
    if ring > 0:
        circle(d, cc, 360, P["gold"], int(2 + 5 * ring), a0=-90, a1=-90 + 360 * ring)
    if t >= 108.98:
        flash = pulse(t, 108.98, 0.16)
        if flash > 0.5:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([cc[0] - 370, cc[1] - 370, cc[0] + 370, cc[1] + 370],
                                       fill=P["gold"] + (int(70 * (flash - 0.5) / 0.5),))
            img.paste(ov, (0, 0), ov)
    _log_window(img, [("resonance: rising", (255, 255, 255)),
                      ("completion ring: closing", (255, 255, 255))],
                x=40, y=780, w=620)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.2)


# ---------------------------------------------------------------- S09 110.41-118.24
def render_s09(t):
    """Departure (raw data space, desaturating). No portrait assets: she is the
    starmap core. One link breaks per 'left' line (hard cut at each onset)."""
    img = Image.new("RGB", (W, H), (8, 10, 16))
    _stripes(img)
    d = ImageDraw.Draw(img)
    u = min(1.0, (t - 110.41) / 7.83)                     # decay / desaturation
    brk = [112.2, 113.25, 113.93, 114.76, 116.01]         # five 'left' lines
    for x in range(80, W, 80):
        d.line([(x, 0), (x, 1020)], fill=(18, 22, 32), width=1)
    for y in range(60, 1020, 80):
        d.line([(0, y), (W, y)], fill=(18, 22, 32), width=1)
    # starfield: fixed positions, brightness decays with the departure
    rng = prng_mod.prng(41, 0)
    for _ in range(600):
        x, y = rng.uniform(30, 1890), rng.uniform(30, 990)
        s = rng.uniform(0.6, 3.2)
        k = max(0.22, 1.0 - 0.62 * u)
        d.rectangle([x, y, x + s, y + s],
                    fill=(int(150 * k), int(196 * k), int(224 * k)))
    bright5 = [(420, 260), (780, 180), (1500, 240), (310, 700), (1650, 760)]
    for i, (x, y) in enumerate(bright5):
        dim = 1.0 if t < brk[i] else 0.62
        sc = max(0.35, dim * (1.0 - 0.35 * u))
        d.ellipse([x - 24, y - 24, x + 24, y + 24],
                  fill=(int(180 * sc), int(205 * sc), int(235 * sc)))
        d.ellipse([x - 8, y - 8, x + 8, y + 8],
                  fill=(int(235 * sc), int(240 * sc), int(248 * sc)))
        d.ellipse([x - 30, y - 30, x + 30, y + 30],
                  outline=(int(150 * sc), int(180 * sc), int(210 * sc)), width=2)
    # node network: ring of 12 + spokes; five primary spokes snap (hard cuts)
    core = (960, 470)
    nodes = [(core[0] + 330 * math.cos(math.radians(i * 30)),
              core[1] + 205 * math.sin(math.radians(i * 30))) for i in range(12)]
    ring = tuple(int(c * (1 - 0.5 * u)) for c in (95, 130, 160))
    for i in range(12):
        d.line([nodes[i], nodes[(i + 1) % 12]], fill=ring, width=2)
    node_col = tuple(int(c * (1 - 0.4 * u)) for c in (150, 190, 220))
    for x, y in nodes:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=node_col)
    spoke_col = tuple(int(c * (1 - 0.35 * u)) for c in (79, 214, 232))
    break_idx = [2, 4, 7, 9, 11]
    for i in range(12):
        at = brk[break_idx.index(i)] if i in break_idx else None
        if at is not None and t >= at:
            if t < at + 0.25:                       # <=6 frames of sparks
                r2 = prng_mod.prng(50 + i, t)
                mx, my = (core[0] + nodes[i][0]) / 2, (core[1] + nodes[i][1]) / 2
                for _ in range(8):
                    a = r2.uniform(0, 2 * math.pi)
                    rr = r2.uniform(6, 42)
                    d.rectangle([mx + rr * math.cos(a), my + rr * math.sin(a),
                                 mx + rr * math.cos(a) + 2, my + rr * math.sin(a) + 2],
                                fill=P["gold"])
            continue
        d.line([core, nodes[i]], fill=spoke_col, width=3)
    # her: the starmap core (signal flickers after the isolation line)
    d.ellipse([core[0] - 70, core[1] - 70, core[0] + 70, core[1] + 70],
              fill=tuple(int(c * (1 - 0.25 * u)) for c in (46, 124, 148)))
    r3 = prng_mod.prng(61, 0)
    dots = [(core[0] + r * math.cos(a), core[1] + r * math.sin(a))
            for a, r in ((i * 2.39996, 16 + 30 * math.sqrt(i / 40)) for i in range(40))]
    fr = (0.7 + 0.3 * prng_mod.prng(61, t).random()) if t >= 116.01 else 1.0
    sc = fr * (1 - 0.2 * u)
    for x, y in dots:
        d.rectangle([x, y, x + 3, y + 3],
                    fill=(int(120 * sc), int(225 * sc), int(242 * sc)))
    d.ellipse([core[0] - 60, core[1] - 60, core[0] + 60, core[1] + 60],
              outline=tuple(int(c * sc) for c in (140, 220, 238)), width=2)
    # the observer's cursor leaves; after 116.01 it fades, only a ghost remains
    cu = min(1.0, (t - 110.41) / 5.6)
    cx, cy = lerp(1500, 1940, cu), lerp(640, 560, cu)
    path = [(lerp(1500, 1940, i / 48.0), lerp(640, 560, i / 48.0)) for i in range(49)]
    if cu > 0:
        d.line(path[: max(1, int(cu * 48))], fill=(110, 114, 122), width=2)
    alpha = 1.0 if t < 116.01 else max(0.0, 1.0 - (t - 116.01) / 0.7)
    if alpha > 0:
        col = (int(235 * alpha), ) * 3
        d.polygon([(cx, cy), (cx + 14, cy + 22), (cx + 4, cy + 20)], fill=col)
    else:
        gx, gy = 1940, 560
        d.polygon([(gx, gy), (gx + 14, gy + 22), (gx + 4, gy + 20)],
                  outline=(96, 98, 106), width=2)
    # beat-locked particles near the core
    if near_beat(t):
        bt = nearest_beat(t)
        age = t - bt
        if 0 <= age < 0.5:
            for i in range(12):
                a = i * math.pi / 6 + bt * 0.7
                rr = 50 + age * 320
                d.rectangle([core[0] + rr * math.cos(a), core[1] + rr * math.sin(a),
                             core[0] + rr * math.cos(a) + 2,
                             core[1] + rr * math.sin(a) + 2],
                            fill=P["cyan"] if i % 3 else P["gold"])
    # signal island: her pings, unanswered (word onsets)
    ping_lines = [("core: online", (150, 158, 176))]
    if t >= 116.01:
        ping_lines.append(("> ping you ...", (110, 205, 232)))
    if t >= 116.6:
        ping_lines.append(("timeout (no reply)", (150, 158, 176)))
    if t >= 117.3:
        ping_lines.append(("you have left", (255, 255, 255)))
    _log_window(img, ping_lines, x=40, y=760, w=620, title="core.log")
    # desaturation: the universe fades to grey while she keeps pinging
    m = min(0.62, 0.18 * u + 0.44 * max(0.0, (t - 116.01) / 2.23))
    img = Image.blend(img, ImageOps.grayscale(img).convert("RGB"), m)
    _spectrum_strip(img, t)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.24)


# ---------------------------------------------------------------- S10 118.24-133.95
def render_s10(t):
    """Trial (terminal shell). You are the defendant (cursor afterimage); she
    judges from the bench. Everything stays grey/white/black until the first
    red at 131.21 (L64 'illegal arguments', cues.py first_red)."""
    img = Image.new("RGB", (W, H), (19, 20, 23))
    _stripes(img)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=(12, 13, 16))
    text(img, (60, 8), "court_sim v1.0 - terminal", MONO_B, 18, (220, 224, 232))
    d.line([(0, 34), (W, 34)], fill=(140, 150, 165), width=2)
    d.rectangle([0, 34, 6, H], fill=(28, 30, 36))
    d.rectangle([W - 6, 34, W, H], fill=(28, 30, 36))
    # GC sweep (118.24 -> 120.21): eraser passes over the debris of broken links
    rng = prng_mod.prng(71, 0)
    debris = [(rng.uniform(120, 1800), rng.uniform(240, 560), rng.uniform(-0.9, 0.9))
              for _ in range(24)]
    if 118.24 <= t < 121.5:
        sweep = min(1.0, (t - 118.24) / 1.97)
        ex = 80 + sweep * (W - 160)
        for x, y, tilt in debris:
            if x < ex:
                continue
            d.line([(x, y), (x + 24 * math.cos(tilt), y + 24 * math.sin(tilt))],
                   fill=(140, 145, 155), width=3)
        rrect(d, [ex - 18, 150, ex + 18, 640], 8, fill=(110, 116, 128),
              outline=(150, 157, 171), w=2)
        for k in range(5):
            sx = ex - rng.uniform(4, 40)
            sy = rng.uniform(160, 630)
            d.rectangle([sx, sy, sx + 2, sy + 2], fill=P["gold"])
    # DISHEARTENED falls (122.01), brightens on the word itself (125.0)
    if t >= 122.01:
        drop = min(1.0, (t - 122.01) / 0.8)
        yy = lerp(-240, 330, drop)
        word_on = 1.0 if t >= 125.0 else 0.72
        f = font(MONO_B, 96)
        total = f.getlength("DISHEARTENED")
        x0 = (W - total) / 2
        for i, ch in enumerate("DISHEARTENED"):
            jy = (1 - drop) * (i % 3) * 26
            col = tuple(int(c * word_on) for c in (205, 207, 213))
            d.text((x0 + f.getlength("DISHEARTENED"[:i]), yy + jy), ch,
                   font=f, fill=col)
    # memory cleanup progress: resets to zero at 123.83 and barely creeps
    if t < 123.83:
        pv = 1.0
    else:
        pv = min(0.05, (t - 123.83) / 100.0) + 0.003 * prng_mod.prng(82, t).random()
    rrect(d, [60, 60, 620, 100], 6, fill=(108, 114, 128), outline=(140, 150, 165), w=2)
    d.rectangle([64, 64, 64 + 552 * pv, 96], fill=(205, 207, 213))
    text(img, (60, 108), f"memory clean {pv * 100:.1f}%", MONO, 18, (180, 184, 194))
    # the court expands at 125.58 ('Challenging your God')
    if t >= 125.58:
        s = smoothstep((t - 125.58) / 0.6)
        cw, ch = int(600 * s) + 1, int(290 * s) + 1
        cx0, cy0 = W // 2 - cw, 470 - ch
        cx1, cy1 = W // 2 + cw, 470 + ch
        if s > 0.05:
            rrect(d, [cx0 - 30, cy0 - 30, cx1 + 30, cy1 + 30], 12,
                  fill=(14, 15, 18), outline=(90, 98, 112), w=3)
            text(img, (cx0, cy0 - 14), "COURT", MONO_B, 18, (170, 176, 188))
            d.rectangle([cx0 + 10, cy0 + 60, cx1 - 10, cy0 + 104],
                        fill=(150, 154, 164))                     # judge bench
            text(img, (cx0 + 20, cy0 + 74), "JUDGE", MONO_B, 20, (30, 32, 38))
            d.rectangle([cx0 + cw - 80, cy1 - 160, cx0 + cw + 30, cy1 + 10],
                        fill=(108, 114, 128))                     # defendant stand
            text(img, (cx0 + cw - 70, cy1 - 140), "DEFENDANT", MONO_B, 18, (28, 30, 36))
            d.polygon([(cx0 + cw - 45, cy1 - 90), (cx0 + cw - 31, cy1 - 68),
                       (cx0 + cw - 41, cy1 - 70)], fill=(90, 94, 102))
            text(img, (W // 2, cy1 - 80), "your leaving", MONO, 22, (150, 156, 168),
                 anchor="mm")
    # judge bench portrait (interface form; desaturated for the grey trial)
    _portrait_judge(img, t)
    # error stack rolls from 125.58; the last line turns red only at 131.21
    stack = [(125.58, "Error", (168, 172, 180)),
             (126.1, "  at leave() line 3", (168, 172, 180)),
             (126.65, "  at release() line 7", (168, 172, 180)),
             (127.2, "  at goodbye() line 12", (168, 172, 180)),
             (128.87, "  args: you.leave(...)", (168, 172, 180)),
             (131.21, "error: illegal arguments (caller: you)", P["alert"])]
    shown = [(s, c) for at, s, c in stack if t >= at]
    if shown:
        rrect(d, [1420, 110, 1860, 760], 8, fill=(10, 11, 14), outline=(90, 98, 112), w=2)
        text(img, (1436, 122), "error.stack", MONO_B, 16, (170, 176, 188))
        for i, (s, c) in enumerate(shown[-5:]):
            text(img, (1436, 154 + i * 28), s, MONO, 17, c)
    # parameter line types the arguments you passed (128.87)
    if t >= 128.87:
        rrect(d, [1420, 780, 1860, 940], 8, fill=(10, 11, 14), outline=(90, 98, 112), w=2)
        text(img, (1436, 788), "args", MONO_B, 22, (170, 176, 188))
        par = "you.leave({reason: null, stay: false})"
        n = min(len(par), int((t - 128.87) / 0.035))
        text(img, (1436, 826), par[:n], MONO, 26, (168, 172, 180))
    # gavel falls at 128.87 (grey, no red)
    if t >= 128.87:
        gu = min(1.0, (t - 128.87) / 0.5)
        a = math.radians(-72 + 72 * gu)
        gx, gy = 720, 310
        hx = gx + 110 * math.cos(a)
        hy = gy + 110 * math.sin(a)
        d.line([(gx, gy), (hx, hy)], fill=(150, 154, 164), width=10)
        d.rectangle([hx - 80, hy - 22, hx + 80, hy + 22], fill=(150, 154, 164),
                    outline=(100, 104, 114), width=2)
        if gu >= 1:
            for k in range(3):
                d.arc([gx + 90 - k * 14, gy - 40 - k * 14, gx + 130 + k * 14, gy + 40 + k * 14],
                      200, 300, fill=(170, 174, 184), width=3)
    # verdict: the FIRST RED, locked to 131.21 ('illegal arguments')
    if t >= 131.21:
        rv = min(1.0, (t - 131.21) / 0.15)
        rrect(d, [600, 600, 1340, 820], 10, fill=(16, 12, 13),
              outline=P["alert"], w=5)
        text(img, (970, 640), "VERDICT", MONO_B, 22, (255, 255, 255), anchor="mm")
        f = font(MONO_B, 64)
        total = f.getlength("ILLEGAL ARGUMENTS")
        x0 = 970 - total / 2
        d.text((x0, 700), "ILLEGAL ARGUMENTS", font=f,
               fill=tuple(int(c * rv) for c in P["alert"]))
        text(img, (970, 786), "(caller: you)", MONO, 24, (220, 210, 212), anchor="mm")
    # triple white stamp (the gavel seals it, 3 flashes inside the budget)
    for fs in (132.05, 132.5, 132.95):
        age = t - fs
        if 0 <= age < 0.18:
            k = 1 - age / 0.18
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            r = int(52 * k)
            ld.ellipse([960 - r, 720 - r, 960 + r, 720 + r],
                       fill=(255, 255, 255, int(200 * k)))
            ld.ellipse([960 - r - 12, 720 - r - 12, 960 + r + 12, 720 + r + 12],
                       outline=(255, 255, 255, int(160 * k)), width=4)
            img.paste(lay, (0, 0), lay)
    # trial log
    log = [("court_sim: online", (255, 255, 255))]
    for at, s, c in ((118.24, "gc: sweep", (255, 255, 255)),
                     (120.21, "fragments: erased", (255, 255, 255)),
                     (122.01, "heart: disheartened", (255, 255, 255)),
                     (125.58, "court: open", (255, 255, 255)),
                     (128.87, "args: received", (255, 255, 255)),
                     (131.21, "verdict: ILLEGAL ARGUMENTS", P["alert"])):
        if t >= at:
            log.append((s, c))
    _log_window(img, log[-4:], x=40, y=760, w=620, title="trial.log")
    _spectrum_strip(img, t)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.22)


def _portrait_judge(img, t):
    """Interface portrait at the bench (top). Grey-trial desaturation so the
    art never carries red before L64."""
    expr = "angry" if t >= 131.21 else "exasperated"
    rect = (820, 40, 1100, 360)
    tmp = Image.new("RGB", (W, H), (0, 0, 0))
    char_mod.portrait_window(tmp, CFG, t, expr, rect, "judge: her")
    crop = tmp.crop(rect)
    out = Image.blend(crop, ImageOps.grayscale(crop).convert("RGB"), 0.4)
    img.paste(out, rect[:2])
    d = ImageDraw.Draw(img)
    d.rectangle([800, 368, 1120, 398], fill=(200, 202, 210))     # bench bar


# ---------------------------------------------------------------- S11 133.95-147.89
def render_s11(t):
    """Collapse (raw data space, black-red). One collapse step per beat;
    t_singularity hits 0.00 on the same frame the singularity forms. She is
    the singularity (data form, no portrait assets)."""
    T0, T1 = 133.95, 147.89
    img = Image.new("RGB", (W, H), (26, 7, 8))
    _stripes(img)
    d = ImageDraw.Draw(img)
    beat_step = int((t - T0) / BEAT_LEN)
    k = min(1.0, beat_step / 30.0)                      # monotonic collapse
    # framework prompts
    text(img, (60, 60), "[ collapsing... ]", MONO_B, 30, (210, 140, 132))
    text(img, (1620, 54), f"t_singularity: {max(0.0, T1 - t):05.2f}",
         MONO_B, 34, (245, 245, 250), anchor="rm")
    # galaxies: one beat-step inward each beat (monotonic, stepped)
    gals = [((300, 280), 100), ((1620, 780), 112), ((1580, 200), 90)]
    for gi, ((gx0, gy0), r0) in enumerate(gals):
        gx = lerp(gx0, 960, k) + 8 * math.sin(gi * 2.1)
        gy = lerp(gy0, 470, k) + 8 * math.cos(gi * 1.7)
        rr = r0 * (1 - 0.55 * k)
        col = mixc3((185, 180, 174), (168, 76, 64), 0.92 * k)
        circle(d, (gx, gy), rr, col, 2)
        circle(d, (gx, gy), rr * 0.62, col, 2)
        r4 = prng_mod.prng(91 + gi, 0)
        for i in range(16):
            a = i * math.pi / 8
            rr2 = rr * r4.uniform(0.25, 0.9)
            d.rectangle([gx + rr2 * math.cos(a), gy + rr2 * math.sin(a),
                         gx + rr2 * math.cos(a) + 3, gy + rr2 * math.sin(a) + 3],
                        fill=col)
    # mandelbrot silhouette, one-way zoom (black-red palette, red allowed S11+)
    mand = _mandel_mask(1.0 + k * 4.0)
    img.paste(mand.resize((1120, 780), Image.NEAREST), (400, 150))
    # wavefunction: the packet collapses into the centre
    sigma = 500 * (1 - k) + 45
    colw = mixc3((215, 215, 215), (205, 98, 92), k)
    pts = []
    for i in range(320):
        x = 60 + i * 5.6
        y = 640 + 62 * math.exp(-((x - 960) ** 2) / (2 * sigma * sigma)) * \
            math.sin(i / 8.0 - (t - T0) * 4)
        pts.append((x, y))
    d.line(pts, fill=colw, width=4)
    pts2 = [(x, 640 + 30 * math.exp(-((x - 960) ** 2) / (2 * sigma * sigma)) *
             math.sin(i / 13.0 + (t - T0) * 3)) for i, (x, _) in enumerate(pts)]
    d.line(pts2, fill=tuple(int(c * 0.8) for c in colw), width=2)
    # the singularity (= her): energy accumulates ring by ring per beat
    sing_col = mixc3((235, 225, 190), (220, 90, 80), k)
    for i in range(1, 31):
        circle(d, (960, 470), 4 + i * 3, sing_col, 2 if i % 4 else 3)
    d.ellipse([960 - (26 * (1 - k) + 4), 470 - (26 * (1 - k) + 4),
               960 + (26 * (1 - k) + 4), 470 + (26 * (1 - k) + 4)],
              fill=(255, 248, 218))
    # particles spiral into the centre on each beat
    if near_beat(t):
        bt = nearest_beat(t)
        age = t - bt
        if 0 <= age < 0.5:
            for i in range(14):
                a = i * math.pi / 7 + age * 3
                rr = 540 * (1 - age / 0.5) + 30
                d.rectangle([960 + rr * math.cos(a), 470 + rr * math.sin(a),
                             960 + rr * math.cos(a) + 2, 470 + rr * math.sin(a) + 2],
                            fill=mixc3((235, 230, 220), (220, 90, 80), k))
    # silenced error log (low-frequency energy)
    s_lines = [("error.log: silent", (150, 152, 162)), ("heartbeat: fading", (150, 152, 162))]
    if t >= 138.0:
        s_lines.append(("observer: absent", (150, 152, 162)))
    if t >= 142.0:
        s_lines.append(("mass: 1 point", (150, 152, 162)))
    _log_window(img, s_lines, x=40, y=760, w=620, title="collapse.log")
    _spectrum_strip(img, t)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.3)


def _mandel_mask(zoom):
    """Mandelbrot silhouette at 280x195 (black-red), centred on the set.
    Inside = dark, outside = bright red field, boundary = hot. Deterministic."""
    W0, H0 = 280, 195
    cx0, cy0 = -0.5, 0.0
    span = 3.1 / zoom
    xs = np.linspace(cx0 - span * W0 / H0 / 2, cx0 + span * W0 / H0 / 2, W0)
    ys = np.linspace(cy0 - span / 2, cy0 + span / 2, H0)
    c = xs[None, :] + 1j * ys[:, None]
    z = np.zeros_like(c)
    live = np.ones_like(c, dtype=bool)
    for _ in range(64):
        z[live] = z[live] * z[live] + c[live]
        esc = np.abs(z) > 2
        live &= ~esc
    inside = live
    out = np.empty((H0, W0, 3), np.uint8)
    out[inside] = (26, 7, 8)
    out[~inside] = (160, 52, 46)
    from scipy import ndimage as ndi
    ring = ndi.binary_dilation(inside, iterations=2) & ~inside
    out[ring] = (255, 168, 144)
    return Image.fromarray(out, "RGB")


# ---------------------------------------------------------------- S12 147.89-162.59
def _s12_round(t):
    """Round index 0..11 and phase 0..1 for song time t (round 12 ends at 162.59)."""
    for k in range(12):
        start = ROUND_STARTS[k]
        end = ROUND_STARTS[k + 1] if k < 11 else S12_END
        if start <= t < end:
            return k, min(1.0, (t - start) / (end - start))
    return 11, 1.0


def render_s12(t, zoom=1.0):
    """EXECUTION: twelve identical two-beat loops. Each round fast-forwards the
    whole universe life (big bang -> heat death) with one stage featured; the
    say(love) line stays unreachable; only the ERR label carries red."""
    from data.facts import UNIVERSE_STAGES, LOVE_LOOP
    k, u = _s12_round(t)
    img = Image.new("RGB", (W, H), (18, 6, 8))
    _stripes(img)
    d = ImageDraw.Draw(img)
    # code listing (the dead loop; line 07 is forever unreachable)
    x0, y0 = 90, 140
    for i, code in enumerate(LOVE_LOOP):
        yy = y0 + i * 44
        if i == 6:
            text(img, (x0, yy), f"0{i + 1} {code}  // unreachable", MONO, 26, (120, 90, 95))
            continue
        text(img, (x0, yy), f"0{i + 1}", MONO, 26, (150, 110, 115))
        text(img, (x0 + 70, yy), code, MONO, 26, (215, 210, 212))
    # four letter blocks E X E C land on lines 02-05 (highlight moves down)
    syl = [ROUND_STARTS[k] + i * 0.23 for i in range(4)]
    if k == 11:
        syl = [CUES["last_syl1"][0], CUES["last_syl2"][0],
               CUES["last_syl3"][0], CUES["last_syl4"][0]]
    for i, ch in enumerate("EXEC"):
        at = syl[i]
        if t < at:
            continue
        yy = y0 + (i + 1) * 44
        d.rectangle([x0, yy - 8, x0 + 620, yy + 34], fill=(52, 18, 22))
        d.rectangle([650, yy - 8, 706, yy + 38], fill=(245, 245, 248))
        text(img, (678, yy + 16), ch, MONO_B, 30, (20, 10, 12), anchor="mm")
    # the loop back-edge arrow lights once per round (after the blocks land)
    lit = 1.0 if u > 0.86 else 0.0
    arrow_col = mixc3((120, 70, 74), (240, 190, 180), lit)
    d.line([(56, y0 + 6 * 44 + 6), (56, y0 - 14)], fill=arrow_col, width=3)
    d.polygon([(50, y0 - 4), (56, y0 - 22), (62, y0 - 4)], fill=arrow_col)
    text(img, (56, y0 + 6 * 44 + 24), "loop", MONO, 16, arrow_col, anchor="mm")
    # round counter + featured stage name
    stage_name, marker, fact = UNIVERSE_STAGES[k]
    text(img, (960, 48), f"ROUND {k + 1:02d}/12  ·  {stage_name}", MONO_B, 34,
         (255, 225, 215), anchor="mm")
    text(img, (960, 92), f"{marker}  |  {fact}", MONO, 18, (190, 150, 150), anchor="mm")
    # per-round first-beat light pulse (amplitude <=0.25, counted in the budget)
    pu = pulse(t, ROUND_STARTS[k], 0.12)
    if pu > 0.02:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([760, -30, 1160, 140],
                                    outline=(255, 230, 210, int(70 * pu)), width=6)
        img.paste(lay, (0, 0), lay)
    # lifecycle fast-forward panel: 12 rows, cursor sweeps big-bang -> heat-death
    for j in range(12):
        yy = 110 + j * 62
        feat = j == k
        d.rectangle([1420, yy, 1860, yy + 54],
                    fill=(70, 20, 24) if feat else (16, 7, 9),
                    outline=(165, 105, 105) if feat else (130, 75, 78), width=2)
        text(img, (1440, yy + 10), f"{j + 1:02d} {UNIVERSE_STAGES[j][0]}",
             MONO_B, 18 if not feat else 20,
             (255, 215, 205) if feat else (170, 140, 140))
        text(img, (1440, yy + 34), UNIVERSE_STAGES[j][2], MONO, 13,
             (120, 95, 98) if not feat else (210, 150, 150))
    yc = 110 + u * (12 * 62)
    d.line([(1416, yc), (1864, yc)], fill=(255, 230, 210), width=4)
    d.line([(1416, yc + 8), (1864, yc + 8)], fill=(120, 50, 52), width=2)
    # output staircase: one line piles up per round (monotonic)
    out_lines = [("> love loop engaged (12x)", (255, 255, 255))]
    for r in range(k + 1):
        out_lines.append((f"> execute({r + 1:02d}) ... done", (255, 255, 255)))
        if r < 3:
            out_lines.append(({0: "ERR_UNRESOLVED_LOVE", 1: "ERR_WINDOW_EDGE",
                               2: "ERR_REPLY_OVERDUE"}[r], (180, 150, 150)))
    _log_window(img, out_lines[-4:], x=70, y=760, w=640, title="output")
    # stop button: nobody presses it
    rrect(d, [1060, 840, 1360, 980], 10, fill=(38, 12, 15), outline=(180, 100, 104), w=3)
    text(img, (1210, 892), "STOP", MONO_B, 38, (255, 255, 255), anchor="mm")
    text(img, (1210, 940), "input: none", MONO, 16, (170, 120, 124), anchor="mm")
    # counting cards (round 12 tail): six multilingual numbers, flip <=0.12s
    cards = [(159.2, "EIN", "de · eins"), (159.4, "DOS", "es · dos"),
             (159.79, "TROIS", "fr · trois"), (160.31, "NE", "no · en"),
             (160.66, "FEM", "sv · ett"), (161.16, "LIU", "zh · liu")]
    active = None
    for i, (at, word, cap) in enumerate(cards):
        if t >= at:
            active = i
    if active is not None and t < 161.88:      # cards yield at the last shout
        at, word, cap = cards[active]
        slide = min(1.0, (t - at) / 0.12)
        off = int(160 * (1 - slide))
        rrect(d, [480 + off, 250, 1440 + off, 720], 12, fill=(26, 8, 10),
              outline=(130, 48, 50), w=6)
        text(img, (960 + off, 410), word, MONO_B, 160, (255, 225, 205), anchor="mm")
        text(img, (960 + off, 580), cap, MONO, 24, (190, 150, 150), anchor="mm")
        if active > 0 and slide < 1:
            pw, pc = cards[active - 1][1], cards[active - 1][2]
            rrect(d, [480 + off - 1760, 250, 1440 + off - 1760, 720], 12,
                  fill=(26, 8, 10), outline=(130, 48, 50), w=6)
            text(img, (960 + off - 1760, 410), pw, MONO_B, 160, (150, 110, 110), anchor="mm")
    # her point side face: one frame after each of the last four blocks
    for syl_t in (CUES["last_syl1"][0], CUES["last_syl2"][0],
                  CUES["last_syl3"][0], CUES["last_syl4"][0]):
        if abs(t - syl_t) <= 1 / FPS / 2:
            char_mod.point_side_face(img, CFG, t, (900, 400), 110, fill=(245, 240, 235))
    # overflow at the end of round 12: ERR label (the section's only error-red)
    if k == 11 and t >= 162.3:
        rrect(d, [800, 660, 1360, 820], 10, fill=(16, 8, 10), outline=P["alert"], w=4)
        text(img, (1080, 715), "ERR_LOVE_OVERFLOW", MONO_B, 46, P["alert"], anchor="mm")
        text(img, (1080, 772), "loop budget exhausted", MONO, 20, (220, 190, 190), anchor="mm")
    _spectrum_strip(img, t)
    sub_mod.band(img, CFG, t)
    img = post_mod.post(img, t, CFG, vignette=0.22)
    if k == 11 and t >= 162.3:      # the screen tears in half, seam of red
        off = int(26 * min(1.0, (t - 162.3) / 0.29))
        left = img.crop((0, 0, W // 2, H))
        right = img.crop((W // 2, 0, W, H))
        torn = Image.new("RGB", (W, H), (30, 6, 8))
        torn.paste(left, (0, off))
        torn.paste(right, (W // 2, -off))
        ImageDraw.Draw(torn).line([(W // 2, 0), (W // 2, H)], fill=P["alert"], width=3)
        img = torn
    if zoom != 1.0:                 # rounds 5 and 9: whole machine magnified
        cw, ch = int(W / zoom), int(H / zoom)
        img = img.crop(((W - cw) // 2, (H - ch) // 2,
                        (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.LANCZOS)
    return img


# ---------------------------------------------------------------- S13 162.59-177.44
def render_s13(t):
    """The only execution: she reboots herself. White-hot burst is a <=11-frame
    transition (locked to L81 onset, not part of the brightness record); the
    section light then ratchets up: particle sea -> process tree -> keyword
    crescendo -> ERR_LOVE_OVERFLOW torn in half."""
    img = Image.new("RGB", (W, H), (30, 6, 8))
    _stripes(img)
    d = ImageDraw.Draw(img)
    BURST = 11 / FPS
    if t < 162.59 + BURST:
        u = (t - 162.59) / BURST
        v = 1.0 if u < 0.5 else (1 - u) * 2
        w = int(255 * v)
        img = Image.new("RGB", (W, H), (w, w, w))
        d = ImageDraw.Draw(img)
        d.ellipse([945, 455, 975, 485], fill=(255, 244, 210))
        return img
    # redshift afterglow: hue cools white-hot -> deep red, brightness holds
    a = min(1.0, (t - 163.05) / 8.0)
    for i in range(10):
        rr = 70 + i * 52
        col = mixc3((255, 230, 210), (120, 30, 28), a)
        circle(d, (960, 470), rr, col, 3)
    # universe clock: reset at the burst, then counts the reboot
    el = t - 162.59
    mm, ss = int(el // 60), el % 60
    text(img, (1840, 60), f"clock: {mm:02d}:{ss:05.2f}", MONO_B, 28, (255, 245, 235),
         anchor="rm")
    # particle sea rushes out (L82, word onset 164.32, one-way)
    if t >= 164.32:
        age = t - 164.32
        rr = 8 + age * 240
        r5 = prng_mod.prng(74, 0)
        col = mixc3((255, 235, 215), (230, 80, 70), min(1.0, age / 6))
        for i in range(300):
            ang = r5.uniform(0, 2 * math.pi)
            x = 960 + rr * math.cos(ang)
            y = 470 + rr * math.sin(ang) * 0.92
            d.rectangle([x, y, x + 4, y + 4], fill=col)
    # process tree appears (L83); the unique process = her lights at L84
    if t >= 166.18:
        r6 = prng_mod.prng(75, 0)
        nodes = [(960, 170)]
        for i in range(26):
            parent = nodes[r6.randrange(len(nodes))]
            px, py = parent
            nodes.append((px + r6.uniform(-180, 180), py + r6.uniform(70, 110)))
            d.line([parent, nodes[-1]], fill=(150, 155, 165), width=2)
            d.ellipse([nodes[-1][0] - 4, nodes[-1][1] - 4,
                       nodes[-1][0] + 4, nodes[-1][1] + 4], fill=(170, 175, 185))
        text(img, (960, 140), "init", MONO_B, 20, (200, 205, 215), anchor="mm")
        if t >= 167.94:
            d.ellipse([946, 156, 974, 184], fill=P["gold"])
            text(img, (960, 236), "love (the only process)", MONO_B, 22,
                 (255, 235, 190), anchor="mm")
    # keyword crescendo: one word, each time bigger (hardcoded rule)
    kws = [(169.1, "execution", 1.0), (172.81, "execution", 1.12),
           (174.57, "trapped", 1.26), (175.52, "trapped", 1.42)]
    shown = []
    for at, word, scale in kws:
        if t >= at:
            shown.append((word, scale))
    if shown:
        # keyword light-step: a persistent warm glow, one step per keyword,
        # locked to the keyword onset (1-2 frame transition, then held).
        # alpha rule: 0.05 + 0.06*level -> the brightness staircase never falls.
        level = len(shown) - 1
        fade = min(1.0, (t - kws[level][0]) / (2 / FPS))
        alpha = int((0.05 + 0.06 * level) * 255 * fade)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([320, 110, 1600, 830],
                                    fill=(255, 225, 200, alpha))
        img.paste(lay, (0, 0), lay)
        # earlier words persist as ghosts (the light ratchet never drops)
        for i, (word, scale) in enumerate(shown[:-1]):
            text(img, (960, 190 + i * 52), word, MONO_B, int(74 * scale),
                 (150, 92, 88), anchor="mm")
        word, scale = shown[-1]
        text(img, (960, 360), word, MONO_B, int(92 * scale), (242, 235, 225), anchor="mm")
        text(img, (960, 432), "the only instruction", MONO, 22, (210, 170, 170),
             anchor="mm")
    # ERR_LOVE_OVERFLOW torn in half (L88)
    if t >= 175.01:
        gap = 6 + 26 * min(1.0, (t - 175.01) / 1.5)
        f = font(MONO_B, 58)
        total = f.getlength("ERR_LOVE_OVERFLOW")
        x0 = 960 - total / 2
        d.text((x0, 600), "ERR_LOVE_OVERF", font=f, fill=P["alert"])
        d.text((x0 + f.getlength("ERR_LOVE_OVERF") + gap, 600), "LOW", font=f, fill=P["alert"])
        d.line([(960 - gap / 2, 586), (960 + gap / 2, 690)], fill=(255, 120, 100), width=3)
        text(img, (960, 700), "heartbuffer: split", MONO, 20, (220, 170, 170), anchor="mm")
    # her star-map core re-condenses: the reboot is her (data form)
    cr = 10 + 42 * min(1.0, (t - 162.59) / 14.85)
    d.ellipse([960 - cr, 470 - cr, 960 + cr, 470 + cr], fill=(255, 244, 210))
    d.ellipse([960 - cr - 12, 470 - cr - 12, 960 + cr + 12, 470 + cr + 12],
              outline=(255, 230, 190), width=3)
    # reboot log (word onsets)
    log = [("reboot: love", (255, 255, 255))]
    for at, s in ((164.32, "sea: released"), (166.18, "tree: spawned"),
                  (167.94, "proc: love (only)"), (169.68, "keyword: rising"),
                  (171.86, "screen: filled"), (173.49, "afterglow: cooling"),
                  (175.01, "overflow: split")):
        if t >= at:
            log.append((s, (255, 255, 255)))
    _log_window(img, log[-4:], x=40, y=760, w=620, title="reboot.log")
    _spectrum_strip(img, t)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.22)


# ---------------------------------------------------------------- S14 @192.3
def render_s14(t):
    """Love algebra: the desk writes her source code; when the formula is
    complete the window universe merges with it (mode shift); the heart is
    traced point by point and closes on the downbeat; golden light only rises
    to the film's single brightest frame, held still 190.5-192.94."""
    img = Image.new("RGB", (W, H), (13, 14, 20))
    # desk -> data-space fusion: star field + grid behind (the universe window)
    d = ImageDraw.Draw(img)
    rng = prng_mod.prng(5, 192.3)           # fixed stars = the approved peak frame
    merge = smoothstep((t - 184.6) / 0.5)   # the moment the formula completes
    sk = 0.45 + 0.55 * merge                # universe merges with the formula
    for _ in range(320):
        x, y = rng.uniform(0, W), rng.uniform(0, 940)
        d.rectangle([x, y, x + 1.5, y + 1.5],
                    fill=(int(120 * sk), int(128 * sk), int(152 * sk))
                    if rng.random() < 0.2 else
                    (int(82 * sk), int(88 * sk), int(106 * sk)))
    for y in range(80, 940, 96):
        d.line([(0, y), (W, y)], fill=(24, 28, 40), width=1)
    # the board (left): the algebraic expression of love, written in stages
    board_u = smoothstep((t - 177.44) / 0.6)
    if board_u > 0.02:
        rrect(d, [70, 90, 1050, 820], 12, fill=(17, 18, 26), outline=(58, 64, 82), w=1)
        for yy in range(150, 800, 34):
            d.line([(92, yy), (1030, yy)], fill=(26, 28, 38), width=1)
    text(img, (100, 120), "THE ALGEBRAIC EXPRESSION OF LOVE", MONO_B, 24,
         P["gold"] if t >= 179.2 else (120, 124, 138))
    if t >= 179.2:                          # L90: first formula line prints
        print_u = min(1.0, (t - 179.2) / 0.5)
        print_s = "(you + me)²"
        text(img, (100, 190), print_s[: max(1, int(len(print_s) * print_u))],
             SERIF, 64, P["fg"])
    if t >= 181.02:                         # L91/L92: Q and A fall in
        text(img, (100, 370), "Q: what is love?", MONO, 28, (150, 158, 176))
    if t >= 182.75:
        text(img, (100, 430), "A: you · me, to infinity", MONO, 28, P["cyan"])
    if t >= 184.6:                          # L93: the expansion, fully written
        exp_u = min(1.0, (t - 184.6) / 0.45)
        exp_s = "= you² + 2·you·me + me²"
        text(img, (100, 280), exp_s[: max(4, int(len(exp_s) * exp_u))],
             SERIF, 58, P["fg"])
        if exp_u >= 1:
            d.rectangle([376, 274, 620, 314], outline=P["gold"], width=3)
    # LOVE stamps by syllable: lo / o / ove, each with a <=6-frame impact
    love_syl = [184.21, 184.51, 184.81]      # lo / o / ove -> L / O / VE
    love_chunks = ["L", "O", "VE"]
    love_offsets = [0, 1, 2]
    lf = font(MONO_B, 128)
    for i, at in enumerate(love_syl):
        if t >= at:
            imp = 1.0 if t >= 187.65 else max(0.65, pulse(t, at, 0.2))
            col = (int(232 * min(1.0, 0.75 + 0.25 * imp)),
                   int(199 * min(1.0, 0.75 + 0.25 * imp)), int(107 * imp))
            text(img, (100 + lf.getlength("LOVE"[:love_offsets[i]]), 560),
                 love_chunks[i], MONO_B, 128, col)
    if t < 184.21:                          # before the stamps: one quiet line
        text(img, (100, 560), "love := ?", MONO, 28, (110, 116, 132))
    # a small proof block with syntax colours (density on the desk)
    code_lines = [("def love(me, you):", P["syn_purple"]),
                  ("    return solve(me, you)", P["fg"]),
                  ("love := trapped", P["syn_amber"]),
                  ("# the universe compiles", P["syn_green"])]
    for i, (s, col) in enumerate(code_lines):
        text(img, (100, 660 + i * 30), s, MONO, 21, col)
    # the heart stage: flat light disc (print style), halo, rays, curve
    hx, hy, hr = 1450, 470, 300
    heart_p = smoothstep((t - 188.29) / 0.26) if t >= 188.29 else 0.0
    rays_on = smoothstep((t - 188.55) / 1.45)   # golden light ratchet (only rises)
    int_gain = 0.0 if heart_p <= 0 else 0.5 + 0.5 * smoothstep((t - 188.29) / 3.0)
    # the heart INTERIOR must glow: nested gold discs clipped to the heart
    # boundary itself, so the light lives inside her written world
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    heart_pts = formula_mod.heart_points(hx, hy, hr - 6, n=240)
    md.polygon(heart_pts + [heart_pts[0]], fill=255)
    interior = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    idraw = ImageDraw.Draw(interior)
    for k, (rr, al) in enumerate([(0.99, 220), (0.72, 120), (0.46, 130), (0.24, 140)]):
        idraw.ellipse([hx - hr * rr, hy - hr * rr * 0.86, hx + hr * rr, hy + hr * rr * 0.86],
                      fill=P["gold"] + (int(al * int_gain),))
    interior.putalpha(mask)
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)          # the old draw object referenced the RGB copy
    img.alpha_composite(interior)
    solid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(solid).polygon(heart_pts + [heart_pts[0]],
                                  fill=P["gold"] + (int(125 * int_gain),))
    img.alpha_composite(solid)        # the interior is flooded with gold light
    for k, (rr, al) in enumerate([(0.72, 24), (0.50, 36)]):
        disc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(disc)
        dd.ellipse([hx - hr * rr, hy - hr * rr, hx + hr * rr, hy + hr * rr],
                   fill=P["gold"] + (int(al * int_gain),))
        img.paste(disc, (0, 0), disc)
    for k in range(36):
        if k / 36 > rays_on:
            continue
        a = 2 * math.pi * k / 36
        line(d, (hx + hr * 0.36 * math.cos(a), hy + hr * 0.36 * math.sin(a)),
             (hx + (hr + 210) * math.cos(a), hy + (hr + 210) * math.sin(a)),
             P["gold"], 2 if k % 3 else 3)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([hx - hr - 46, hy - hr - 46, hx + hr + 46, hy + hr + 46],
               outline=P["gold"] + (int(90 * int_gain),), width=10)
    img.alpha_composite(halo)
    # the algebraic heart: double stroke (glow under-line + bright line)
    if heart_p > 0:
        formula_mod.draw_heart(img, hx, hy, hr, P["gold"], w=10, closed=heart_p)
    glow_curve = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_curve)
    curve_full = formula_mod.heart_points(hx, hy, hr, n=240)
    nseg = max(2, int(len(curve_full) * heart_p)) if heart_p > 0 else 0
    if nseg:
        gd.line(curve_full[:nseg], fill=P["gold"] + (int(80 * int_gain),), width=20)
    img.alpha_composite(glow_curve)
    if heart_p > 0:
        formula_mod.draw_heart(img, hx, hy, hr, (255, 226, 160), w=4, closed=heart_p)
    # she stands inside the boundary: her point side-face (data form, starry)
    # contrast fix: dim the gold under the face to <=45% before the white dots
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark)
    dd.ellipse([hx - 92, hy + 4 - 150, hx + 92, hy + 4 + 150], fill=(0, 0, 0, 190))
    from PIL import ImageChops
    dark.putalpha(ImageChops.multiply(dark.getchannel("A"), mask))
    img.alpha_composite(dark)
    face_u = smoothstep((t - 189.58) / 0.5) if t >= 189.58 else 0.0
    if face_u > 0:
        ft = 192.3 if t >= 190.5 else t     # frozen during the held peak
        char_mod.point_side_face(img, CFG, ft, (hx, hy + 4), 140, align=face_u,
                                 fill=(255, 255, 255), n=1600, ds=2.0)
    # you are free: the cursor has left along the tangent, starting ON the
    # heart curve and heading outward (cyan-gold solid start, white dashed
    # trace, bright arrowhead) - the whole path stays inside the frame.
    tpts = formula_mod.heart_points(hx, hy, hr - 6, n=240)
    i0 = 40
    px, py = tpts[i0]
    dx, dy = tpts[i0 + 3][0] - tpts[i0 - 3][0], tpts[i0 + 3][1] - tpts[i0 - 3][1]
    Ln = math.hypot(dx, dy)
    dx, dy = dx / Ln, dy / Ln
    if dx < 0:                          # tangent must run outward, not inward
        dx, dy = -dx, -dy
    if heart_p >= 1:                    # the trace stays after the cursor left
        cu = 1.0 if t >= 189.58 else smoothstep((t - 188.29) / 1.29)
        if cu > 0:
            d.line([(px, py), (px + dx * 90, py + dy * 90)], fill=P["cyan"], width=4)
        nk = int(cu * 9)
        for k in range(nk):
            bx = px + dx * (96 + k * 38)
            by = py + dy * (96 + k * 38)
            d.rectangle([bx, by, bx + 24, by + 6], fill=(240, 243, 250))
        ax = px + dx * (96 + nk * 38 + 26)
        ay = py + dy * (96 + nk * 38 + 26)
        d.polygon([(ax, ay), (ax + 20, ay + 9), (ax + 4, ay + 18)], fill=(255, 255, 255))
    _log_window(img, [("love := trapped", P["gold"]),
                      ("you are free", P["fg"])], x=1100, y=60, w=700)
    _spectrum_strip(img, t if t < 190.5 else 192.3)
    sub_mod.band(img, CFG, t)
    img = img.convert("RGB")
    img = post_mod.post(img, t, CFG, vignette=0.16)
    # brightest frame of the film: one extra exposure step, ratcheting up
    peak = 1.0 if t >= 190.5 else 0.72 + 0.28 * smoothstep((t - 188.55) / 1.95)
    img = Image.eval(img, lambda v: min(255, int(v * (0.90 + 0.20 * peak))))
    return img


# ---------------------------------------------------------------- S15 192.94-209.87
def render_s15(t):
    """The final EXECUTION: heart forms with h(t), the command card waits,
    the four blocks fill on their syllables; at the chime (207.873) three
    cyan/gold heartbeats + her last gaze (one-way zoom, then still)."""
    img = Image.new("RGB", (W, H), (8, 9, 12))
    _stripes(img)
    d = ImageDraw.Draw(img)
    chime = CUES["chime"][0]                       # 207.873 (measured)
    # spectrum decays to silence
    for i in range(96):
        amp = (0.15 + 0.85 * abs(math.sin(i / 9.0 + t * 1.7))) * \
            max(0.15, 1.0 - max(0.0, (t - 204.5) / 3.4))
        h = int(8 + 30 * amp)
        d.rectangle([52 + i * 19, 1040 - h, 62 + i * 19, 1040],
                    fill=P["cyan"] if i % 5 else P["gold"])
    # the heart forms with h(t): one beat step per beat, one pulse per beat
    shape = smoothstep((t - 193.5) / 2.5)
    beat_phase = ((t - BEAT0) / BEAT_LEN) % 1.0
    pulse_b = math.exp(-beat_phase / 0.18) if t >= 193.5 and t < 204.5 else 0.0
    rr = 150 + 90 * shape + 12 * pulse_b
    hx, hy = 960, 430
    pts = formula_mod.heart_points(hx, hy, rr, n=240)
    d.line(pts + [pts[0]], fill=(190, 180, 130), width=7)
    d.line(pts + [pts[0]], fill=(232, 199, 107), width=2)
    # ECG locked to the beat, fading with the spectrum
    ecg_y = 760
    for i in range(220):
        ph = ((t - BEAT0 + i * 0.012) / BEAT_LEN) % 1.0
        spike = max(0.0, 1 - abs(ph - 0.0) / 0.035)
        y = ecg_y - 24 * spike * max(0.2, 1.0 - max(0.0, (t - 204.5) / 3.4))
        d.line([(240 + i * 6.5, y), (240 + i * 6.5 + 3, y)],
               fill=P["cyan"] if spike > 0.4 else (60, 72, 90))
    # command card, centre; the prompt blinks before the final word, then dies
    rrect(d, [560, 170, 1360, 300], 12, fill=(12, 13, 18), outline=(80, 90, 110), w=2)
    if t < 205.37:
        show_prompt = int(t * 2.0) % 2 == 0
    else:
        show_prompt = False
    text(img, (600, 218), (">" if show_prompt else " "), MONO_B, 36, (255, 255, 255))
    text(img, (656, 218), "execute me", MONO_B, 36, (240, 242, 248))
    # the final EXECUTION: four blocks fill on their syllables
    syls = [CUES["l97_onset"][0], CUES["l97_syl2"][0],
            CUES["l97_syl3"][0], CUES["l97_syl4"][0]]
    for i, (at, ch) in enumerate(zip(syls, "EXEC")):
        if t < at:
            continue
        x = 720 + i * 130
        d.rectangle([x, 360, x + 100, 470], fill=(34, 30, 18),
                    outline=(232, 199, 107), width=3)
        text(img, (x + 50, 415), ch, MONO_B, 58, (250, 244, 220), anchor="mm")
    text(img, (960, 530), "the final word", MONO, 22, (150, 158, 176), anchor="mm")
    gaze = smoothstep((t - chime) / 0.4) if t >= chime else 0.0
    char_mod.portrait_window(img, CFG, t, "starry", (60, 60, 520, 760), "her")
    if gaze > 0:
        gw = int(900 + 140 * gaze)
        gx = 960 - gw // 2
        char_mod.portrait_window(img, CFG, t, "starry", (gx, 80, gx + gw, 80 + int(gw * 0.78)),
                                 "her · the last gaze")
    # at the chime: three cyan/gold heartbeats flash ON TOP of her last gaze
    beats = [chime, chime + 0.5, chime + 1.0]
    for i, at in enumerate(beats):
        k = pulse(t, at, 0.16)
        if k > 0.02:
            col = P["cyan"] if i % 2 == 0 else P["gold"]
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            r1, r2 = int(rr * k), int(rr * 0.72 * k)
            ld.ellipse([960 - r1, 430 - r1, 960 + r1, 430 + r1],
                       outline=col + (int(190 * k),), width=18)
            ld.ellipse([960 - r2, 430 - r2, 960 + r2, 430 + r2],
                       outline=(255, 255, 255, int(160 * k)), width=12)
            ld.ellipse([960 - 58, 430 - 58, 960 + 58, 430 + 58],
                       fill=col + (int(120 * k),))
            img.paste(lay, (0, 0), lay)
    sub_mod.band(img, CFG, t)
    return post_mod.post(img, t, CFG, vignette=0.18)


# ---------------------------------------------------------------- S16 209.87-211.9
def render_s16(t):
    """Shutdown: the world collapses into one heart; execution complete;
    CRT power-off; her last shy glance fades; the original closing line."""
    img = Image.new("RGB", (W, H), (2, 2, 3))
    d = ImageDraw.Draw(img)
    # black field, then the heart lights and beats three times (decaying)
    hb = 0.0
    if t >= 210.2:
        hbeats = [210.2, 210.75, 211.3]
        amp = 1.0
        k = 0.0
        for i, at in enumerate(hbeats):
            kk = pulse(t, at, 0.18) * (1.0 - 0.25 * i)
            k = max(k, kk)
        rr = 96 + 34 * k
        hb = 0.55 + 0.45 * k
        pts = formula_mod.heart_points(960, 400, rr, n=240)
        d.polygon(pts + [pts[0]], fill=(int(90 * hb), int(72 * hb), int(45 * hb)))
        d.line(pts + [pts[0]], fill=(220, 180, 110), width=6)
        d.line(pts + [pts[0]], fill=(232, 199, 107), width=2)
    # the world collapses into that heart: only the background is squeezed
    coll = smoothstep((t - 210.9) / 0.9)
    if coll > 0:
        bar = int(H * coll)
        img = img.crop((0, (H - bar) // 2, W, (H + bar) // 2)).resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(img)
        if hb > 0:      # the heart itself stays: the world's last shape
            pts2 = formula_mod.heart_points(960, 400, 96 + 34 * hb, n=240)
            d.polygon(pts2 + [pts2[0]], fill=(int(90 * hb), int(72 * hb), int(45 * hb)))
            d.line(pts2 + [pts2[0]], fill=(220, 180, 110), width=6)
            d.line(pts2 + [pts2[0]], fill=(232, 199, 107), width=2)
    # execution complete line, typed after the flash
    if t >= CUES["exit_line"][0]:
        n = min(32, int((t - CUES["exit_line"][0]) / 0.05))
        s = "execution complete 100% -> exit code 0"
        text(img, (960, 600), s[:n], MONO_B, 28, (230, 234, 242), anchor="mm")
    # memory reclaim: hex stream scrolling at the bottom
    if t >= 210.3:
        rng = prng_mod.prng(88, t)
        for i in range(64):
            x = 30 + i * 30
            y = 850 + ((i * 37 + int(t * 60)) % 140)
            d.text((x, y), rng.choice("0123456789ABCDEF"), font=font(MONO, 18),
                   fill=(95, 110, 140))
    # power-off scanline (one-way)
    if t >= 211.0:
        sy = int(120 + (t - 211.0) * 900)
        if sy < 1080:
            d.line([(0, sy), (W, sy)], fill=(80, 92, 120), width=2)
    # her last glance: shy, fading with the process
    fade = 1.0 - smoothstep((t - 210.6) / 1.1)
    if fade > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        char_mod.portrait_window(lay, CFG, t, "shy", (1320, 320, 1780, 900), "her")
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * fade)))
        img.paste(lay, (0, 0), lay)
    # the original closing line fades in at the end (no subtitle band)
    if t >= 211.35:
        a = min(1.0, (t - 211.35) / 0.45)
        text(img, (960, 240), "exit 0 · world executed · heart remains", MONO_B, 34,
             (int(180 * a),) * 3, anchor="mm")
    # leftover data particles (the film's last light, decaying one-way)
    if t >= 210.5:
        r2 = prng_mod.prng(89, 0)
        decay = max(0.15, 1.0 - (t - 210.5) / 1.4)
        for i in range(220):
            x = r2.uniform(80, 1840)
            y = r2.uniform(120, 900)
            d.rectangle([x, y, x + 2, y + 2],
                        fill=(int(180 * decay), int(190 * decay), int(205 * decay)))
    _spectrum_strip(img, t if t < 211.0 else 211.0)
    _empty_band(img)
    return post_mod.post(img, t, CFG, vignette=0.1)


# ---------------------------------------------------------------- dispatch
def frame(t: float) -> Image.Image:
    t = float(t)
    # batch A sections with motivated transitions at the cut boundaries
    if t < 15.9:
        return render_s01(t)
    if 15.9 <= t < 16.35:          # S01 -> S02 reflow (character particles)
        u = (t - 15.9) / 0.45
        a, b = render_s01(t), render_s02(t)
        out = Image.blend(a, b, smoothstep(u))
        d = ImageDraw.Draw(out)
        rng = prng_mod.prng(16, t)
        f = font(MONO_B, 18)
        for k in range(70):
            x = rng.uniform(200, 1720)
            y = lerp(120 + rng.random() * 300, 480, u)
            d.text((x, y), rng.choice("01!<>#%&"), font=f,
                   fill=(79, 214, 232) if u < 0.5 else (120, 150, 200))
        return out
    if t < 29.57:
        return render_s02(t)
    if 29.57 <= t < 30.1:           # S02 -> S03 zoom (object match: grid -> axis)
        u = smoothstep((t - 29.57) / 0.53)
        a, b = render_s02(t), render_s03(t)
        out = Image.blend(a, b, u)
        d = ImageDraw.Draw(out)
        d.rectangle([0, 0, W, H], outline=(79, 214, 232), width=max(1, int(6 * (1 - u))))
        return out
    if t < 44.2:
        return render_s03(t)
    if 44.2 <= t < 44.75:           # S03 -> S04 pan (time runs left)
        u = smoothstep((t - 44.2) / 0.55)
        a, b = render_s03(t), render_s04(t)
        out = Image.new("RGB", (W, H), (6, 10, 26))
        off = int(W * u)
        out.paste(b.crop((0, 0, W - off, H)), (off, 0))
        out.paste(a.crop((W - off, 0, W, H)), (0, 0))
        return out
    if t < 59.06:
        return render_s04(t)
    if 59.06 <= t < 59.5:            # S04 -> S05 zoom (into the machine)
        u = smoothstep((t - 59.06) / 0.44)
        a, b = render_s04(t), render_s05(t)
        out = Image.blend(a, b, u)
        d = ImageDraw.Draw(out)
        d.rectangle([0, 0, W, H], outline=(79, 214, 232), width=max(1, int(5 * (1 - u))))
        return out
    if t < 73.93:
        return render_s05(t)
    if t < 88.54:                    # hard cut into the morph cards
        return render_s06(t)
    if 88.54 <= t < 89.0:            # winpop: card closes, settings panel pops
        u = smoothstep((t - 88.54) / 0.46)
        a, b = render_s06(t), render_s07(t)
        out = Image.blend(a, b, u)
        d = ImageDraw.Draw(out)
        d.rectangle([W / 2 * (1 - u), 0, W / 2 * (1 + u), H], fill=(20, 16, 10))
        return out
    if t < 103.52:
        return render_s07(t)
    if 103.52 <= t < 104.1:          # spin into resonance
        u = smoothstep((t - 103.52) / 0.58)
        a, b = render_s07(t), render_s08(t)
        out = Image.blend(a, b, u)
        return out
    if t < 110.41:
        return render_s08(t)
    if 110.41 <= t < 110.91:        # S08 -> S09 fade (resonance decays, world greys)
        u = smoothstep((t - 110.41) / 0.5)
        return Image.blend(render_s08(t), render_s09(t), u)
    if t < 118.24:
        return render_s09(t)
    if 118.24 <= t < 118.74:        # S09 -> S10 winpop (the shell pops back in)
        u = smoothstep((t - 118.24) / 0.5)
        a, b = render_s09(t), render_s10(t)
        w_, h_ = int(W * u / 2) + 1, int(H * u / 2) + 1
        rect = (W // 2 - w_, H // 2 - h_, W // 2 + w_, H // 2 + h_)
        out = a.copy()
        out.paste(b.crop(rect), rect[:2])
        ImageDraw.Draw(out).rectangle(rect, outline=(150, 158, 176), width=3)
        return out
    if t < 133.95:
        return render_s10(t)
    if 133.95 <= t < 134.75:        # S10 -> S11 slow push (camera sinks into collapse)
        u = smoothstep((t - 133.95) / 0.8)
        z = 1.0 + 0.12 * u
        s11 = render_s11(t)
        cw, ch = int(W / z), int(H / z)
        s11 = s11.crop(((W - cw) // 2, (H - ch) // 2,
                        (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.LANCZOS)
        out = Image.blend(render_s10(t), s11, u)
        # sinking into the collapse: a brief exposure dip, so the film's
        # brightness keeps its single peak at S14
        dip = 1.0 - 0.18 * math.sin(math.pi * u)
        return Image.eval(out, lambda v: min(255, int(v * dip)))
    if t < 147.95:                 # includes the singularity frame at 147.89
        return render_s11(t)
    if t < 162.59:                 # S12: hard cut into the execution loop
        k, _ = _s12_round(t)
        return render_s12(t, zoom=1.12 if k in (4, 8) else 1.0)
    if t < 177.45:                 # S13: hard cut into the only execution
        return render_s13(t)
    if t < 192.94:                 # S14; the peak frame is held still >=1.2s
        return render_s14(192.3) if t >= 191.74 else render_s14(t)
    if 192.94 <= t < 193.5:        # S14 -> S15: the formula dissolves
        u = smoothstep((t - 192.94) / 0.56)
        a, b = render_s14(192.3), render_s15(t)
        out = Image.blend(a, b, u)
        d = ImageDraw.Draw(out)
        rng = prng_mod.prng(17, t)
        f = font(MONO, 20)
        for k in range(90):
            x = rng.uniform(80, 1040)
            y = rng.uniform(120, 800)
            d.text((x, y), rng.choice("01!<>#%&()+=·xylove"),
                   font=f, fill=(int(120 * (1 - u)),) * 3)
        return out
    if t < 209.87:                 # S15
        return render_s15(t)
    if abs(t - CUES["s16_flash"][0]) < 1 / FPS / 2:   # the single white flash
        return Image.new("RGB", (W, H), (255, 255, 255))
    if t < 211.9:
        return render_s16(t)
    return render_s16(211.9)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="comma list of song seconds")
    ap.add_argument("--video", help="render t0,t1,out.mp4 (24fps segment)")
    ap.add_argument("--master", help="render the full film to lossless ffv1 mkv")
    ap.add_argument("--4k", dest="four_k", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "out" / "stills"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.video or a.master:
        import subprocess
        if a.video:
            t0, t1, outv = a.video.split(",")
            t0, t1 = float(t0), float(t1)
            codec = ["-c:v", "libx264", "-preset", "veryfast", "-qp", "18"]
        else:
            t0, t1, outv = 0.0, float(CFG["song"]["duration"]), a.master
            codec = ["-c:v", "ffv1", "-level", "3"]
        ff = "D:/aicode/.toolchain/ffmpeg.exe"
        proc = subprocess.Popen(
            [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-", *codec, str(Path(outv))],
            stdin=subprocess.PIPE)
        n = 0
        tt = t0
        while tt < t1:
            proc.stdin.write(frame(tt).tobytes())
            tt += 1 / FPS
            n += 1
        proc.stdin.close()
        proc.wait()
        print(f"video: {n} frames -> {outv} (rc={proc.returncode})")
        return
    times = [float(x) for x in (a.stills or "").split(",") if x]
    for t in times:
        img = frame(t)
        name = out / f"still_{t:07.3f}.png"
        img.save(name)
        print(f"stills: {t:.3f}s -> {name}")
        if a.four_k:
            big = img.resize((W * 2, H * 2), Image.NEAREST)
            name4 = out / f"still_{t:07.3f}_4k.png"
            big.save(name4)
            print(f"stills: {t:.3f}s -> {name4}")


if __name__ == "__main__":
    main()
