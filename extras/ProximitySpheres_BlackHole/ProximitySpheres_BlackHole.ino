// ProximitySpheres — two LilyGO T-QT Pro boards, each showing a dotted rainbow sphere.
// Bring the boards together and the spheres stretch toward each other.
//
// How it works: both boards broadcast a tiny ESP-NOW packet ~40x per second (no router,
// no Wi-Fi network, no internet). Each board reads the radio signal strength (RSSI) of the
// other's packets and uses it as a rough distance sensor.
//
// Flash the SAME sketch to both boards. See README.md for Arduino IDE settings.
//
// Buttons:
//   KEY  (right button, IO47) : swap which way the spheres reach (flips BOTH boards)
//   BOOT (left button,  IO0)  : toggle the debug overlay (signal strength + proximity bar)

#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <Preferences.h>
#include "tqt_display.h"

#if !defined(ESP_ARDUINO_VERSION_MAJOR) || ESP_ARDUINO_VERSION_MAJOR < 3
#error "Install 'esp32 by Espressif Systems' version 3.x in Boards Manager (2.x won't work)."
#endif

// ============================ SETTINGS YOU MAY TWEAK ============================

// LilyGO has shipped three different screens on this board: 1, 2 or 3.
// Black/garbled screen? Run the PanelTest sketch once — it tells you which number to use.
#define PANEL_VERSION 3

// Backlight: LOW turns it on for the T-QT Pro. Only change if PanelTest says so.
#define BACKLIGHT_ON LOW

// 1 = turn the image upside down (if the sphere looks upside-down relative to the USB plug)
#define FLIP_SCREEN 0

// Signal strength (dBm) where the effect STARTS and where it's at FULL strength.
// Turn on the debug overlay (BOOT button) to read live values, then adjust.
// Closer to 0 = stronger signal = boards closer. These are set so the effect only
// kicks in when the boards are quite close (roughly within a hand's width).
const float RSSI_FAR  = -42.0f;
const float RSSI_NEAR = -22.0f;

// Low transmit power makes the signal strength change more over short (desk-scale) distances.
const wifi_power_t TX_POWER = WIFI_POWER_2dBm;

const uint8_t ESPNOW_CHANNEL = 1;

// Look
const float SPHERE_RADIUS = 55.0f;   // pixels (screen is 128 wide, so this nearly fills it)
const int   RINGS         = 44;      // latitude rows of dots
const int   NUM_STARS     = 70;      // faint background stars (they get lensed by the black hole)

// ================================================================================

constexpr int W = tqt::W, H = tqt::H;
static uint16_t fb[W * H];           // framebuffer, byte-swapped RGB565

const int PIN_BTN_BOOT = 0;
const int PIN_BTN_KEY  = 47;

// ---------- sphere points ----------
struct Dot {
  float x, y, z, hue;      // sphere position + rainbow hue
  float rd, ang, omega;    // accretion-disk orbit: radius, start angle, angular speed
  float jitter;            // small vertical offset so the disk has some thickness
};
const int MAX_DOTS = 3200;
static Dot dots[MAX_DOTS];
static int numDots = 0;

// ---------- radio link ----------
struct __attribute__((packed)) Packet {
  uint32_t magic;
  uint8_t  version;
  uint8_t  swapCount;
  uint16_t seq;
};
const uint32_t MAGIC = 0x50535154;   // "TQSP"
const uint8_t  BCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static portMUX_TYPE linkMux = portMUX_INITIALIZER_UNLOCKED;
const int RSSI_BUF = 8;
static volatile int8_t   rssiBuf[RSSI_BUF];
static volatile uint32_t rssiCount = 0;
static volatile uint32_t lastRxMs = 0;
static volatile uint8_t  peerSwap = 0;
static uint8_t peerMac[6] = {0};
static uint8_t myMac[6]   = {0};

static uint8_t  mySwap = 0;
static uint16_t txSeq = 0;
static Preferences prefs;

// ---------- animation state ----------
static float rssiFiltered = -100.0f;
static float prox = 0.0f;            // 0 = far, 1 = touching
static float sideSmooth = 1.0f;      // +1 = peer is to the right, -1 = left
static float rotY = 0.0f;
static float swirlExtra = 0.0f;
static float hueBase = 0.0f;
static bool  showDebug = false;

