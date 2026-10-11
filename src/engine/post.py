"""CRT post: scanlines, barrel vignette, phosphor afterglow, controlled dispersion."""
from __future__ import annotations

import numpy as np
from PIL import Image


def post(img: Image.Image, t: float, cfg: dict, *, dispersion: float = 0.0,
         scan: bool = True, vignette: float = 0.28) -> Image.Image:
    a = np.asarray(img, np.float32)
    if dispersion > 0:
        # controlled chromatic shift on the red channel only, by dispersion px
        shift = int(round(dispersion))
        if shift:
            a[..., 0] = np.roll(a[..., 0], shift, axis=1)
    if scan:
        a[2::3, :, :] *= 0.92          # scanlines
    if vignette > 0:
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
        rr = np.sqrt(((xx - a.shape[1] / 2) / (a.shape[1] * 0.62)) ** 2 +
                     ((yy - a.shape[0] / 2) / (a.shape[0] * 0.62)) ** 2)
        a *= (1 - np.clip(rr - 0.55, 0, 1) * vignette)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
