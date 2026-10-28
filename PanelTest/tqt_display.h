// tqt_display.h — tiny self-contained driver for the LilyGO T-QT Pro 0.85" 128x128 LCD.
//
// No display library needed. Pins, init sequences and offsets come from LilyGO's own
// T-QT repo (extras/old_panel + extras/new_panel). LilyGO has shipped three different
// panels on this board, so pick the right one with PANEL_VERSION in ProximitySpheres.ino
// (run the PanelTest sketch to find out which one you have).
#pragma once
#include <Arduino.h>
#include <SPI.h>

namespace tqt {

constexpr int PIN_MOSI = 2;
constexpr int PIN_SCLK = 3;
constexpr int PIN_CS   = 5;
constexpr int PIN_DC   = 6;
constexpr int PIN_RST  = 1;
constexpr int PIN_BL   = 10;   // backlight is ACTIVE LOW on this board

constexpr int W = 128;
constexpr int H = 128;
constexpr int COL_OFS = 2;     // panel RAM offset for rotation 0 (same on both panels)
constexpr int ROW_OFS = 1;

constexpr uint32_t SPI_HZ = 40000000;

// Init tables: {command, count, data...}. count | 0x80 => delay 120 ms after the command.
// (Length-based: no end marker, because 0xFF is a real command on one panel.)
constexpr uint8_t DELAY_FLAG = 0x80;

// Newer panel ("LilyGo Version 3 20260310 new panel")
static const uint8_t INIT_V3[] = {
  0x11, 0 | DELAY_FLAG,
  0xB1, 3, 0x05, 0x3C, 0x3C,
  0xB2, 3, 0x05, 0x3C, 0x3C,
  0xB3, 6, 0x05, 0x3C, 0x3C, 0x05, 0x3C, 0x3C,
  0xB4, 1, 0x03,
  0xC0, 3, 0xAB, 0x0B, 0x04,
  0xC1, 1, 0xC5,
  0xC2, 2, 0x0D, 0x00,
  0xC3, 2, 0x8D, 0x6A,
  0xC4, 2, 0x8D, 0xEE,
  0xC5, 1, 0x0F,
  0xE0, 16, 0x07, 0x0E, 0x08, 0x07, 0x10, 0x07, 0x02, 0x07,
            0x09, 0x0F, 0x25, 0x36, 0x00, 0x08, 0x04, 0x10,
  0xE1, 16, 0x0A, 0x0D, 0x08, 0x07, 0x0F, 0x07, 0x02, 0x07,
            0x09, 0x0F, 0x25, 0x35, 0x00, 0x09, 0x04, 0x10,
  0xFC, 1, 0x80,
  0x3A, 1, 0x05,          // 16-bit colour
  0x21, 0,                // inversion on
  0x29, 0,                // display on
};

// Older panel ("LilyGo version 2")
static const uint8_t INIT_V2[] = {
  0xFE, 0,
  0xEF, 0,
  0xB0, 1, 0xC0,
  0xB1, 1, 0x80,
  0xB2, 1, 0x27,
  0xB3, 1, 0x13,
  0xB6, 1, 0x19,
  0xB7, 1, 0x05,
  0xAC, 1, 0xC8,
  0xAB, 1, 0x0F,
  0x3A, 1, 0x05,          // 16-bit colour
  0xB4, 1, 0x04,
  0xA8, 1, 0x08,
  0xB8, 1, 0x08,
  0xEA, 1, 0x02,
  0xE8, 1, 0x2A,
  0xE9, 1, 0x47,
  0xE7, 1, 0x5F,
  0xC6, 1, 0x21,
  0xC7, 1, 0x15,
  0xF0, 14, 0x1D, 0x38, 0x09, 0x4D, 0x92, 0x2F, 0x35, 0x52, 0x1E, 0x0C, 0x04, 0x12, 0x14, 0x1F,
  0xF1, 14, 0x16, 0x40, 0x1C, 0x54, 0xA9, 0x2D, 0x2E, 0x56, 0x10, 0x0D, 0x0C, 0x1A, 0x14, 0x1E,
  0xF4, 3, 0x00, 0x00, 0xFF,
  0xBA, 2, 0xFF, 0xFF,
  0x20, 0,                // inversion off
  0x11, 0 | DELAY_FLAG,   // sleep out
  0x29, 0,                // display on
};

// Original panel ("LilyGo version 1" — also what the Arduino_GFX library uses for T-QT Pro)
static const uint8_t INIT_V1[] = {
  0xEF, 0,
  0xEB, 1, 0x14,
  0xFE, 0,
  0xEF, 0,
  0xEB, 1, 0x14,
  0x84, 1, 0x40,
  0x85, 1, 0xFF,
  0x86, 1, 0xFF,
  0x87, 1, 0xFF,
  0x88, 1, 0x0A,
  0x89, 1, 0x21,
  0x8A, 1, 0x00,
  0x8B, 1, 0x80,
  0x8C, 1, 0x01,
  0x8D, 1, 0x01,
  0x8E, 1, 0xFF,
  0x8F, 1, 0xFF,
  0xB6, 2, 0x00, 0x20,
  0x3A, 1, 0x05,          // 16-bit colour
  0x90, 4, 0x08, 0x08, 0x08, 0x08,
  0xBD, 1, 0x06,
  0xBC, 1, 0x00,
  0xFF, 3, 0x60, 0x01, 0x04,
  0xC3, 1, 0x13,
  0xC4, 1, 0x13,
  0xC9, 1, 0x22,
  0xBE, 1, 0x11,
  0xE1, 2, 0x10, 0x0E,
  0xDF, 3, 0x21, 0x0C, 0x02,
  0xF0, 6, 0x45, 0x09, 0x08, 0x08, 0x26, 0x2A,
  0xF1, 6, 0x43, 0x70, 0x72, 0x36, 0x37, 0x6F,
  0xF2, 6, 0x45, 0x09, 0x08, 0x08, 0x26, 0x2A,
  0xF3, 6, 0x43, 0x70, 0x72, 0x36, 0x37, 0x6F,
  0xED, 2, 0x1B, 0x0B,
  0xAE, 1, 0x77,
  0xCD, 1, 0x63,
  0x70, 9, 0x07, 0x07, 0x04, 0x0E, 0x0F, 0x09, 0x07, 0x08, 0x03,
  0xE8, 1, 0x34,
  0x62, 12, 0x18, 0x0D, 0x71, 0xED, 0x70, 0x70, 0x18, 0x0F, 0x71, 0xEF, 0x70, 0x70,
  0x63, 12, 0x18, 0x11, 0x71, 0xF1, 0x70, 0x70, 0x18, 0x13, 0x71, 0xF3, 0x70, 0x70,
  0x64, 7, 0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07,
  0x66, 10, 0x3C, 0x00, 0xCD, 0x67, 0x45, 0x45, 0x10, 0x00, 0x00, 0x00,
  0x67, 10, 0x00, 0x3C, 0x00, 0x00, 0x00, 0x01, 0x54, 0x10, 0x32, 0x98,
  0x74, 7, 0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00,
  0x98, 2, 0x3E, 0x07,
  0x35, 0,
  0x21, 0,                // inversion on
  0x11, 0 | DELAY_FLAG,   // sleep out
  0x29, 0 | DELAY_FLAG,   // display on
};

static const SPISettings spiSettings(SPI_HZ, MSBFIRST, SPI_MODE0);

inline void writeCmd(uint8_t c) {
  digitalWrite(PIN_DC, LOW);
  SPI.write(c);
  digitalWrite(PIN_DC, HIGH);
}

inline void runTable(const uint8_t *t, size_t len) {
  const uint8_t *endp = t + len;
  while (t + 1 < endp) {
    uint8_t c = *t++;
    uint8_t n = *t++;
    bool wait = n & DELAY_FLAG;
    n &= ~DELAY_FLAG;
    writeCmd(c);
    while (n-- && t < endp) SPI.write(*t++);
    if (wait) delay(120);
  }
}

// panelVersion: 1, 2 or 3.  blOn: level that turns the backlight ON (LOW on the T-QT Pro).
inline void begin(int panelVersion, int blOn = LOW) {
  pinMode(PIN_BL, OUTPUT);
  digitalWrite(PIN_BL, !blOn);         // backlight off while we init
  pinMode(PIN_CS, OUTPUT);
  digitalWrite(PIN_CS, HIGH);
  pinMode(PIN_DC, OUTPUT);
  digitalWrite(PIN_DC, HIGH);
  pinMode(PIN_RST, OUTPUT);

  static bool spiStarted = false;
  if (!spiStarted) { SPI.begin(PIN_SCLK, -1, PIN_MOSI, -1); spiStarted = true; }

  // hardware reset only (same as LilyGO's TFT_eSPI — no software reset command)
  digitalWrite(PIN_RST, HIGH); delay(10);
  digitalWrite(PIN_RST, LOW);  delay(50);
  digitalWrite(PIN_RST, HIGH); delay(150);

  SPI.beginTransaction(spiSettings);
  digitalWrite(PIN_CS, LOW);
  if (panelVersion == 1)      runTable(INIT_V1, sizeof(INIT_V1));
  else if (panelVersion == 2) runTable(INIT_V2, sizeof(INIT_V2));
  else                        runTable(INIT_V3, sizeof(INIT_V3));
  writeCmd(0x36); SPI.write(0x08);     // MADCTL: rotation 0, BGR (matches LilyGO's rotation file)
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();

  digitalWrite(PIN_BL, blOn);          // backlight on
}

// Fill the panel's ENTIRE internal memory (132x162) with one colour, ignoring offsets.
// Useful for testing: if anything works at all, the whole visible screen changes colour.
inline void fillRaw(uint16_t colorBE, int barCount = 0, uint16_t barBE = 0xFFFF) {
  static uint16_t line[132];
  SPI.beginTransaction(spiSettings);
  digitalWrite(PIN_CS, LOW);
  writeCmd(0x2A); SPI.write(0); SPI.write(0); SPI.write(0); SPI.write(131);
  writeCmd(0x2B); SPI.write(0); SPI.write(0); SPI.write(0); SPI.write(161);
  writeCmd(0x2C);
  for (int y = 0; y < 162; y++) {
    // barCount horizontal white bars across the middle 128 rows, so you can count them
    bool bar = false;
    if (barCount > 0 && y >= 17 && y < 145) {
      int slot = (y - 17) * (barCount * 2 + 1) / 128;
      bar = (slot & 1) == 1;
    }
    for (int x = 0; x < 132; x++) line[x] = bar ? barBE : colorBE;
    SPI.writeBytes((const uint8_t *)line, sizeof(line));
  }
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

// Push a full 128x128 frame. Pixels must already be byte-swapped (big-endian RGB565).
inline void pushFrame(const uint16_t *fb) {
  SPI.beginTransaction(spiSettings);
  digitalWrite(PIN_CS, LOW);
  writeCmd(0x2A);
  SPI.write(0); SPI.write(COL_OFS); SPI.write(0); SPI.write(COL_OFS + W - 1);
  writeCmd(0x2B);
  SPI.write(0); SPI.write(ROW_OFS); SPI.write(0); SPI.write(ROW_OFS + H - 1);
  writeCmd(0x2C);
  SPI.writeBytes((const uint8_t *)fb, W * H * 2);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

} // namespace tqt