// =================================== helpers ===================================

static inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

static inline uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
  uint16_t c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
  return (uint16_t)((c << 8) | (c >> 8));  // byte-swap for the SPI push
}

static uint16_t hsv565(float h, float s, float v) {
  h -= floorf(h);
  v = clampf(v, 0.0f, 1.0f);
  float hf = h * 6.0f;
  int   i  = (int)hf;
  float f  = hf - i;
  float p = v * (1 - s), q = v * (1 - s * f), t = v * (1 - s * (1 - f));
  float r, g, b;
  switch (i % 6) {
    case 0:  r = v; g = t; b = p; break;
    case 1:  r = q; g = v; b = p; break;
    case 2:  r = p; g = v; b = t; break;
    case 3:  r = p; g = q; b = v; break;
    case 4:  r = t; g = p; b = v; break;
    default: r = v; g = p; b = q; break;
  }
  return rgb565((uint8_t)(r * 255), (uint8_t)(g * 255), (uint8_t)(b * 255));
}

static inline void plot(int x, int y, uint16_t c) {
  if ((unsigned)x >= (unsigned)W || (unsigned)y >= (unsigned)H) return;
#if FLIP_SCREEN
  x = W - 1 - x; y = H - 1 - y;
#endif
  fb[y * W + x] = c;
}

static inline void fillRect(int x, int y, int w, int h, uint16_t c) {
  for (int j = 0; j < h; j++)
    for (int i = 0; i < w; i++) plot(x + i, y + j, c);
}

// 3x5 pixel font for the debug overlay: digits, '-', 'L', 'R'
static const uint8_t FONT3x5[][5] = {
  {7,5,5,5,7}, {2,6,2,2,7}, {7,1,7,4,7}, {7,1,7,1,7}, {5,5,7,1,1},
  {7,4,7,1,7}, {7,4,7,5,7}, {7,1,1,1,1}, {7,5,7,5,7}, {7,5,7,1,7},
  {0,0,7,0,0}, {4,4,4,4,7}, {6,5,6,5,5},
};
static void drawChar(int x, int y, char ch, uint16_t c, int s) {
  int idx;
  if (ch >= '0' && ch <= '9') idx = ch - '0';
  else if (ch == '-') idx = 10;
  else if (ch == 'L') idx = 11;
  else if (ch == 'R') idx = 12;
  else return;
  for (int row = 0; row < 5; row++)
    for (int col = 0; col < 3; col++)
      if (FONT3x5[idx][row] & (4 >> col)) fillRect(x + col * s, y + row * s, s, s, c);
}
static void drawText(int x, int y, const char *str, uint16_t c, int s) {
  for (; *str; str++, x += 4 * s) drawChar(x, y, *str, c, s);
}

// ================================= radio link ==================================

static void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len != (int)sizeof(Packet)) return;
  Packet p;
  memcpy(&p, data, sizeof(p));
  if (p.magic != MAGIC || p.version != 1) return;
  portENTER_CRITICAL(&linkMux);
  memcpy(peerMac, info->src_addr, 6);
  rssiBuf[rssiCount % RSSI_BUF] = (int8_t)info->rx_ctrl->rssi;
  rssiCount++;
  lastRxMs = millis();
  peerSwap = p.swapCount;
  portEXIT_CRITICAL(&linkMux);
}

static void radioBegin() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  WiFi.setTxPower(TX_POWER);
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
  esp_wifi_get_mac(WIFI_IF_STA, myMac);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed");
    return;
  }
  esp_now_register_recv_cb(onRecv);

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, BCAST, 6);
  peer.channel = 0;                  // 0 = current channel
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = false;
  esp_now_add_peer(&peer);
}

static void radioSend() {
  Packet p = {MAGIC, 1, mySwap, txSeq++};
  esp_now_send(BCAST, (const uint8_t *)&p, sizeof(p));
}

// Median of the most recent RSSI samples (kills single-packet spikes)
static float rssiMedian() {
  int8_t s[RSSI_BUF];
  int n;
  portENTER_CRITICAL(&linkMux);
  n = rssiCount < RSSI_BUF ? (int)rssiCount : RSSI_BUF;
  for (int i = 0; i < n; i++) s[i] = rssiBuf[i];
  portEXIT_CRITICAL(&linkMux);
  if (n == 0) return -100;
  for (int i = 1; i < n; i++) {      // insertion sort, n <= 8
    int8_t v = s[i]; int j = i - 1;
    while (j >= 0 && s[j] > v) { s[j + 1] = s[j]; j--; }
    s[j + 1] = v;
  }
  return s[n / 2];
}

