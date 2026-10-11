"""Real formulas. The algebraic heart is traced by bisection on the implicit
equation itself - never drawn from a bitmap."""
from __future__ import annotations

import math

from PIL import ImageDraw

from data import facts


def heart_points(cx, cy, r, n=360):
    """Points of (x²+y²−1)³−x²y³=0, by ray bisection (y up)."""
    pts = []
    for i in range(n + 1):
        th = math.pi / 2 - 2 * math.pi * i / n
        c, s = math.cos(th), math.sin(th)
        q = c * c * s * s * s
        lo, hi = 0.0, 2.0
        for _ in range(48):
            mid = (lo + hi) / 2
            if (mid * mid - 1) ** 3 - mid ** 5 * q < 0:
                lo = mid
            else:
                hi = mid
        rr = lo
        pts.append((cx + math.cos(th) * rr * r, cy - math.sin(th) * rr * r))
    return pts


def draw_heart(img, cx, cy, r, outline, w=3, closed=1.0, n=360):
    pts = heart_points(cx, cy, r, n)
    k = int(len(pts) * closed)
    d = ImageDraw.Draw(img)
    seg = pts[: max(2, k)]
    if closed >= 1:
        d.line(seg + [seg[0]], fill=outline, width=w)
    else:
        d.line(seg, fill=outline, width=w)
