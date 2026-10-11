"""Vector-ish drawing helpers on a Pillow canvas (RGB)."""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def line(d, p0, p1, fill, w=2, dash=None):
    if dash:
        x0, y0, x1, y1 = *p0, *p1
        total = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(total / (dash[0] + dash[1])))
        for i in range(n + 1):
            s0 = i * (dash[0] + dash[1])
            s1 = min(s0 + dash[0], total)
            u0, u1 = s0 / total, s1 / total
            d.line([(x0 + (x1 - x0) * u0, y0 + (y1 - y0) * u0),
                    (x0 + (x1 - x0) * u1, y0 + (y1 - y0) * u1)], fill=fill, width=w)
        return
    d.line([p0, p1], fill=fill, width=w)


def circle(d, c, r, outline, w=2, a0=0, a1=360, n=96):
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    d.line(pts, fill=outline, width=w)


def rrect(d, box, radius=8, fill=None, outline=None, w=2):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=w)


def text(img, xy, s, font_path, size, fill, anchor="la", alpha=255):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, s, font=font(font_path, size), fill=fill + (alpha,), anchor=anchor)
    if img.mode == "RGBA":
        img.alpha_composite(layer)
    else:
        img.paste(layer, (0, 0), layer)


def glow(base, rect, radius=12, gain=0.35):
    """Bloom: blurred bright copy added back (flat, cheap)."""
    crop = base.crop(rect)
    blur = crop.filter(ImageFilter.GaussianBlur(radius))
    blur = blur.point(lambda v: int(v * gain))
    from PIL import ImageChops
    out = base.copy()
    out.paste(ImageChops.add(crop, blur), rect[:2])
    return out