// ================================== sphere ====================================

static float hash01(uint32_t n) {                      // cheap repeatable pseudo-random 0..1
  n = (n ^ 61) ^ (n >> 16); n *= 9; n ^= n >> 4; n *= 0x27d4eb2d; n ^= n >> 15;
  return (n & 0xFFFFFF) / 16777216.0f;
}

struct Star { float x, y, b; };
static Star stars[NUM_STARS];

static void buildSphere() {
  numDots = 0;
  for (int r = 0; r < RINGS && numDots < MAX_DOTS; r++) {
    float lat = PI * ((r + 0.5f) / RINGS) - HALF_PI;     // -90..90 deg
    float cl = cosf(lat), sl = sinf(lat);
    int count = max(1, (int)roundf(2.0f * RINGS * cl));
    for (int k = 0; k < count && numDots < MAX_DOTS; k++) {
      float lon = TWO_PI * (k + 0.5f * (r & 1)) / count;
      Dot &d = dots[numDots];
      d.x = cl * cosf(lon);
      d.y = sl;
      d.z = cl * sinf(lon);
      d.hue = 0.42f * d.y + 0.25f * d.x + 0.12f * d.z;  // diagonal rainbow across the sphere
      // accretion disk: each dot keeps its longitude, and the sphere's equator falls to the
      // (dense, white-hot) inner edge while the poles spread to the outer edge. That way the
      // sphere visibly flattens and spirals in instead of scrambling.
      float u = powf(1.0f - cl, 0.6f) + 0.06f * (hash01(numDots * 2 + 1) - 0.5f);
      d.rd = 0.40f + 0.85f * clampf(u, 0.0f, 1.0f);
      d.ang = lon;
      d.omega = 1.0f / (d.rd * sqrtf(d.rd)) - 0.8f;       // inner orbits faster (Kepler-ish)
      d.jitter = (sl >= 0 ? 0.025f : -0.025f) + (hash01(numDots * 2 + 7) - 0.5f) * 0.04f;
      numDots++;
    }
  }
  for (int i = 0; i < NUM_STARS; i++) {
    stars[i].x = hash01(i * 3 + 101) * W;
    stars[i].y = hash01(i * 3 + 202) * H;
    stars[i].b = 0.15f + 0.45f * hash01(i * 3 + 303);
  }
}

static inline float smoothstepf(float a, float b, float x) {
  float t = clampf((x - a) / (b - a), 0.0f, 1.0f);
  return t * t * (3.0f - 2.0f * t);
}

static void hsvToRgb(float h, float s, float v, float &r, float &g, float &b) {
  h -= floorf(h);
  float hf = h * 6.0f; int i = (int)hf; float f = hf - i;
  float p = v * (1 - s), q = v * (1 - s * f), t = v * (1 - s * (1 - f));
  switch (i % 6) {
    case 0: r = v; g = t; b = p; break;  case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;  case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;  default: r = v; g = p; b = q; break;
  }
}

// Accretion-disk palette: 0 = inner edge (white-hot, a little blue) -> 1 = outer edge (deep red)
static void diskColor(float k, float &r, float &g, float &b) {
  k = clampf(k, 0.0f, 1.0f);
  if (k < 0.25f)      { float t = k / 0.25f;          r = 0.85f + 0.15f * t; g = 0.90f - 0.10f * t; b = 1.00f - 0.55f * t; }
  else if (k < 0.6f)  { float t = (k - 0.25f) / 0.35f; r = 1.0f;              g = 0.80f - 0.45f * t; b = 0.45f - 0.38f * t; }
  else                { float t = (k - 0.6f) / 0.4f;   r = 1.0f - 0.45f * t;  g = 0.35f - 0.30f * t; b = 0.07f; }
}

static inline uint16_t pack(float r, float g, float b) {
  return rgb565((uint8_t)(clampf(r, 0, 1) * 255), (uint8_t)(clampf(g, 0, 1) * 255), (uint8_t)(clampf(b, 0, 1) * 255));
}

