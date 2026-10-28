"""Preview of MiniGalaxy_Earth (chunky Earth version) -- 1:1 port of its renderScene().

Both boards draw ONE scene: a 280-px-wide virtual canvas (screen, bezel gap, screen) holding
the left Earth, the right Earth and the shared black hole in the gap. Each board shows its
own 128-px window of it. At rest each board shows a chunky-pixel Earth (blue sea, green
land); as the boards approach it stretches toward the other one, then every dot spirals
into the black hole.

    python sim/preview_earth.py   -> reference/sharedhole-preview.png  (merge, by dBm)
                                          -> reference/earth-rest-preview.png     (resting Earths)
The Earth texture comes from sim/earth_map.npz (python sim/make_earth_map.py).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tqt_sim import *

RSSI_FAR, MERGE_START_DBM, MERGE_FULL_DBM = -20.0, -17.0, -13.0
RSSI_NEAR = MERGE_FULL_DBM
MERGE_START = (MERGE_START_DBM - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR)
MERGE_FULL = (MERGE_FULL_DBM - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR)
GAP_PX, HOLE_RADIUS, DISK_TILT = 24.0, 44.0, 0.10
DISK_INNER, DISK_OUTER = 1.20, 3.40           # disk radii in horizon radii
SPHERE_RADIUS, RINGS, NUM_STARS = 55.0, 36, 70
MAX_DOTS = 1700
STREAM_DIP = 0.22                              # how far the stream dives toward the hole mid-way
REACH_AMP  = 0.60                              # how far the lobe stretches toward the other sphere

SPIN_PERIOD_S = 60.0
SUN = (-0.62, 0.30, 0.72)
TILT = 0.42

_map = np.load(os.path.join(os.path.dirname(__file__), "earth_map.npz"))
EARTH_LAND = _map["land"]
EARTH_TH, EARTH_TW = EARTH_LAND.shape


def turn16(f):
    f -= math.floor(f)
    return int(f * 65536.0) & 0xFFFF


SEA_DEEP, SEA_SHALLOW = (0.03, 0.10, 0.38), (0.10, 0.34, 0.72)
LAND_DARK, LAND_MID, LAND_LIGHT = (0.08, 0.38, 0.10), (0.22, 0.58, 0.14), (0.48, 0.76, 0.24)
EARTH_PAL = [SEA_DEEP, SEA_DEEP, SEA_SHALLOW, LAND_LIGHT, LAND_MID, LAND_DARK, LAND_DARK, LAND_MID,
             LAND_LIGHT, LAND_MID, LAND_DARK, LAND_MID, SEA_DEEP, SEA_DEEP, SEA_DEEP, SEA_DEEP]


class Dot:
    __slots__ = ("x", "y", "z", "rdn", "ang", "omega", "jitter", "land")


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
            tu = turn16(0.5 - lon / TWO_PI)
            tv = int(clampf((0.5 - lat / PI) * EARTH_TH, 0, EARTH_TH - 1))
            d.land = int(EARTH_LAND[tv, tu >> 8]) & 15
            u = (1.0 - cl) ** 0.55 + 0.05 * (hash01(n * 2 + 1) - 0.5)
            d.rdn = DISK_INNER + (DISK_OUTER - DISK_INNER) * clampf(u, 0.0, 1.0)
            d.ang = lon
            d.omega = 1.3 / (d.rdn * math.sqrt(d.rdn))
            d.jitter = (0.025 if sl >= 0 else -0.025) + (hash01(n * 2 + 7) - 0.5) * 0.05
            dots.append(d)
    for i in range(NUM_STARS):
        stars.append((hash01(i * 3 + 101) * W, hash01(i * 3 + 202) * H, 0.15 + 0.45 * hash01(i * 3 + 303)))
    return dots, stars


def disk_color(k):
    k = clampf(k, 0.0, 1.0)
    if k < 0.30:
        t = k / 0.30;            return 1.0, 1.0 - 0.08 * t, 1.0 - 0.30 * t
    elif k < 0.65:
        t = (k - 0.30) / 0.35;   return 1.0, 0.92 - 0.32 * t, 0.70 - 0.45 * t
    else:
        t = (k - 0.65) / 0.35;   return 1.0 - 0.25 * t, 0.60 - 0.32 * t, 0.25 - 0.18 * t


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


def render(fb, dots, stars, glow, P, sgn, t, tShared, spinExtra=0.0):
    """sgn = +1 if this board is the LEFT one (peer on its right), -1 if it is the right one."""
    m = clampf((P - MERGE_START) / (MERGE_FULL - MERGE_START), 0.0, 1.0)
    reachAmt = clampf(P / MERGE_START, 0.0, 1.0) * (1.0 - m)

    if m > 0.01:
        g = glow * m * 0.42
        fb.px[..., 0] = (np.clip(g, 0, 1) * 255).astype(np.uint8) & 0xF8
        fb.px[..., 1] = (np.clip(g * 0.60, 0, 1) * 255).astype(np.uint8) & 0xFC
        fb.px[..., 2] = (np.clip(g * 0.30, 0, 1) * 255).astype(np.uint8) & 0xF8
    else:
        fb.clear()

    hcx, hcy = hole_center_x(sgn), H * 0.5
    hR = HOLE_RADIUS * smoothstepf(0.0, 1.0, m)
    Rh = HOLE_RADIUS
    R = SPHERE_RADIUS

    rotY = TWO_PI * math.fmod(tShared, SPIN_PERIOD_S) / SPIN_PERIOD_S + spinExtra
    cT, sT = math.cos(TILT), math.sin(TILT)
    sE = math.sin(0.17)
    cD, sD = math.cos(DISK_TILT), math.sin(DISK_TILT)
    bright = 1.0 + 0.15 * P
    sn = math.sqrt(sum(c * c for c in SUN))
    lx, ly, lz = (c / sn for c in SUN)
    dot_size = 3 if m > 0.0 else (5 if reachAmt < 0.5 else 4)

    # --- stars ---
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

    back, front_list = [], []           # (x, y, colour, size)

    for sphere in (1, -1):              # +1 = the left sphere, -1 = the right sphere
        mine = (sphere == sgn)
        cx = W * 0.5 + (0.0 if mine else sgn * (W + GAP_PX)) + sphere * 9.0 * reachAmt
        cy = H * 0.5
        angOff = 0.0 if sphere > 0 else PI
        if not mine and m <= 0.0:
            extent = R * (1.0 + REACH_AMP * reachAmt) * 1.42
            if cx - extent > W or cx + extent < 0:
                continue
        spin = rotY + (0.0 if sphere > 0 else PI)
        cR, sR = math.cos(spin), math.sin(spin)

        for d in dots:
            x1 = d.x * cR + d.z * sR
            z1 = -d.x * sR + d.z * cR
            sy = d.y * cT - z1 * sT
            sz = d.y * sT + z1 * cT
            sx = x1
            nx, ny, nz = sx, sy, sz
            dp = sx * sphere
            reach = dp ** 3 if dp > 0 else 0.0
            back_ = -dp if dp < 0 else 0.0
            r = 1.0 + reachAmt * (REACH_AMP * reach - 0.10 * back_)
            pinch = 1.0 - 0.30 * reachAmt * reach
            sx *= r; sy *= r * pinch; sz *= r * pinch
            persp = 3.4 / (3.4 - sz)
            spx, spy = cx + sx * R * persp, cy - sy * R * persp
            sFront = sz >= 0

            delay = (1.0 - clampf(dp, -1, 1)) * 0.5
            mi = smoothstepf(0.0, 1.0, m * 1.7 - delay * 0.7)

            def earth_colour():
                lit = (0.30 + 0.70 * clampf(nx * lx + ny * ly + nz * lz, 0.0, 1.0)) * bright
                c = EARTH_PAL[d.land]
                return c[0] * lit, c[1] * lit, c[2] * lit

            if mi <= 0.0:
                if not sFront:
                    continue
                if spx < -2 or spx > W + 1 or spy < -2 or spy > H + 1:
                    continue
                er, eg, eb = earth_colour()
                front_list.append((int(spx) - 1, int(spy) - 1, pack(er, eg, eb), 10 + dot_size))
                continue

            th = d.ang + angOff - tShared * d.omega
            ct, st = math.cos(th), math.sin(th)
            rpx = d.rdn * Rh
            dzp = -rpx * st
            ux = rpx * ct
            uy = dzp * sE + d.jitter * Rh
            vx = ux * cD + uy * sD
            vy = -ux * sD + uy * cD
            dpx, dpy = hcx + vx, hcy - vy
            dFront = dzp < 0
            k = (d.rdn - DISK_INNER) / (DISK_OUTER - DISK_INNER)
            hr, hg, hb = disk_color(k)
            doppler = 1.0 - 0.45 * ct
            red = max(ct, 0.0)
            hg *= 1.0 - 0.35 * red
            hb *= 1.0 - 0.60 * red

            if mi >= 1.0:
                px, py = dpx, dpy
            else:
                ax, ay = spx - hcx, hcy - spy
                bx, by = dpx - hcx, hcy - dpy
                ra, aa = math.hypot(ax, ay), math.atan2(ay, ax)
                rb, ab = math.hypot(bx, by), math.atan2(by, bx)
                dth = ab - aa
                while dth > 0.0: dth -= TWO_PI
                while dth <= -TWO_PI: dth += TWO_PI
                rr_ = ra + (rb - ra) * mi
                rr_ *= 1.0 - STREAM_DIP * math.sin(PI * mi)
                if rr_ < hR * 1.08: rr_ = hR * 1.08
                a = aa + dth * mi
                px, py = hcx + rr_ * math.cos(a), hcy - rr_ * math.sin(a)

            front = sFront if mi < 0.5 else dFront
            if px >= -2 and px <= W + 1 and py >= -2 and py <= H + 1:
                er, eg, eb = earth_colour()
                if not sFront:
                    f = smoothstepf(0.0, 0.3, mi)
                    er, eg, eb = er * f, eg * f, eb * f
                db = (1.0 if dFront else 0.80) * (1.0 - 0.55 * k) * doppler
                heat = 1.0 + 0.3 * math.sin(PI * mi)
                cr = (er + (hr * db - er) * mi) * heat
                cg = (eg + (hg * db - eg) * mi) * heat
                cb = (eb + (hb * db - eb) * mi) * heat
                hidden = False
                if not front and mi > 0.5:
                    ex_, ey_ = px - hcx, py - hcy
                    hidden = ex_ * ex_ + ey_ * ey_ < hR * hR
                if not hidden:
                    (front_list if front else back).append((px, py, pack(cr, cg, cb), 2 if (front or mi > 0.5) else 1))

            if not dFront and mi > 0.05 and hR > 2.0:
                far = dzp / rpx
                lb = smoothstepf(0.4, 1.0, mi) * 0.90 * (1.0 - 0.5 * k) * doppler
                lr = hR * (1.10 + 0.40 * k)
                ax, ay = ct * lr, far * lr * 1.04
                lx_, ly_ = hcx + ax * cD + ay * sD, hcy - (-ax * sD + ay * cD)
                back.append((lx_, ly_, pack(hr * lb, hg * lb, hb * lb), 3))
                lr2 = hR * (1.06 + 0.12 * k)
                bx, by = ct * lr2, -far * lr2
                l2x, l2y = hcx + bx * cD + by * sD, hcy - (-bx * sD + by * cD)
                lb2 = lb * 0.40
                back.append((l2x, l2y, pack(hr * lb2, hg * lb2, hb * lb2), 1))

    def draw(lst):
        for x, y, c, sz in lst:
            if sz == 2: fb.fill_rect(x, y, 2, 2, c)
            elif sz >= 10: fb.fill_rect(x, y, sz - 10, sz - 10, c)
            elif sz == 3: fb.fill_rect(x, y, 2, 1, c)
            else: fb.plot(x, y, c)

    draw(back)
    if m > 0.01:
        fb.fill_circle(hcx, hcy, hR * 1.05, pack(0.95 * m, 0.90 * m, 0.80 * m))
        fb.fill_circle(hcx, hcy, hR, (0, 0, 0))
    draw(front_list)


def pair(dots, stars, glowL, glowR, P, tShared):
    L, Rb = FB(), FB()
    render(L, dots, stars, glowL, P, 1.0, 3.0, float(tShared))
    render(Rb, dots, stars, glowR, P, -1.0, 3.0, float(tShared))
    return compose_pair(L, Rb, int(GAP_PX))


def main(out="reference/sharedhole-preview.png", tShared=7.0):
    dots, stars = build_scene()
    print("dots:", len(dots))
    glowL, glowR = build_glow(1.0), build_glow(-1.0)
    # resting Earths at a few moments of the turn
    rest = [pair(dots, stars, glowL, glowR, 0.0, ts) for ts in (7.0, 22.0, 37.0)]
    compose_strip(rest).save("reference/earth-rest-preview.png")
    # one frame per dBm step through the merge
    pairs = []
    for dbm in (-20, -19.5, -19, -18, -17, -16, -15, -14, -13):
        P = clampf((dbm - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR), 0.0, 1.0)
        pairs.append(pair(dots, stars, glowL, glowR, P, float(tShared)))
    strip = compose_strip(pairs)
    strip.save(out)
    print("wrote", out, strip.size, "and reference/earth-rest-preview.png")


if __name__ == "__main__":
    main(*sys.argv[1:])
