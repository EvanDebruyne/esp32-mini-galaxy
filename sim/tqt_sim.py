"""Tiny PC-side stand-in for the T-QT Pro framebuffer + the helper math the sketches use.

The sketches can't run on a PC (no host C++ compiler here), so the scene code is ported
1:1 into Python and drawn with the same integer plotting so the preview looks like the
real 128x128 panel. Run a preview script in this folder to get a PNG strip.
"""
import math
import numpy as np
from PIL import Image

W = H = 128
PI = math.pi
TWO_PI = 2 * math.pi
HALF_PI = math.pi / 2


def clampf(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def smoothstepf(a, b, x):
    t = clampf((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def roundf(x):
    return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)


def hash01(n):
    n &= 0xFFFFFFFF
    n = ((n ^ 61) ^ (n >> 16)) & 0xFFFFFFFF
    n = (n * 9) & 0xFFFFFFFF
    n ^= n >> 4
    n = (n * 0x27D4EB2D) & 0xFFFFFFFF
    n ^= n >> 15
    return (n & 0xFFFFFF) / 16777216.0


def hsv_to_rgb(h, s, v):
    h -= math.floor(h)
    hf = h * 6.0
    i = int(hf)
    f = hf - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    return [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]


def pack(r, g, b):
    """RGB565-quantised colour, like the sketch's pack()."""
    r = int(clampf(r, 0, 1) * 255) & 0xF8
    g = int(clampf(g, 0, 1) * 255) & 0xFC
    b = int(clampf(b, 0, 1) * 255) & 0xF8
    return (r, g, b)


class FB:
    def __init__(self):
        self.px = np.zeros((H, W, 3), dtype=np.uint8)

    def clear(self):
        self.px[:] = 0

    def plot(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            self.px[y, x] = c

    def fill_rect(self, x, y, w, h, c):
        x, y = int(x), int(y)
        for j in range(h):
            for i in range(w):
                self.plot(x + i, y + j, c)

    def fill_circle(self, cx, cy, rad, c):
        r = int(math.ceil(rad))
        r2 = rad * rad
        x0, y0 = int(math.floor(cx)), int(math.floor(cy))
        for y in range(-r, r + 1):
            yy = y0 + y
            if yy < 0 or yy >= H:
                continue
            for x in range(-r, r + 1):
                xx = x0 + x
                if xx < 0 or xx >= W:
                    continue
                dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
                if dx * dx + dy * dy <= r2:
                    self.px[yy, xx] = c

    def image(self):
        return Image.fromarray(self.px, "RGB")


def compose_pair(left, right, gap_px, scale=3, bezel=(28, 28, 28)):
    """Two boards side by side with `gap_px` of dark bezel between the active areas."""
    img = Image.new("RGB", (2 * W + gap_px, H), bezel)
    img.paste(left.image(), (0, 0))
    img.paste(right.image(), (W + gap_px, 0))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def compose_strip(pairs, pad=12, bg=(40, 40, 40), per_row=3):
    """Lay the pairs out left to right, wrapping after `per_row` of them."""
    rows = [pairs[i:i + per_row] for i in range(0, len(pairs), per_row)]
    w = max(sum(p.width for p in r) + pad * (len(r) + 1) for r in rows)
    rh = max(p.height for p in pairs)
    out = Image.new("RGB", (w, rh * len(rows) + pad * (len(rows) + 1)), bg)
    y = pad
    for r in rows:
        x = pad
        for p in r:
            out.paste(p, (x, y))
            x += p.width + pad
        y += rh + pad
    return out
