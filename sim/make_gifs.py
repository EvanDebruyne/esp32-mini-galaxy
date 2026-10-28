"""Render the demo animations for the README from the PC simulators (no hardware needed).

    python sim/make_gifs.py            -> docs/*.gif and docs/*.png

  docs/merge.gif        both boards: Earths reach for each other, tear apart, become the black hole, then let go
  docs/earth.gif        one board: the pixel Earth doing a full turn (seamless loop)
  docs/debug.gif        the same, with the BOOT-button debug overlay on
  docs/zoom.gif         one board: the whole 7.5-minute zoom-out cycle in about 30 s
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
import preview_earth as sh
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
FONT_DBG = {  # the sketch's 3x5 debug font: digits, '-', 'L', 'R'
    '0': (7,5,5,5,7), '1': (2,6,2,2,7), '2': (7,1,7,4,7), '3': (7,1,7,1,7), '4': (5,5,7,1,1),
    '5': (7,4,7,1,7), '6': (7,4,7,5,7), '7': (7,1,1,1,1), '8': (7,5,7,5,7), '9': (7,5,7,1,7),
    '-': (0,0,7,0,0), 'L': (4,4,4,4,7), 'R': (6,5,6,5,5),
}


def draw_text_dbg(fb, x, y, text, c, s):
    for ch in text:
        g = FONT_DBG.get(ch)
        if g:
            for row in range(5):
                for col in range(3):
                    if g[row] & (4 >> col):
                        fb.fill_rect(x + col * s, y + row * s, s, s, c)
        x += 4 * s


def draw_debug(fb, linked, rssi, fps, side, sceneP):
    """1:1 port of renderDebug() in MiniGalaxy_Earth.ino."""
    white, dim, tick = (255, 255, 255), (60, 60, 60), (255, 140, 0)
    draw_text_dbg(fb, 2, 2, "%d" % round(rssi) if linked else "---", white, 2)
    draw_text_dbg(fb, 2, 15, "%d" % round(fps), (0, 200, 255), 2)
    draw_text_dbg(fb, W - 8, 2, side, white, 2)
    fb.fill_rect(W - 14, 4, 4, 4, (0, 255, 0) if linked else (255, 0, 0))
    fb.fill_rect(2, H - 6, W - 4, 4, dim)
    fb.fill_rect(2, H - 6, int((W - 4) * sceneP), 4, white)
    fb.fill_rect(2 + int((W - 5) * sh.MERGE_START), H - 9, 1, 3, tick)
    fb.fill_rect(2 + int((W - 5) * sh.MERGE_FULL), H - 9, 1, 3, tick)


def merge_frames(fps=20, debug=False):
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
        if debug:
            # what the overlay would read: dBm from the scene P (apart = a bit below RSSI_FAR), jittery fps
            j = hash01(i * 7 + 3) * 2 - 1
            dbm = (sh.RSSI_FAR + P * (sh.RSSI_NEAR - sh.RSSI_FAR)) if p1 > 0 or P > 0 else sh.RSSI_FAR - 5
            fpsv = 36 - 6 * P + 2 * j
            draw_debug(L, True, dbm + j, fpsv, "L", P)
            draw_debug(Rb, True, dbm - j, fpsv + 1, "R", P)
        frames.append(compose_pair(L, Rb, int(sh.GAP_PX), 2))     # 2x keeps the file under ~3 MB
        if not debug and abs(P - 0.72) < abs(prev - 0.72) and P > prev:
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
        sh.render(fb, dots, stars, glow, 0.0, 1.0, ts, ts, 0.0, starWrap=1)   # stars loop with the turn
        img = fb.image()
        frames.append(img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST))
    return frames


# ------------------------------------------------------------------ the zoom
def zoom_frames(seconds=30, fps=15):
    dots, stars, galaxy, near = zm.build_scene()
    em = zm.Emitter(dots, galaxy, near)
    glowL, glowR = zm.build_glow(1.0), zm.build_glow(-1.0)
    frames = []
    n = seconds * fps
    for i in range(n):
        phase = i / n
        fb = zm.FB()
        z = zm.render(fb, em, stars, glowL, 0.0, 1.0, 3.0, phase * zm.ZOOM_MINUTES * 60.0, phase)
        zm.draw_scale_bar(fb, z["ppm"], z["env"])
        img = fb.image()
        frames.append(img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST))
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
    save_gif(merge_frames(15, debug=True), "debug.gif", 15)
    save_gif(earth_frames(), "earth.gif", 12)
    save_gif(zoom_frames(), "zoom.gif", 15)
    zoom_stages()
