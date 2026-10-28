"""Preview of the reworked MiniGalaxy_Earth — 1:1 port of its renderScene().

Both boards draw ONE scene: a 280-px-wide virtual canvas (screen, bezel gap, screen) holding
the left sphere, the right sphere and the shared black hole in the gap. Each board shows its
own 128-px window of it. When the spheres merge, every dot spirals around the hole as a tidal
stream instead of flying in a straight line to a random disk slot.

    python extras/sim/preview_sharedhole_v2.py            -> extras/previews/sharedhole-rainbow-preview.png
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sim"))
from tqt_sim import *

RSSI_FAR, MERGE_START_DBM, MERGE_FULL_DBM = -20.0, -17.0, -13.0
RSSI_NEAR = MERGE_FULL_DBM
MERGE_START = (MERGE_START_DBM - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR)
MERGE_FULL = (MERGE_FULL_DBM - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR)
GAP_PX, HOLE_RADIUS, DISK_TILT = 24.0, 44.0, 0.10
DISK_INNER, DISK_OUTER = 1.20, 3.40           # disk radii in horizon radii
SPHERE_RADIUS, RINGS, NUM_STARS = 55.0, 44, 70
MAX_DOTS = 2600
STREAM_DIP = 0.22                              # how far the stream dives toward the hole mid-way
REACH_AMP  = 0.60                              # how far the lobe stretches toward the other sphere


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
            # Disk slot comes from where the dot sits on the sphere (not a random hash), so
            # neighbouring dots stay neighbours while they fall in: the equator feeds the hot
            # inner edge, the poles spread out to the cool outer rim.
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


def render(fb, dots, stars, glow, P, sgn, t, tShared, rotY, hueL, hueR):
    """sgn = +1 if this board is the LEFT one (peer on its right), -1 if it is the right one."""
    m = clampf((P - MERGE_START) / (MERGE_FULL - MERGE_START), 0.0, 1.0)
    reachAmt = clampf(P / MERGE_START, 0, 1) * (1.0 - m)

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
    R = SPHERE_RADIUS * (1.0 + 0.02 * math.sin(t * 1.7))

    cR, sR = math.cos(rotY), math.sin(rotY)
    cT, sT = math.cos(0.42), math.sin(0.42)
    sE = math.sin(0.17)
    cD, sD = math.cos(DISK_TILT), math.sin(DISK_TILT)

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
        hueBase = hueL if sphere > 0 else hueR
        # Skip the other board's sphere while it can't reach into this screen.
        if not mine and m <= 0.0:
            extent = R * (1.0 + REACH_AMP * reachAmt) * 1.42
            if cx - extent > W or cx + extent < 0:
                continue

        for d in dots:
            # ---- sphere: rotate, tilt, stretch toward the other sphere ----
            x1 = d.x * cR + d.z * sR
            z1 = -d.x * sR + d.z * cR
            sy = d.y * cT - z1 * sT
            sz = d.y * sT + z1 * cT
            sx = x1
            dp = sx * sphere                    # +1 = facing the other sphere
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

            if mi <= 0.0:
                if spx < -2 or spx > W + 1 or spy < -2 or spy > H + 1:
                    continue
                rr, gg, bb = hsv_to_rgb(d.hue + hueBase + 0.04 * t + 0.25 * reachAmt * reach, 0.95, 1.0)
                sb = (0.55 + 0.45 * clampf(sz, 0, 1)) if sFront else (0.12 + 0.25 * (1.0 + clampf(sz, -1, 0)))
                sb *= 0.9 + 0.25 * P
                (front_list if sFront else back).append((spx, spy, pack(rr * sb, gg * sb, bb * sb), 2 if sFront else 1))
                continue

            # ---- shared disk slot (same on both boards, driven by the shared clock) ----
            th = d.ang + angOff - tShared * d.omega
            ct, st = math.cos(th), math.sin(th)
            rpx = d.rdn * Rh
            dzp = -rpx * st                     # > 0 = far side (behind the hole)
            ux = rpx * ct
            uy = dzp * sE + d.jitter * Rh
            vx = ux * cD + uy * sD
            vy = -ux * sD + uy * cD
            dpx, dpy = hcx + vx, hcy - vy
            dFront = dzp < 0
            k = (d.rdn - DISK_INNER) / (DISK_OUTER - DISK_INNER)
            hr, hg, hb = disk_color(k)
            doppler = 1.0 - 0.45 * ct                 # side moving toward you is brighter...
            red = max(ct, 0.0)                        # ...the receding side goes dim AND red
            hg *= 1.0 - 0.35 * red
            hb *= 1.0 - 0.60 * red

            # ---- tidal stream: spiral around the hole from the sphere slot to the disk slot ----
            if mi >= 1.0:
                px, py = dpx, dpy
            else:
                ax, ay = spx - hcx, hcy - spy
                bx, by = dpx - hcx, hcy - dpy
                ra, aa = math.hypot(ax, ay), math.atan2(ay, ax)
                rb, ab = math.hypot(bx, by), math.atan2(by, bx)
                dth = ab - aa
                while dth > 0.0: dth -= TWO_PI      # always sweep in the disk's spin direction
                while dth <= -TWO_PI: dth += TWO_PI
                rr_ = ra + (rb - ra) * mi
                rr_ *= 1.0 - STREAM_DIP * math.sin(PI * mi)
                if rr_ < hR * 1.08: rr_ = hR * 1.08
                a = aa + dth * mi
                px, py = hcx + rr_ * math.cos(a), hcy - rr_ * math.sin(a)

            front = sFront if mi < 0.5 else dFront
            if px >= -2 and px <= W + 1 and py >= -2 and py <= H + 1:
                rr, gg, bb = hsv_to_rgb(d.hue + hueBase + 0.04 * t + 0.25 * reachAmt * reach, 0.95, 1.0)
                sb = (0.55 + 0.45 * clampf(sz, 0, 1)) if sFront else (0.12 + 0.25 * (1.0 + clampf(sz, -1, 0)))
                sb *= 0.9 + 0.25 * P
                db = (1.0 if dFront else 0.80) * (1.0 - 0.55 * k) * doppler
                heat = 1.0 + 0.3 * math.sin(PI * mi)           # the stream runs hot
                cr = (rr * sb + (hr * db - rr * sb) * mi) * heat
                cg = (gg * sb + (hg * db - gg * sb) * mi) * heat
                cb = (bb * sb + (hb * db - bb * sb) * mi) * heat
                hidden = False
                if not front and mi > 0.5:
                    ex, ey = px - hcx, py - hcy
                    hidden = ex * ex + ey * ey < hR * hR
                if not hidden:
                    (front_list if front else back).append((px, py, pack(cr, cg, cb), 2 if (front or mi > 0.5) else 1))

            # ---- lensed images of the far side of the disk ----
            if not dFront and mi > 0.05 and hR > 2.0:
                far = dzp / rpx
                lb = smoothstepf(0.4, 1.0, mi) * 0.90 * (1.0 - 0.5 * k) * doppler
                lr = hR * (1.10 + 0.40 * k)
                ax, ay = ct * lr, far * lr * 1.04
                lx, ly = hcx + ax * cD + ay * sD, hcy - (-ax * sD + ay * cD)
                back.append((lx, ly, pack(hr * lb, hg * lb, hb * lb), 3))        # 3 = 2x1
                lr2 = hR * (1.06 + 0.12 * k)
                bx, by = ct * lr2, -far * lr2
                l2x, l2y = hcx + bx * cD + by * sD, hcy - (-bx * sD + by * cD)
                lb2 = lb * 0.40
                back.append((l2x, l2y, pack(hr * lb2, hg * lb2, hb * lb2), 1))

    def draw(lst):
        for x, y, c, sz in lst:
            if sz == 2: fb.fill_rect(x, y, 2, 2, c)
            elif sz == 3: fb.fill_rect(x, y, 2, 1, c)
            else: fb.plot(x, y, c)

    draw(back)
    if m > 0.01:
        fb.fill_circle(hcx, hcy, hR * 1.05, pack(0.95 * m, 0.90 * m, 0.80 * m))
        fb.fill_circle(hcx, hcy, hR, (0, 0, 0))
    draw(front_list)


def main(out="extras/previews/sharedhole-rainbow-preview.png", tShared=7.0):
    dots, stars = build_scene()
    glowL, glowR = build_glow(1.0), build_glow(-1.0)
    pairs = []
    # one frame per dBm step through the merge, labelled by signal strength
    for dbm in (-22, -20, -18.5, -17, -16, -15, -14.5, -14, -13):
        P = clampf((dbm - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR), 0.0, 1.0)
        L, Rb = FB(), FB()
        render(L, dots, stars, glowL, P, 1.0, 3.0, float(tShared), 1.1, 0.0, 0.55)
        render(Rb, dots, stars, glowR, P, -1.0, 3.0, float(tShared), 1.1, 0.0, 0.55)
        pairs.append(compose_pair(L, Rb, int(GAP_PX)))
    strip = compose_strip(pairs)
    strip.save(out)
    print("wrote", out, strip.size)


if __name__ == "__main__":
    main(*sys.argv[1:])
