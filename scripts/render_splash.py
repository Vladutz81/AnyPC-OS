#!/usr/bin/env python3
"""Regenerate the boot splash images in session/plymouth/anypc/.

The PNGs are committed, so this only has to be run after changing the artwork.
SVG sources in session/plymouth/src/ are rendered with rsvg-convert. The soft
light behind the mark is computed here instead, with dithering, because a plain
gradient shows rings (banding) on 8-bit screens.

Needs: rsvg-convert (librsvg), Python 3 with Pillow and NumPy.
"""
import pathlib
import subprocess

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent / "session" / "plymouth"
OUT = ROOT / "anypc"


def render_svgs():
    for svg in sorted((ROOT / "src").glob("*.svg")):
        png = OUT / (svg.stem + ".png")
        subprocess.run(["rsvg-convert", "--format=png", "-o", str(png), str(svg)], check=True)
        print(png.relative_to(ROOT.parent.parent))


def render_glow(size=1200, seed=7):
    """Blue light: #2A62D6 in the middle fading to transparent #0D2C78.

    Stored at 1200 px; the theme shows it 1600 px wide on a 2160-pixel-high screen."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float64)
    c = (size - 1) / 2
    r = np.hypot(x - c, y - c) / (size / 2)              # 0 at centre, 1 at edge
    alpha = 0.5 * np.exp(-4.2 * r * r)
    edge = np.clip((1 - r) / 0.25, 0, 1)                 # reach zero before the edge
    alpha *= edge * edge * (3 - 2 * edge)
    inner = np.array([0x2A, 0x62, 0xD6], np.float64)
    outer = np.array([0x0D, 0x2C, 0x78], np.float64)
    mix = np.clip(r / 0.7, 0, 1)[..., None]
    rgb = inner * (1 - mix) + outer * mix
    rng = np.random.default_rng(seed)
    noise = rng.random((size, size, 4)) - rng.random((size, size, 4))  # triangular dither, ±1 LSB
    img = np.dstack([rgb, alpha * 255]) + noise
    img = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    png = OUT / "glow.png"
    Image.fromarray(img, "RGBA").save(png, optimize=True)
    print(png.relative_to(ROOT.parent.parent))


if __name__ == "__main__":
    render_svgs()
    render_glow()
