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

// Signal strength (dBm) that counts as "far apart" and "touching".
// Turn on the debug overlay (BOOT button) to read live values, then adjust.
const float RSSI_FAR  = -62.0f;
const float RSSI_NEAR = -28.0f;

// Low transmit power makes the signal strength change more over short (desk-scale) distances.
const wifi_power_t TX_POWER = WIFI_POWER_2dBm;

const uint8_t ESPNOW_CHANNEL = 1;

// Sphere look
const float SPHERE_RADIUS = 40.0f;   // pixels
const int   RINGS         = 34;      // latitude rows of dots

// ================================================================================

constexpr int W = tqt::W, H = tqt::H;
static uint16_t fb[W * H];           // framebuffer, byte-swapped RGB565

const int PIN_BTN_BOOT = 0;
const int PIN_BTN_KEY  = 47;

// ---------- sphere points ----------
struct Dot { float x, y, z, hue; };
const int MAX_DOTS = 2000;
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

static void buildSphere() {
  numDots = 0;
  for (int r = 0; r < RINGS && numDots < MAX_DOTS; r++) {
    float lat = PI * ((r + 0.5f) / RINGS) - HALF_PI;     // -90..90 deg
    float cl = cosf(lat), sl = sinf(lat);
    int count = max(1, (int)roundf(2.0f * RINGS * cl));
    for (int k = 0; k < count && numDots < MAX_DOTS; k++) {
      float lon = TWO_PI * (k + 0.5f * (r & 1)) / count;
      Dot &d = dots[numDots++];
      d.x = cl * cosf(lon);
      d.y = sl;
      d.z = cl * sinf(lon);
      d.hue = 0.42f * d.y + 0.25f * d.x + 0.12f * d.z;  // diagonal rainbow across the sphere
    }
  }
}

static void renderSphere(float t, float dt) {
  memset(fb, 0, sizeof(fb));

  const float P = prox;
  const float s = sideSmooth;
  const float cx = W * 0.5f + s * P * 9.0f;             // drift toward the other board
  const float cy = H * 0.5f;
  const float R  = SPHERE_RADIUS * (1.0f + 0.025f * sinf(t * 1.7f) * (0.4f + P));

  rotY += dt * (0.55f + 1.6f * P);                      // spins faster when close
  const float cR = cosf(rotY), sR = sinf(rotY);
  const float tilt = 0.42f;
  const float cT = cosf(tilt), sT = sinf(tilt);

  for (int pass = 0; pass < 2; pass++) {                // back half first, then front half
    for (int i = 0; i < numDots; i++) {
      const Dot &d = dots[i];
      // rotate around Y, then tilt around X
      float x1 = d.x * cR + d.z * sR;
      float z1 = -d.x * sR + d.z * cR;
      float y2 = d.y * cT - z1 * sT;
      float z2 = d.y * sT + z1 * cT;
      float x2 = x1;
      bool front = z2 >= 0;
      if (front != (pass == 1)) continue;

      // deform toward the peer (screen-space x)
      float dp = x2 * s;                                 // +1 = facing the other board
      float reach = dp > 0 ? dp * dp * dp : 0.0f;
      float back  = dp < 0 ? -dp : 0.0f;
      float wob   = 0.04f * P * sinf(7.0f * d.y + 5.0f * t + 3.0f * d.x);
      float r     = 1.0f + P * (0.95f * reach - 0.10f * back) + wob;
      float pinch = 1.0f - 0.30f * P * reach;            // narrow the reaching lobe

      float X = x2 * r, Y = y2 * r * pinch, Z = z2 * r * pinch;
      float persp = 3.2f / (3.2f - Z);
      int sx = (int)(cx + X * R * persp);
      int sy = (int)(cy - Y * R * persp);

      float h  = d.hue + hueBase + 0.04f * t + 0.20f * P * reach;
      float br = front ? 0.55f + 0.45f * z2 : 0.10f + 0.22f * (1.0f + z2);
      br *= 0.85f + 0.30f * P;
      uint16_t c = hsv565(h, 0.95f, br);

      if (front) fillRect(sx, sy, 2, 2, c);
      else       plot(sx, sy, c);
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
