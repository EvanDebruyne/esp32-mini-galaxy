"""Preview of ProximitySpheres_SharedHole (as written by Opus) — 1:1 port of renderScene().

    python extras/sim/preview_sharedhole_v1.py            -> extras/previews/sharedhole-v1-preview.png
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sim"))
from tqt_sim import *

RSSI_FAR, RSSI_NEAR = -32.0, -20.0
MERGE_START, MERGE_FULL = 0.45, 0.90
GAP_PX, HOLE_RADIUS, DISK_TILT = 24.0, 44.0, 0.10
SPHERE_RADIUS, RINGS, NUM_STARS = 55.0, 44, 70
MAX_DOTS = 3200


class Dot:
    __slots__ = ("x", "y", "z", "hue", "rdn", "ang", "omega", "jitter")


def build_scene():
    dots, stars = [], []
    for r in range(RINGS):
        lat = PI * ((r + 0.5) / RINGS) - HALF_PI
        cl, sl = math.cos(lat), math.sin(lat)
        count = max(1, int(roundf(2.0 * RINGS * cl)))
        for k in range(count):
            if len(dots) >= MAX_DOTS:
                break
            n = len(dots)
            lon = TWO_PI * (k + 0.5 * (r & 1)) / count
            d = Dot()
            d.x, d.y, d.z = cl * math.cos(lon), sl, cl * math.sin(lon)
            d.hue = 0.42 * d.y + 0.25 * d.x + 0.12 * d.z
            u = hash01(n * 2 + 1)
            d.rdn = 1.20 + 2.30 * (u ** 1.35)
            d.ang = TWO_PI * hash01(n * 2 + 5)
            d.omega = 1.3 / (d.rdn * math.sqrt(d.rdn))
            d.jitter = (hash01(n * 2 + 7) - 0.5) * (0.05 + 0.04 * u)
            dots.append(d)
    for i in range(NUM_STARS):
        stars.append((hash01(i * 3 + 101) * W, hash01(i * 3 + 202) * H, 0.15 + 0.45 * hash01(i * 3 + 303)))
    return dots, stars


def disk_color(k):
    k = clampf(k, 0.0, 1.0)
    if k < 0.35:
        t = k / 0.35;            return 1.0, 1.0 - 0.10 * t, 1.0 - 0.25 * t
    elif k < 0.7:
        t = (k - 0.35) / 0.35;   return 1.0, 0.90 - 0.25 * t, 0.75 - 0.40 * t
    else:
        t = (k - 0.7) / 0.3;     return 1.0 - 0.15 * t, 0.65 - 0.25 * t, 0.35 - 0.20 * t


def hole_center_x(side):
    return W * 0.5 + side * (W * 0.5 + GAP_PX * 0.5)


def build_glow(side):
    hcx, hcy = hole_center_x(side), H * 0.5
    ct, st = math.cos(DISK_TILT), math.sin(DISK_TILT)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float64)
    dx, dy = xs + 0.5 - hcx, hcy - (ys + 0.5)
    ux, uy = dx * ct + dy * st, -dx * st + dy * ct
    r = np.sqrt(dx * dx + dy * dy)
    band = np.exp(-np.abs(uy) / (5.0 + 0.07 * np.abs(ux))) * np.exp(-np.abs(ux) / 150.0)
    ring = np.exp(-np.abs(r - HOLE_RADIUS * 1.22) / 10.0)
    haze = np.exp(-(r - HOLE_RADIUS) / 60.0)
    g = np.where(r > HOLE_RADIUS, 0.55 * band + 0.40 * ring + 0.25 * haze, 0.0)
    return np.clip(g, 0, 1)


def render(fb, dots, stars, glow, P, s, t, tShared, rotY, hueBase):
    sgn = 1.0 if s >= 0 else -1.0
    m = smoothstepf(MERGE_START, MERGE_FULL, P)
    reachAmt = clampf(P / MERGE_START, 0, 1) * (1.0 - m)

    if m > 0.01:
        g = glow * m * 0.42
        fb.px[..., 0] = (np.clip(g, 0, 1) * 255).astype(np.uint8) & 0xF8
        fb.px[..., 1] = (np.clip(g * 0.60, 0, 1) * 255).astype(np.uint8) & 0xFC
        fb.px[..., 2] = (np.clip(g * 0.30, 0, 1) * 255).astype(np.uint8) & 0xF8
    else:
        fb.clear()

    scx = W * 0.5 + s * 9.0 * reachAmt
    scy = H * 0.5
    R = SPHERE_RADIUS * (1.0 + 0.02 * math.sin(t * 1.7))
    hcx, hcy = hole_center_x(sgn), H * 0.5
    hR = HOLE_RADIUS * smoothstepf(0.0, 0.8, m)
    Rh = HOLE_RADIUS

    cR, sR = math.cos(rotY), math.sin(rotY)
    cT, sT = math.cos(0.42), math.sin(0.42)
    sE = math.sin(0.17)
    cD, sD = math.cos(DISK_TILT), math.sin(DISK_TILT)

    for i, (sx0, sy0, b) in enumerate(stars):
        dx, dy = sx0 - hcx, sy0 - hcy
        d2 = dx * dx + dy * dy + 1.0
        push = 1.0 + m * (hR * hR * 1.6) / d2
        tw = 0.75 + 0.25 * math.sin(t * 2.0 + i)
        v = b * tw * (0.5 + 0.3 * m)
        sx, sy = hcx + dx * push, hcy + dy * push
        rx, ry = sx - hcx, sy - hcy
        if m > 0.01 and rx * rx + ry * ry < hR * hR * 1.3:
            continue
        fb.plot(sx, sy, pack(v, v, v))

    for p in range(3):
        if p == 1:
            if m > 0.01:
                fb.fill_circle(hcx, hcy, hR * 1.04, pack(0.95 * m, 0.90 * m, 0.80 * m))
                fb.fill_circle(hcx, hcy, hR, (0, 0, 0))
            continue
        for d in dots:
            x1 = d.x * cR + d.z * sR
            z1 = -d.x * sR + d.z * cR
            sy = d.y * cT - z1 * sT
            sz = d.y * sT + z1 * cT
            sx = x1
            dp = sx * s
            reach = dp ** 3 if dp > 0 else 0.0
            back = -dp if dp < 0 else 0.0
            r = 1.0 + reachAmt * (0.9 * reach - 0.10 * back)
            pinch = 1.0 - 0.30 * reachAmt * reach
            sx *= r; sy *= r * pinch; sz *= r * pinch
            persp = 3.4 / (3.4 - sz)
            spx, spy = scx + sx * R * persp, scy - sy * R * persp
            sFront = sz >= 0

            delay = (1.0 - clampf(dp, -1, 1)) * 0.5
            mi = smoothstepf(0.0, 1.0, m * 1.7 - delay * 0.7)

            th = d.ang - tShared * d.omega
            ct, st = math.cos(th), math.sin(th)
            rpx = d.rdn * Rh
            dzp = -rpx * st
            ux = rpx * ct
            uy = dzp * sE + d.jitter * Rh
            vx = ux * cD + uy * sD
            vy = -ux * sD + uy * cD
            dpx, dpy = hcx + vx, hcy - vy
            dFront = dzp < 0

            front = sFront if mi < 0.5 else dFront
            drawMain = front == (p == 2)
            drawLens = p == 0 and not dFront and mi > 0.05 and hR > 2.0
            if not drawMain and not drawLens:
                continue

            k = (d.rdn - 1.20) / 2.30
            hr, hg, hb = disk_color(k)
            doppler = 1.0 - 0.45 * ct

            if drawMain:
                px = spx + (dpx - spx) * mi
                py = spy + (dpy - spy) * mi
                tw = mi * (1.0 - mi) * 4.0
                py += tw * 10.0 * math.sin(th * 2.0 + t)
                rr, gg, bb = hsv_to_rgb(d.hue + hueBase + 0.04 * t + 0.25 * reachAmt * reach, 0.95, 1.0)
                sb = (0.55 + 0.45 * clampf(sz, 0, 1)) if sFront else (0.12 + 0.25 * (1.0 + clampf(sz, -1, 0)))
                sb *= 0.9 + 0.25 * P
                db = (1.0 if dFront else 0.80) * (1.0 - 0.55 * k) * doppler
                cr = rr * sb + (hr * db - rr * sb) * mi
                cg = gg * sb + (hg * db - gg * sb) * mi
                cb = bb * sb + (hb * db - bb * sb) * mi
                c = pack(cr, cg, cb)
                hidden = False
                if not front and mi > 0.5:
                    ex, ey = px - hcx, py - hcy
                    hidden = ex * ex + ey * ey < hR * hR
                if not hidden:
                    if front or mi > 0.5:
                        fb.fill_rect(px, py, 2, 2, c)
                    else:
                        fb.plot(px, py, c)

            if drawLens:
                far = dzp / rpx
                lb = mi * 0.90 * (1.0 - 0.5 * k) * doppler
                lr = hR * (1.10 + 0.40 * k)
                ax, ay = ct * lr, far * lr * 1.04
                lx, ly = hcx + ax * cD + ay * sD, hcy - (-ax * sD + ay * cD)
                fb.fill_rect(lx, ly, 2, 1, pack(hr * lb, hg * lb, hb * lb))
                lr2 = hR * (1.06 + 0.12 * k)
                bx, by = ct * lr2, -far * lr2
                l2x, l2y = hcx + bx * cD + by * sD, hcy - (-bx * sD + by * cD)
                lb2 = lb * 0.40
                fb.plot(l2x, l2y, pack(hr * lb2, hg * lb2, hb * lb2))


def main(out="extras/previews/sharedhole-v1-preview.png"):
    dots, stars = build_scene()
    glowL, glowR = build_glow(1.0), build_glow(-1.0)
    pairs = []
    for P in (0.0, 0.3, 0.5, 0.6, 0.75, 0.9, 1.0):
        L, Rb = FB(), FB()
        render(L, dots, stars, glowL, P, 1.0, 3.0, 7.0, 1.1, 0.0)
        render(Rb, dots, stars, glowR, P, -1.0, 3.0, 7.0, 1.1, 0.55)
        pairs.append(compose_pair(L, Rb, int(GAP_PX)))
    strip = compose_strip(pairs)
    strip.save(out)
    print("wrote", out, strip.size)


if __name__ == "__main__":
    main(*sys.argv[1:])