static void fillCircle(float cx, float cy, float rad, uint16_t c) {
  int r = (int)ceilf(rad);
  float r2 = rad * rad;
  for (int y = -r; y <= r; y++)
    for (int x = -r; x <= r; x++)
      if (x * x + y * y <= r2) plot((int)cx + x, (int)cy + y, c);
}

// The two stages:
//   far        -> big rainbow dot-sphere, slowly turning
//   getting close (P up to ~0.4) -> sphere stretches toward the other board and starts to swirl
//   close      -> sphere collapses into a black hole: dark event horizon, glowing accretion disk,
//                 a lensed halo arcing over the top, background stars warped around it.
static void renderSphere(float t, float dt) {
  memset(fb, 0, sizeof(fb));

  const float P = prox;
  const float s = sideSmooth;
  const float m = smoothstepf(0.30f, 0.85f, P);         // 0 = sphere, 1 = black hole
  const float reachAmt = P * (1.0f - m);                // stretch only before the collapse
  const float cx = W * 0.5f + s * (9.0f * reachAmt + 14.0f * m);  // drift toward the other board
  const float cy = H * 0.5f;
  const float R  = SPHERE_RADIUS * (1.0f + 0.02f * sinf(t * 1.7f) * (1.0f - m));

  rotY += dt * (0.45f + 1.2f * P);
  const float cR = cosf(rotY), sR = sinf(rotY);
  const float tilt = 0.42f;
  const float cT = cosf(tilt), sT = sinf(tilt);

  const float elev = 0.30f;                             // we view the disk from slightly above
  const float cE = cosf(elev), sE = sinf(elev);
  const float horizon = 0.30f * R * m;                  // event-horizon radius in pixels
  const float swirl = t * (0.6f + 1.8f * m);            // photon-ring flicker phase
  swirlExtra += dt * 1.6f * m;                          // extra disk shear builds up as it collapses

  // --- background stars, pushed outward around the hole like gravitational lensing ---
  for (int i = 0; i < NUM_STARS; i++) {
    float dx = stars[i].x - cx, dy = stars[i].y - cy;
    float d2 = dx * dx + dy * dy + 1.0f;
    float push = 1.0f + m * (horizon * horizon * 2.2f) / d2;
    float twinkle = 0.75f + 0.25f * sinf(t * 2.0f + i);
    float v = stars[i].b * twinkle * (0.35f + 0.65f * m);
    plot((int)(cx + dx * push), (int)(cy + dy * push), pack(v, v, v * 1.1f));
  }

  // pass 0: back half (+ lensed halo), pass 1: event horizon + photon ring, pass 2: front half
  for (int pass = 0; pass < 3; pass++) {
    if (pass == 1) {
      if (m > 0.01f) {
        // photon ring: thin flickering bright ring hugging the horizon
        int nRing = 90;
        for (int k = 0; k < nRing; k++) {
          float a = TWO_PI * k / nRing + swirl * 0.3f;
          float rr = horizon * (1.08f + 0.03f * sinf(a * 5.0f + t * 6.0f));
          float v = m * (0.75f + 0.25f * sinf(a * 3.0f - t * 4.0f));
          plot((int)(cx + cosf(a) * rr), (int)(cy + sinf(a) * rr), pack(v, v * 0.85f, v * 0.6f));
        }
        fillCircle(cx, cy, horizon, 0);                 // the hole itself: pure black
      }
      continue;
    }
    for (int i = 0; i < numDots; i++) {
      const Dot &d = dots[i];

      // ---- sphere position (rotate around Y, then tilt around X) ----
      float x1 = d.x * cR + d.z * sR;
      float z1 = -d.x * sR + d.z * cR;
      float sy = d.y * cT - z1 * sT;
      float sz = d.y * sT + z1 * cT;
      float sx = x1;
      // stretch toward the other board while approaching
      float dp = sx * s;
      float reach = dp > 0 ? dp * dp * dp : 0.0f;
      float back  = dp < 0 ? -dp : 0.0f;
      float r = 1.0f + reachAmt * (0.9f * reach - 0.10f * back);
      float pinch = 1.0f - 0.30f * reachAmt * reach;
      sx *= r; sy *= r * pinch; sz *= r * pinch;

      // ---- disk position (orbiting, tilted toward the viewer) ----
      // same angle the dot had on the sphere (lon - rotY), plus extra Keplerian shear
      float th = d.ang - rotY - swirlExtra * d.omega;
      float ct = cosf(th), st = sinf(th);
      float dxp = d.rd * ct, dzp = -d.rd * st;          // dzp > 0 = far side of the disk
      float dx = dxp;
      float dy = dzp * sE + d.jitter;
      float dz = -dzp * cE;

      // ---- blend sphere -> disk; as it collapses, everything also spirals inward ----
      float X = sx + (dx - sx) * m;
      float Y = sy + (dy - sy) * m;
      float Z = sz + (dz - sz) * m;
      bool front = Z >= 0;
      if (front != (pass == 2)) continue;

      float persp = 3.4f / (3.4f - Z);
      int px = (int)(cx + X * R * persp);
      int py = (int)(cy - Y * R * persp);

      // ---- colour: rainbow sphere blends into a white-hot -> red accretion disk ----
      float rr, gg, bb;
      hsvToRgb(d.hue + hueBase + 0.04f * t + 0.25f * reachAmt * reach, 0.95f, 1.0f, rr, gg, bb);
      float hr, hg, hb;
      diskColor((d.rd - 0.40f) / 0.85f, hr, hg, hb);
      // Doppler beaming: the side of the disk moving toward you is brighter
      // (theta decreases over time, so the side with cos(theta) > 0 is coming toward you)
      float doppler = 1.0f + 0.6f * ct;
      float cr = rr + (hr * doppler - rr) * m;
      float cg = gg + (hg * doppler - gg) * m;
      float cb = bb + (hb * doppler - bb) * m;

      float depth = front ? 0.55f + 0.45f * clampf(Z, 0, 1) : 0.12f + 0.25f * (1.0f + clampf(Z, -1, 0));
      float br = depth * (1.0f - m) + m * (front ? 1.0f : 0.8f);
      br *= 0.9f + 0.25f * P;
      // the disk fades a bit toward its outer edge
      br *= 1.0f - 0.45f * m * clampf((d.rd - 0.40f) / 0.85f, 0, 1);
      uint16_t c = pack(cr * br, cg * br, cb * br);

      if (front || m > 0.5f) fillRect(px, py, 2, 2, c);
      else                   plot(px, py, c);

      // ---- lensed image of the FAR side of the disk, bent up over the top of the hole ----
      if (pass == 0 && m > 0.05f && dzp > 0.0f) {
        float lr = horizon * 1.25f + (d.rd - 0.40f) * R * 0.38f;  // radius of the halo arc
        float far = dzp / d.rd;                                    // 0..1, 1 = directly behind
        float lx = cx + ct * lr;
        float ly = cy - far * lr * 1.05f;                          // arc over the top
        float lb = m * 0.75f;
        fillRect((int)lx, (int)ly, 2, 1, pack(hr * lb, hg * lb, hb * lb));
        // faint secondary image under the hole
        float ly2 = cy + far * lr * 0.80f;
        float lb2 = m * 0.30f;
        plot((int)lx, (int)ly2, pack(hr * lb2, hg * lb2, hb * lb2));
      }
    }
  }
}

