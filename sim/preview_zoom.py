"""Preview of MiniGalaxy_Zoom -- 1:1 port of its renderScene().

Earth -> Moon -> solar system -> Oort cloud -> nearby stars -> Milky Way, in ZOOM_MINUTES,
then fade and repeat. Bring the boards together at any point and whatever is on screen
spirals into the shared black hole.

    python sim/preview_zoom.py            -> reference/zoom-cycle-preview.png  (12 moments of the cycle)
                                          -> reference/zoom-merge-preview.png  (merging at 3 stages)
    python sim/preview_zoom.py 0.27       -> reference/zoom-at-0.27.png (one moment, both boards)
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tqt_sim import *

RSSI_FAR, MERGE_START_DBM, MERGE_FULL_DBM = -20.0, -17.0, -13.0
RSSI_NEAR = MERGE_FULL_DBM
MERGE_START = (MERGE_START_DBM - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR)
MERGE_FULL = (MERGE_FULL_DBM - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR)
GAP_PX, HOLE_RADIUS, DISK_TILT = 24.0, 44.0, 0.10
DISK_INNER, DISK_OUTER = 1.20, 3.40
REACH_AMP, STREAM_DIP = 0.60, 0.22

ZOOM_MINUTES = 7.5
ZOOM_KEYS = [
    (0.000, 7.14, 0.02), (0.022, 7.14, 0.02), (0.164, 9.05, 0.12), (0.373, 11.85, 2.5),
    (0.473, 13.20, 20.0), (0.585, 15.60, 150.0), (0.618, 16.30, 400.0), (0.744, 18.00, 1500.0),
    (0.967, 21.00, 1500.0), (1.000, 21.00, 1500.0),
]
FADE_IN_END, FADE_OUT_BEG, FADE_OUT_END = 0.020, 0.955, 0.985
VIEW_TILT, AXIAL_TILT = 0.50, 0.42
RINGS, NUM_STARS = 36, 70
MAX_DOTS, MAX_PART = 1700, 4000

SEA_DEEP, SEA_SHALLOW = (0.03, 0.10, 0.38), (0.10, 0.34, 0.72)
LAND_DARK, LAND_MID, LAND_LIGHT = (0.08, 0.38, 0.10), (0.22, 0.58, 0.14), (0.48, 0.76, 0.24)
EARTH_PAL = [SEA_DEEP, SEA_DEEP, SEA_SHALLOW, LAND_LIGHT, LAND_MID, LAND_DARK, LAND_DARK, LAND_MID,
             LAND_LIGHT, LAND_MID, LAND_DARK, LAND_MID, SEA_DEEP, SEA_DEEP, SEA_DEEP, SEA_DEEP]

AU, LY = 1.496e11, 9.461e15
PLANETS = [  # a, period, radius, r, g, b, phase0
    (0.387 * AU, 87.97, 2.44e6, 0.62, 0.60, 0.56, 1.3),
    (0.723 * AU, 224.70, 6.05e6, 0.95, 0.86, 0.62, 3.1),
    (1.000 * AU, 365.25, 6.371e6, 0.30, 0.55, 1.00, 1.20),
    (1.524 * AU, 687.00, 3.39e6, 0.90, 0.45, 0.25, 5.0),
    (5.203 * AU, 4332.60, 6.99e7, 0.85, 0.72, 0.52, 0.6),
    (9.537 * AU, 10759.00, 5.82e7, 0.90, 0.82, 0.58, 2.2),
    (19.19 * AU, 30687.00, 2.54e7, 0.62, 0.85, 0.90, 4.1),
    (30.07 * AU, 60190.00, 2.46e7, 0.35, 0.45, 0.95, 5.6),
]
EARTH_IX = 2
SUN_RADIUS = 6.96e8
MOON_A, MOON_PERIOD, MOON_RADIUS = 3.844e8, 27.32, 1.737e6
GAL_CENTER_LY, GAL_DIR_X, GAL_DIR_Y = 26000.0, -0.55, 0.835
N_GALAXY, N_NEAR, N_OORT = 1400, 350, 300
PF_BACK, PF_EARTH, PF_OTHER, PF_FRONT = 1, 2, 4, 8

_map = np.load(os.path.join(os.path.dirname(__file__), "earth_map.npz"))
EARTH_LAND = _map["land"]
EARTH_TH, EARTH_TW = EARTH_LAND.shape


def turn16(f):
    f -= math.floor(f)
    return int(f * 65536.0) & 0xFFFF


def unpack(c):
    return c[0] / 255.0, c[1] / 255.0, c[2] / 255.0


def disk_color(k):
    k = clampf(k, 0.0, 1.0)
    if k < 0.30:
        t = k / 0.30;            return 1.0, 1.0 - 0.08 * t, 1.0 - 0.30 * t
    elif k < 0.65:
        t = (k - 0.30) / 0.35;   return 1.0, 0.92 - 0.32 * t, 0.70 - 0.45 * t
    else:
        t = (k - 0.65) / 0.35;   return 1.0 - 0.25 * t, 0.60 - 0.32 * t, 0.25 - 0.18 * t


# ------------------------------------------------------------------ timeline
def zoom_at(phase):
    phase = clampf(phase, 0.0, 1.0)
    i = 0
    while i < len(ZOOM_KEYS) - 2 and phase >= ZOOM_KEYS[i + 1][0]:
        i += 1
    p0, w0, r0 = ZOOM_KEYS[i]
    p1, w1, r1 = ZOOM_KEYS[i + 1]
    f = clampf((phase - p0) / (p1 - p0), 0.0, 1.0)
    return w0 + (w1 - w0) * f, math.exp(math.log(r0) + (math.log(r1) - math.log(r0)) * f)


def build_day_table():
    cycle = ZOOM_MINUTES * 60.0
    tab = [0.0]
    cum, r0 = 0.0, zoom_at(0.0)[1]
    for k in range(1, 257):
        r1 = zoom_at(k / 256.0)[1]
        cum += 0.5 * (r0 + r1) * (cycle / 256.0)
        tab.append(cum)
        r0 = r1
    return tab


DAY_TAB = build_day_table()


def sim_days_at(phase):
    f = clampf(phase, 0.0, 1.0) * 256.0
    k = min(int(f), 255)
    return DAY_TAB[k] + (DAY_TAB[k + 1] - DAY_TAB[k]) * (f - k)


# ------------------------------------------------------------------ building
class Dot:
    __slots__ = ("x", "y", "z", "land", "u", "a")


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
            d.u = int(clampf(u, 0.0, 1.0) * 255.0)
            d.a = int(lon / TWO_PI * 255.0)
            dots.append(d)
    for i in range(NUM_STARS):
        stars.append((hash01(i * 3 + 101) * W, hash01(i * 3 + 202) * H, 0.15 + 0.45 * hash01(i * 3 + 303)))
    galaxy = []
    for i in range(N_GALAXY):
        h1, h2, h3, h4 = hash01(i * 7 + 11), hash01(i * 7 + 13), hash01(i * 7 + 17), hash01(i * 7 + 19)
        if (i & 3) == 0:
            r, th, typ = 4500.0 * math.sqrt(h1), h2 * TWO_PI, 0
        else:
            r = 1500.0 + 48500.0 * h1 ** 0.65
            arm = PI if (i & 1) else 0.0
            th = arm + 3.6 * math.log(r / 1500.0) + (h2 + h3 - 1.0) * 0.45
            typ = 1
            if (i % 3) == 2:
                th += (h4 - 0.5) * 2.5
                typ = 2
        galaxy.append((int(r * math.cos(th) / 100.0), int(r * math.sin(th) / 100.0), typ))
    near = []
    for i in range(N_NEAR):
        h1, h2, h3 = hash01(i * 5 + 23), hash01(i * 5 + 29), hash01(i * 5 + 31)
        r, th = 150.0 * math.sqrt(h1), h2 * TWO_PI
        x, y = int(r * math.cos(th) * 2.0), int(r * math.sin(th) * 2.0)
        if h3 < 0.30:   typ, br = 0, int(60 + 50 * hash01(i * 5 + 37))
        elif h3 < 0.85: typ, br = 1, int(120 + 100 * hash01(i * 5 + 37))
        else:           typ, br = 2, int(200 + 55 * hash01(i * 5 + 37))
        near.append((x, y, br, typ))
    return dots, stars, galaxy, near


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


# ------------------------------------------------------------------ emitters
class Emitter:
    def __init__(self, dots, galaxy, near):
        self.dots, self.galaxy, self.near = dots, galaxy, near
        self.parts = []           # [x, y, c, size, u, a, fl]
        self.cullX0, self.cullX1, self.cullAll = -3.0, W + 2.0, False

    def add(self, x, y, c, size, u, a, fl, may_poke=False):
        if len(self.parts) >= MAX_PART:
            return
        if not self.cullAll:
            x0 = -3.0 if may_poke else self.cullX0
            x1 = W + 2.0 if may_poke else self.cullX1
            if x < x0 or x > x1 or y < -3.0 or y > H + 2.0:
                return
        elif x < -3 * W or x > 4 * W or y < -3 * H or y > 4 * H:
            return
        self.parts.append([int(math.floor(x)), int(math.floor(y)), c, size, u & 255, a & 255, fl])

    def earth_dots(self, cx, cy, R, sphere, spin, reachAmt, lx, ly, lz, size_f, env, other, with_back):
        cR, sR = math.cos(spin), math.sin(spin)
        cT, sT = math.cos(AXIAL_TILT), math.sin(AXIAL_TILT)
        fl0 = PF_EARTH | (PF_OTHER if other else 0)
        aOff = 128 if other else 0
        base_size = int(math.floor(size_f))
        frac = size_f - base_size
        for i, d in enumerate(self.dots):
            dot_size = base_size + (1 if hash01(i * 7 + 99) < frac else 0)
            off = dot_size // 2
            x1 = d.x * cR + d.z * sR
            z1 = -d.x * sR + d.z * cR
            sy = d.y * cT - z1 * sT
            sz = d.y * sT + z1 * cT
            sx = x1
            nx, ny, nz = sx, sy, sz
            sFront = sz >= 0
            if not sFront and not with_back:
                continue
            dp = sx * sphere
            reach = dp ** 3 if dp > 0 else 0.0
            back = -dp if dp < 0 else 0.0
            r = 1.0 + reachAmt * (REACH_AMP * reach - 0.10 * back)
            pinch = 1.0 - 0.30 * reachAmt * reach
            sx *= r; sy *= r * pinch; sz *= r * pinch
            persp = 3.4 / (3.4 - sz)
            spx, spy = cx + sx * R * persp, cy - sy * R * persp
            lit = (0.30 + 0.70 * clampf(nx * lx + ny * ly + nz * lz, 0.0, 1.0)) * env
            c = EARTH_PAL[d.land]
            self.add(spx - off, spy - off, pack(c[0] * lit, c[1] * lit, c[2] * lit), dot_size,
                     d.u, d.a + aOff, fl0 | (0 if sFront else PF_BACK), True)

    def mini_globe(self, cx, cy, rad, spin, lx, ly, lz, env, other):
        cR, sR = math.cos(spin), math.sin(spin)
        cT, sT = math.cos(AXIAL_TILT), math.sin(AXIAL_TILT)
        fl0 = PF_EARTH | (PF_OTHER if other else 0)
        aOff = 128 if other else 0
        for py in range(int(math.floor(cy - rad)), int(math.ceil(cy + rad)) + 1):
            for px in range(int(math.floor(cx - rad)), int(math.ceil(cx + rad)) + 1):
                nx, ny = (px + 0.5 - cx) / rad, (cy - (py + 0.5)) / rad
                d2 = nx * nx + ny * ny
                if d2 > 1.0:
                    continue
                nz = math.sqrt(1.0 - d2)
                ey = ny * cT + nz * sT
                z1 = -ny * sT + nz * cT
                ex = nx * cR - z1 * sR
                ez = nx * sR + z1 * cR
                lon = math.atan2(ez, ex)
                lat = math.asin(clampf(ey, -1.0, 1.0))
                tu = turn16(0.5 - lon / TWO_PI)
                tv = int(clampf((0.5 - lat / PI) * EARTH_TH, 0, EARTH_TH - 1))
                c = EARTH_PAL[int(EARTH_LAND[tv, tu >> 8]) & 15]
                lit = (0.30 + 0.70 * clampf(nx * lx + ny * ly + nz * lz, 0.0, 1.0)) * env
                u = int(math.sqrt(1.0 - math.cos(lat)) * 255.0)
                a = ((tu >> 8) + aOff) & 255
                self.add(px, py, pack(c[0] * lit, c[1] * lit, c[2] * lit), 1, u, a, fl0, True)

    def disc(self, cx, cy, rad, cr, cg, cb, lx, ly, lz, env, ident, other):
        rad = min(rad, 40.0)
        fl0 = PF_OTHER if other else 0
        x0, x1 = int(math.floor(cx - rad)), int(math.ceil(cx + rad))
        y0, y1 = int(math.floor(cy - rad)), int(math.ceil(cy + rad))
        if x1 < self.cullX0 - W or x0 > self.cullX1 + W:
            return
        for py in range(y0, y1 + 1):
            for px in range(x0, x1 + 1):
                nx, ny = (px + 0.5 - cx) / rad, (cy - (py + 0.5)) / rad
                d2 = nx * nx + ny * ny
                if d2 > 1.0:
                    continue
                nz = math.sqrt(1.0 - d2)
                lit = (0.18 + 0.82 * clampf(nx * lx + ny * ly + nz * lz, 0.0, 1.0)) * env
                h = (ident * 7919 + (px - x0) * 131 + (py - y0)) & 0xFFFFFFFF
                self.add(px, py, pack(cr * lit, cg * lit, cb * lit), 1,
                         int(hash01(h) * 255), int(hash01(h + 17) * 255), fl0)

    def pixel(self, x, y, r, g, b, ident, other):
        self.add(math.floor(x), math.floor(y), pack(r, g, b), 1, int(hash01(ident * 13 + 5) * 255),
                 int(hash01(ident * 13 + 9) * 255), PF_OTHER if other else 0)

    def body(self, x, y, r, g, b, ident, other):
        self.add(math.floor(x - 0.5), math.floor(y - 0.5), pack(r, g, b), 2, int(hash01(ident * 13 + 5) * 255),
                 int(hash01(ident * 13 + 9) * 255), PF_OTHER if other else 0)

    def ring(self, cx, cy, ra, alpha, ident, other):
        if alpha <= 0.01:
            return
        if cx + ra < self.cullX0 - 2 or cx - ra > self.cullX1 + 2:
            return
        n = int(clampf(ra * 0.9, 16.0, 120.0))
        cr, cg, cb = 0.35 * alpha, 0.42 * alpha, 0.55 * alpha
        for k in range(n):
            th = TWO_PI * k / n
            self.pixel(cx + ra * math.cos(th), cy - ra * math.sin(th) * VIEW_TILT, cr, cg, cb, ident * 256 + k, other)

    def sun(self, cx, cy, rs, rb, env, other):
        ext = rb * 2.2 + 2.0
        if cx + ext < self.cullX0 - 2 or cx - ext > self.cullX1 + 2 or cy + ext < -3 or cy - ext > H + 2:
            return
        x0, x1 = int(math.floor(cx - ext)), int(math.ceil(cx + ext))
        y0, y1 = int(math.floor(cy - ext)), int(math.ceil(cy + ext))
        for py in range(y0, y1 + 1):
            for px in range(x0, x1 + 1):
                dx, dy = px + 0.5 - cx, py + 0.5 - cy
                d = math.hypot(dx, dy)
                v = 1.0 if d <= rs else math.exp(-(d - rs) / (0.55 * rb))
                if v < 0.06:
                    continue
                v *= env
                self.pixel(px, py, v, v * 0.93, v * 0.70, 900000 + (px - x0) * 97 + (py - y0), other)

    def scene(self, z, ox, oy, sphere, spin, reachAmt, other, with_back):
        ppm, env, logW = z["ppm"], z["env"], z["logW"]
        VT, CT = VIEW_TILT, math.sqrt(1.0 - VIEW_TILT ** 2)
        camX, camY = z["camX"], z["camY"]
        scrX = lambda rx: ox + (rx - camX) * ppm
        scrY = lambda ry: oy - (ry - camY) * ppm * VT
        sunRelX, sunRelY = -z["earthX"], -z["earthY"]
        sunSx, sunSy = scrX(sunRelX), scrY(sunRelY)

        galA = smoothstepf(18.8, 20.2, logW)
        if galA > 0.0:
            gcx = sunRelX + GAL_CENTER_LY * LY * GAL_DIR_X
            gcy = sunRelY + GAL_CENTER_LY * LY * GAL_DIR_Y
            for i, (gx, gy, typ) in enumerate(self.galaxy):
                rx, ry = gcx + gx * (100.0 * LY), gcy + gy * (100.0 * LY)
                dist = math.hypot(gx, gy) / 500.0
                b = (1.0 - 0.55 * dist) * galA * env
                if typ == 0:   col = (1.00 * b, 0.88 * b, 0.68 * b)
                elif typ == 1: col = (0.70 * b * 0.8, 0.80 * b * 0.8, 1.00 * b * 0.8)
                else:          col = (0.85 * b * 0.5, 0.85 * b * 0.5, 0.80 * b * 0.5)
                self.pixel(scrX(rx), scrY(ry), *col, 100000 + i, other)
        nearA = smoothstepf(15.3, 16.3, logW) * (1.0 - smoothstepf(19.3, 20.3, logW))
        if nearA > 0.0:
            for i, (x, y, br, typ) in enumerate(self.near):
                sx, sy = scrX(sunRelX + x * (0.5 * LY)), scrY(sunRelY + y * (0.5 * LY))
                if abs(sx - sunSx) < 1.5 and abs(sy - sunSy) < 1.5:
                    continue
                b = br / 255.0 * nearA * env
                if typ == 0:   self.pixel(sx, sy, b, b * 0.38, b * 0.25, 200000 + i, other)
                elif typ == 1: self.pixel(sx, sy, b, b * 0.97, b * 0.90, 200000 + i, other)
                else:          self.pixel(sx, sy, b * 0.80, b * 0.86, b, 200000 + i, other)
        oortA = 0.45 * smoothstepf(13.3, 14.3, logW) * (1.0 - smoothstepf(16.8, 17.8, logW))
        if oortA > 0.0:
            for i in range(N_OORT):
                rAU = 2000.0 * 50.0 ** hash01(i * 3 + 41)
                th = hash01(i * 3 + 43) * TWO_PI
                b = oortA * env * (0.6 + 0.4 * hash01(i * 3 + 47))
                self.pixel(scrX(sunRelX + rAU * AU * math.cos(th)), scrY(sunRelY + rAU * AU * math.sin(th)),
                           b * 0.55, b * 0.65, b * 0.85, 300000 + i, other)
        for i, p in enumerate(PLANETS):
            ra = p[0] * ppm
            alpha = 0.38 * smoothstepf(2.5, 7.0, ra) * (1.0 - smoothstepf(300.0, 600.0, ra)) * env
            self.ring(sunSx, sunSy, ra, alpha, 1000 + i, other)
        moonRa = MOON_A * ppm
        self.ring(scrX(0.0), scrY(0.0), moonRa,
                  0.38 * smoothstepf(2.5, 7.0, moonRa) * (1.0 - smoothstepf(300.0, 600.0, moonRa)) * env, 1100, other)
        rs = SUN_RADIUS * ppm
        rb = max(rs, 2.6 - 1.6 * smoothstepf(16.0, 18.0, logW))
        self.sun(sunSx, sunSy, rs, rb, env, other)
        here = smoothstepf(19.6, 20.4, logW) * z["pulse"] * env
        if here > 0.02:
            self.body(sunSx, sunSy, here, here, here * 0.9, 700, other)
        for i, (a, period, radius, pr, pg, pb, phase0) in enumerate(PLANETS):
            th = TWO_PI * z["days"] / period + phase0
            relX, relY = a * math.cos(th) - z["earthX"], a * math.sin(th) - z["earthY"]
            sx, sy = scrX(relX), scrY(relY)
            rpx = radius * ppm
            ra = a * ppm
            dX, dY = sunRelX - relX, sunRelY - relY
            dn = math.hypot(dX, dY); dX /= dn; dY /= dn
            lx, ly, lz = dX, dY * VT, -dY * CT
            if i == EARTH_IX:
                if rpx >= 20.0:
                    size_f = clampf(rpx / 11.0, 2.0, 5.0)
                    if self.cullAll and size_f > 3.0:
                        size_f = 3.0
                    self.earth_dots(sx, sy, rpx, sphere, spin, reachAmt, lx, ly, lz, size_f, env, other, with_back)
                elif rpx >= 0.6:
                    self.mini_globe(sx, sy, rpx, spin, lx, ly, lz, env, other)
                elif abs(sx - sunSx) > 1.5 or abs(sy - sunSy) > 1.5:
                    self.body(sx, sy, pr * env, pg * env, pb * env, 500 + i, other)
                continue
            if rpx >= 0.6:
                self.disc(sx, sy, rpx, pr, pg, pb, lx, ly, lz, env, 500 + i, other)
            else:
                vis = smoothstepf(2.5, 6.0, ra) * env
                if vis > 0.02 and (abs(sx - sunSx) > 1.5 or abs(sy - sunSy) > 1.5):
                    self.body(sx, sy, pr * vis, pg * vis, pb * vis, 500 + i, other)
        th = TWO_PI * z["days"] / MOON_PERIOD + 0.8
        relX, relY = MOON_A * math.cos(th), MOON_A * math.sin(th)
        sx, sy = scrX(relX), scrY(relY)
        rpx = MOON_RADIUS * ppm
        dX, dY = sunRelX - relX, sunRelY - relY
        dn = math.hypot(dX, dY); dX /= dn; dY /= dn
        if rpx >= 0.6:
            self.disc(sx, sy, rpx, 0.72, 0.72, 0.70, dX, dY * VT, -dY * CT, env, 600, other)
        else:
            vis = smoothstepf(2.5, 6.0, moonRa) * env
            if vis > 0.02:
                self.body(sx, sy, 0.72 * vis, 0.72 * vis, 0.70 * vis, 600, other)


# ------------------------------------------------------------------ rendering
def zoom_state(phase, spinExtra=0.0):
    logW, rate = zoom_at(phase)
    z = {"logW": logW, "ppm": W / 10.0 ** logW, "days": sim_days_at(phase),
         "env": smoothstepf(0.0, FADE_IN_END, phase) * (1.0 - smoothstepf(FADE_OUT_BEG, FADE_OUT_END, phase))}
    a, period, radius, _, _, _, phase0 = PLANETS[EARTH_IX]
    th = TWO_PI * z["days"] / period + phase0
    z["earthX"], z["earthY"] = a * math.cos(th), a * math.sin(th)
    s = smoothstepf(11.0, 12.6, logW)
    z["camX"], z["camY"] = -z["earthX"] * s, -z["earthY"] * s
    z["rotY"] = TWO_PI * z["days"] + spinExtra
    z["pulse"] = 0.65 + 0.35 * math.sin(3.0 * 3.0)
    z["earthRpx"] = radius * z["ppm"]
    return z


def render(fb, em, stars, glow, P, sgn, t, tShared, phase):
    m = clampf((P - MERGE_START) / (MERGE_FULL - MERGE_START), 0.0, 1.0)
    reachAmt = clampf(P / MERGE_START, 0.0, 1.0) * (1.0 - m)
    z = zoom_state(phase)

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

    for i, (sx0, sy0, b) in enumerate(stars):
        dx, dy = sx0 - hcx, sy0 - hcy
        d2 = dx * dx + dy * dy + 1.0
        push = 1.0 + m * (hR * hR * 1.6) / d2
        tw = 0.75 + 0.25 * math.sin(t * 2.0 + i)
        v = b * tw * (0.5 + 0.3 * m) * (0.4 + 0.6 * z["env"])
        sx, sy = hcx + dx * push, hcy + dy * push
        rx, ry = sx - hcx, sy - hcy
        if m > 0.01 and rx * rx + ry * ry < hR * hR * 1.3:
            continue
        fb.plot(sx, sy, pack(v, v, v))

    em.parts = []
    em.cullAll = m > 0.0
    oxMine = W * 0.5 + sgn * 9.0 * reachAmt
    oxOther = W * 0.5 + sgn * (W + GAP_PX) - sgn * 9.0 * reachAmt
    spinL, spinR = z["rotY"], z["rotY"] + PI
    em.cullX0, em.cullX1 = -3.0, W + 2.0
    em.scene(z, oxMine, H * 0.5, sgn, spinL if sgn > 0 else spinR, reachAmt, False, em.cullAll)
    emit_other = em.cullAll
    if not emit_other and reachAmt > 0.0 and z["earthRpx"] >= 20.0:
        extent = z["earthRpx"] * (1.0 + REACH_AMP * reachAmt) * 1.42
        emit_other = (oxOther - extent < W and oxOther + extent > 0)
    if emit_other:
        em.cullX0, em.cullX1 = oxOther - W * 0.5 - 3.0, oxOther + W * 0.5 + 2.0
        em.scene(z, oxOther, H * 0.5, -sgn, spinR if sgn > 0 else spinL, reachAmt, True, em.cullAll)

    if m <= 0.0:
        for x, y, c, size, u, a, fl in em.parts:
            if fl & PF_BACK:
                continue
            fb.fill_rect(x, y, size, size, c)
        return z

    sE = math.sin(0.17)
    cD, sD = math.cos(DISK_TILT), math.sin(DISK_TILT)
    for p in em.parts:
        other = p[6] & PF_OTHER
        ox = oxOther if other else oxMine
        sph = -sgn if other else sgn
        spx, spy = p[0] + p[3] * 0.5, p[1] + p[3] * 0.5
        sFront = not (p[6] & PF_BACK)
        dp = clampf((spx - ox) / (W * 0.5), -1.0, 1.0) * sph
        delay = (1.0 - dp) * 0.5
        mi = smoothstepf(0.0, 1.0, m * 1.7 - delay * 0.7)
        if mi <= 0.0:
            if sFront:
                p[6] |= PF_FRONT
            continue
        rdn = DISK_INNER + (DISK_OUTER - DISK_INNER) * (p[4] / 255.0)
        omega = 1.3 / (rdn * math.sqrt(rdn))
        jitter = (hash01(p[4] * 256 + p[5]) - 0.5) * 0.10
        th = p[5] * (TWO_PI / 256.0) - tShared * omega
        ct, st = math.cos(th), math.sin(th)
        rpx = rdn * Rh
        dzp = -rpx * st
        dFront = dzp < 0
        front = sFront if mi < 0.5 else dFront
        drawLens = (not dFront) and mi > 0.05 and hR > 2.0
        ux = rpx * ct
        uy = dzp * sE + jitter * Rh
        vx = ux * cD + uy * sD
        vy = -ux * sD + uy * cD
        dpx, dpy = hcx + vx, hcy - vy
        k = (rdn - DISK_INNER) / (DISK_OUTER - DISK_INNER)
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
            rr = ra + (rb - ra) * mi
            rr *= 1.0 - STREAM_DIP * math.sin(PI * mi)
            if rr < hR * 1.08: rr = hR * 1.08
            a_ = aa + dth * mi
            px, py = hcx + rr * math.cos(a_), hcy - rr * math.sin(a_)
        drawn = False
        if -2 <= px <= W + 1 and -2 <= py <= H + 1:
            er, eg, eb = unpack(p[2])
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
                ex, ey = px - hcx, py - hcy
                hidden = ex * ex + ey * ey < hR * hR
            if not hidden:
                c = pack(cr, cg, cb)
                size = 2 if (front or mi > 0.5) else 1
                if front:
                    p[0], p[1], p[2], p[3] = int(px), int(py), c, size
                    p[6] |= PF_FRONT
                else:
                    fb.fill_rect(int(px), int(py), size, size, c)
                drawn = True
        if not drawn:
            p[6] &= ~PF_FRONT
        if drawLens:
            far = dzp / rpx
            lb = smoothstepf(0.4, 1.0, mi) * 0.90 * (1.0 - 0.5 * k) * doppler
            lr = hR * (1.10 + 0.40 * k)
            ax, ay = ct * lr, far * lr * 1.04
            lx, ly = hcx + ax * cD + ay * sD, hcy - (-ax * sD + ay * cD)
            fb.fill_rect(int(lx), int(ly), 2, 1, pack(hr * lb, hg * lb, hb * lb))
            lr2 = hR * (1.06 + 0.12 * k)
            bx, by = ct * lr2, -far * lr2
            l2x, l2y = hcx + bx * cD + by * sD, hcy - (-bx * sD + by * cD)
            lb2 = lb * 0.40
            fb.plot(int(l2x), int(l2y), pack(hr * lb2, hg * lb2, hb * lb2))
    if m > 0.01:
        fb.fill_circle(hcx, hcy, hR * 1.05, pack(0.95 * m, 0.90 * m, 0.80 * m))
        fb.fill_circle(hcx, hcy, hR, (0, 0, 0))
    for x, y, c, size, u, a, fl in em.parts:
        if fl & PF_FRONT:
            fb.fill_rect(x, y, size, size, c)
    return z


FONT = {  # 3x5 glyphs for the scale bar label
    '0': (7,5,5,5,7), '1': (2,6,2,2,7), '2': (7,1,7,4,7), '3': (7,1,7,1,7), '4': (5,5,7,1,1),
    '5': (7,4,7,1,7), '6': (7,4,7,5,7), '7': (7,1,1,1,1), '8': (7,5,7,5,7), '9': (7,5,7,1,7),
    '.': (0,0,0,0,2), 'A': (2,5,7,5,5), 'K': (5,5,6,5,5), 'M': (5,7,7,5,5), 'U': (5,5,5,5,7),
    'Y': (5,5,2,2,2), 'L': (4,4,4,4,7),
}


def draw_text(fb, x, y, s, c):
    for ch in s:
        g = FONT.get(ch)
        if g:
            for row in range(5):
                for col in range(3):
                    if g[row] & (4 >> col):
                        fb.plot(x + col, y + row, c)
        x += 4


def draw_scale_bar(fb, ppm, alpha):
    if alpha <= 0.02:
        return
    widthM = W / ppm
    if widthM < 2e9:    unitM, unit = 1e3, "KM"
    elif widthM < 2e15: unitM, unit = AU, "AU"
    else:               unitM, unit = LY, "LY"
    maxLen = 70.0 / (ppm * unitM)
    p = 10.0 ** math.floor(math.log10(maxLen))
    v = 5 * p if maxLen >= 5 * p else (2 * p if maxLen >= 2 * p else p)
    length = int(v * unitM * ppm)
    if v >= 1.0:   label = "%d %s" % (int(v + 0.5), unit)
    elif v >= 0.1: label = "0.%d %s" % (int(v * 10 + 0.5), unit)
    else:          label = "0.0%d %s" % (int(v * 100 + 0.5), unit)
    c = pack(0.70 * alpha, 0.72 * alpha, 0.78 * alpha)
    fb.fill_rect(3, H - 4, length + 1, 1, c)
    fb.fill_rect(3, H - 6, 1, 3, c)
    fb.fill_rect(3 + length, H - 6, 1, 3, c)
    draw_text(fb, 3, H - 12, label, c)


def pair(em, stars, glowL, glowR, P, phase, tShared=7.0):
    L, Rb = FB(), FB()
    render(L, em, stars, glowL, P, 1.0, 3.0, tShared, phase)
    z = render(Rb, em, stars, glowR, P, -1.0, 3.0, tShared, phase)
    for fb in (L, Rb):
        draw_scale_bar(fb, z["ppm"], z["env"] * (1.0 - clampf(P / MERGE_START, 0.0, 1.0)))
    return compose_pair(L, Rb, int(GAP_PX)), z


def main(*args):
    dots, stars, galaxy, near = build_scene()
    em = Emitter(dots, galaxy, near)
    glowL, glowR = build_glow(1.0), build_glow(-1.0)
    if args:
        ph = float(args[0])
        img, z = pair(em, stars, glowL, glowR, 0.0, ph)
        out = "reference/zoom-at-%.2f.png" % ph
        img.save(out)
        print("wrote", out, "logW=%.2f days=%.1f" % (z["logW"], z["days"]))
        return
    pairs = []
    for ph in (0.01, 0.08, 0.14, 0.21, 0.29, 0.37, 0.45, 0.52, 0.60, 0.70, 0.82, 0.94):
        img, z = pair(em, stars, glowL, glowR, 0.0, ph)
        print("phase %.2f  %4.1f min  logW %5.2f  days %9.1f  parts %d" % (ph, ph * ZOOM_MINUTES, z["logW"], z["days"], len(em.parts)))
        pairs.append(img)
    compose_strip(pairs, per_row=4).save("reference/zoom-cycle-preview.png")
    merges = []
    for ph in (0.03, 0.29, 0.92):
        for dbm in (-18.0, -15.5, -13.0):
            P = clampf((dbm - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR), 0.0, 1.0)
            merges.append(pair(em, stars, glowL, glowR, P, ph)[0])
    compose_strip(merges, per_row=3).save("reference/zoom-merge-preview.png")
    print("wrote reference/zoom-cycle-preview.png and reference/zoom-merge-preview.png")


if __name__ == "__main__":
    main(*sys.argv[1:])
