"""Render the demo animations for the README from the PC simulators (no hardware needed).

    python sim/make_gifs.py            -> docs/*.gif and docs/*.png

  docs/merge.gif        both boards: Earths reach for each other, tear apart, become the black hole, then let go
  docs/earth.gif        one board: the pixel Earth doing a full turn (seamless loop)
  docs/zoom.gif         both boards: the whole 7.5-minute zoom-out cycle in about 20 s
  docs/zoom-stages.png  twelve moments of the zoom, one strip
  docs/hero.png         the merge mid-way, as a still

The simulators are pixel-for-pixel ports of the sketches, so these look like the real screens.
Stills are rendered at 3x (one screen pixel = a 3x3 block), the merge GIF at 2x, with the bezel gap between the boards.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from tqt_sim import *
import preview_sharedhole as sh
import preview_zoom as zm

DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)
SCALE = 3


def save_gif(frames, name, fps, loop=0):
    path = os.path.join(DOCS, name)
    # one shared palette for every frame (no flicker), built from frames sampled across the whole
    # animation so it holds the Earth's blues and greens AND the disk's oranges
    sample = frames[::max(1, len(frames) // 16)]
    w, h = frames[0].size
    montage = Image.new("RGB", (w, h * len(sample)))
    for i, f in enumerate(sample):
        montage.paste(f, (0, i * h))
    pal = montage.convert("P", palette=Image.ADAPTIVE, colors=255)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=loop,
              optimize=True, disposal=1)
    print("wrote %s  (%d frames, %dx%d, %.1f s, %.0f KB)" %
          (name, len(frames), frames[0].width, frames[0].height, len(frames) / fps, os.path.getsize(path) / 1024))


# ------------------------------------------------------------------ the merge
def merge_frames(fps=20):
    """P over time, like the real thing: apart, reach, slow merge (FORM_SECONDS), hold, let go."""
    dots, stars = sh.build_scene()
    glowL, glowR = sh.build_glow(1.0), sh.build_glow(-1.0)
    FORM = 4.0
    timeline = [  # (seconds, target P)
        (0.0, 0.0), (1.5, 0.0), (3.0, sh.MERGE_START),           # reach
        (3.0 + FORM, 1.0), (3.0 + FORM + 2.5, 1.0),                # merge, hold
        (3.0 + FORM + 4.5, 0.0), (3.0 + FORM + 6.0, 0.0),          # let go, settle
    ]
    total = timeline[-1][0]
    frames, spinExtra, prev = [], 0.0, 0.0
    n = int(total * fps)
    for i in range(n):
        t = i / fps
        k = 0
        while k < len(timeline) - 2 and t >= timeline[k + 1][0]:
            k += 1
        (t0, p0), (t1, p1) = timeline[k], timeline[k + 1]
        P = p0 + (p1 - p0) * clampf((t - t0) / (t1 - t0), 0, 1)
        spinExtra = math.fmod(spinExtra + (1.0 / fps) * 0.8 * P, TWO_PI)
        L, Rb = FB(), FB()
        sh.render(L, dots, stars, glowL, P, 1.0, t, 7.0 + t, spinExtra)
        sh.render(Rb, dots, stars, glowR, P, -1.0, t, 7.0 + t, spinExtra)
        frames.append(compose_pair(L, Rb, int(sh.GAP_PX), 2))     # 2x keeps the file under ~3 MB
        if abs(P - 0.72) < abs(prev - 0.72) and P > prev:
            compose_pair(L, Rb, int(sh.GAP_PX), SCALE).save(os.path.join(DOCS, "hero.png"))
        prev = P
    return frames


# ------------------------------------------------------------------ the Earth
def earth_frames(n=72):
    """One full turn of the globe on one board (SPIN_PERIOD_S seconds), seamless."""
    dots, stars = sh.build_scene()
    glow = sh.build_glow(1.0)
    frames = []
    for i in range(n):
        ts = sh.SPIN_PERIOD_S * i / n
        fb = FB()
        sh.render(fb, dots, stars, glow, 0.0, 1.0, ts, ts, 0.0)
        img = fb.image()
        frames.append(img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST))
    return frames


# ------------------------------------------------------------------ the zoom
def zoom_frames(seconds=24, fps=15):
    dots, stars, galaxy, near = zm.build_scene()
    em = zm.Emitter(dots, galaxy, near)
    glowL, glowR = zm.build_glow(1.0), zm.build_glow(-1.0)
    frames = []
    n = seconds * fps
    for i in range(n):
        phase = i / n
        img, z = zm.pair(em, stars, glowL, glowR, 0.0, phase, tShared=phase * zm.ZOOM_MINUTES * 60.0)
        frames.append(img)
    return frames


def zoom_stages():
    dots, stars, galaxy, near = zm.build_scene()
    em = zm.Emitter(dots, galaxy, near)
    glowL, glowR = zm.build_glow(1.0), zm.build_glow(-1.0)
    pairs = []
    for ph in (0.01, 0.08, 0.14, 0.21, 0.29, 0.37, 0.45, 0.52, 0.60, 0.70, 0.82, 0.94):
        pairs.append(zm.pair(em, stars, glowL, glowR, 0.0, ph)[0])
    strip = compose_strip(pairs, per_row=3)
    strip.save(os.path.join(DOCS, "zoom-stages.png"))
    print("wrote zoom-stages.png", strip.size)


if __name__ == "__main__":
    save_gif(merge_frames(15), "merge.gif", 15)
    save_gif(earth_frames(), "earth.gif", 12)
    save_gif(zoom_frames(), "zoom.gif", 15)
    zoom_stages()