static void renderDebug(bool linked, float rawRssi) {
  uint16_t white = rgb565(255, 255, 255);
  uint16_t dim   = rgb565(60, 60, 60);
  char buf[8];
  if (linked) snprintf(buf, sizeof(buf), "%d", (int)roundf(rawRssi));
  else        snprintf(buf, sizeof(buf), "---");
  drawText(2, 2, buf, white, 2);
  drawText(W - 8, 2, sideSmooth > 0 ? "R" : "L", white, 2);
  fillRect(W - 14, 4, 4, 4, linked ? rgb565(0, 255, 0) : rgb565(255, 0, 0));
  // proximity bar along the bottom
  fillRect(2, H - 6, W - 4, 4, dim);
  fillRect(2, H - 6, (int)((W - 4) * prox), 4, white);
}

static void bootTest() {
  // Red / green / blue bands with a white border: checks colours, panel version and offsets.
  uint16_t red = rgb565(255, 0, 0), green = rgb565(0, 255, 0), blue = rgb565(0, 0, 255);
  uint16_t white = rgb565(255, 255, 255);
  fillRect(0, 0, W, H / 3, red);
  fillRect(0, H / 3, W, H / 3, green);
  fillRect(0, 2 * H / 3, W, H - 2 * H / 3, blue);
  for (int i = 0; i < W; i++) { plot(i, 0, white); plot(i, H - 1, white); }
  for (int j = 0; j < H; j++) { plot(0, j, white); plot(W - 1, j, white); }
  tqt::pushFrame(fb);
  delay(1200);
}

// =================================== buttons ===================================

struct Button {
  int pin; bool last = true; uint32_t t = 0;
  explicit Button(int p) : pin(p) {}
  bool pressed() {                                     // true once per press
    bool now = digitalRead(pin);
    if (now != last && millis() - t > 40) {
      t = millis(); last = now;
      return now == LOW;
    }
    return false;
  }
};
static Button btnBoot(PIN_BTN_BOOT), btnKey(PIN_BTN_KEY);

// ==================================== main =====================================

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN_BOOT, INPUT_PULLUP);
  pinMode(PIN_BTN_KEY, INPUT_PULLUP);

  tqt::begin(PANEL_VERSION, BACKLIGHT_ON);
  bootTest();

  prefs.begin("spheres", false);
  mySwap = prefs.getUChar("swap", 0);

  radioBegin();
  buildSphere();
  hueBase = (myMac[5] % 32) / 32.0f;                   // each board gets its own colours

  Serial.printf("\nProximitySpheres  panel=V%d  dots=%d  mac=%02X:%02X:%02X:%02X:%02X:%02X\n",
                PANEL_VERSION, numDots, myMac[0], myMac[1], myMac[2], myMac[3], myMac[4], myMac[5]);
}

void loop() {
  static uint32_t lastFrameUs = micros();
  static uint32_t lastTxMs = 0, lastLogMs = 0;

  uint32_t nowUs = micros();
  float dt = clampf((nowUs - lastFrameUs) * 1e-6f, 0.0f, 0.1f);
  lastFrameUs = nowUs;
  float t = millis() * 0.001f;

  if (millis() - lastTxMs >= 25) { lastTxMs = millis(); radioSend(); }

  // buttons
  if (btnKey.pressed()) {
    mySwap++;
    prefs.putUChar("swap", mySwap);
    Serial.println("Swapped reach direction");
  }
  if (btnBoot.pressed()) showDebug = !showDebug;

  // link + proximity
  uint32_t lastRx;
  uint8_t pSwap, pMac[6];
  portENTER_CRITICAL(&linkMux);
  lastRx = lastRxMs; pSwap = peerSwap; memcpy(pMac, peerMac, 6);
  portEXIT_CRITICAL(&linkMux);

  bool linked = lastRx != 0 && (millis() - lastRx) < 800;
  float rawRssi = rssiMedian();
  float target = 0.0f;
  if (linked) {
    float a = 1.0f - expf(-dt * 6.0f);
    rssiFiltered = (rssiFiltered < -99.0f) ? rawRssi : rssiFiltered + (rawRssi - rssiFiltered) * a;
    target = clampf((rssiFiltered - RSSI_FAR) / (RSSI_NEAR - RSSI_FAR), 0.0f, 1.0f);
    target = target * target * (3.0f - 2.0f * target);  // smoothstep
  } else {
    rssiFiltered = -100.0f;
  }
  prox += (target - prox) * (1.0f - expf(-dt * 4.0f));

  // which side is the other board on? Lower MAC = "left" board, so it reaches right.
  // The swap counters from both boards are summed so one button press flips both.
  bool iAmLeft = memcmp(myMac, pMac, 6) < 0;
  bool flipped = ((mySwap + pSwap) & 1) != 0;
  float sideTarget = (iAmLeft != flipped) ? 1.0f : -1.0f;
  sideSmooth += (sideTarget - sideSmooth) * (1.0f - expf(-dt * 5.0f));

  renderSphere(t, dt);
  if (showDebug) renderDebug(linked, rssiFiltered);
  tqt::pushFrame(fb);

  if (millis() - lastLogMs > 500) {
    lastLogMs = millis();
    Serial.printf("linked=%d  rssi=%.1f  prox=%.2f  side=%s  fps=%.0f\n",
                  linked, rssiFiltered, prox, sideSmooth > 0 ? "R" : "L", dt > 0 ? 1.0f / dt : 0.0f);
  }
}
