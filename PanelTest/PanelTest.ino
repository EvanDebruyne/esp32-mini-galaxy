// PanelTest — finds which screen version your T-QT Pro has.
//
// Cycles through 6 test configs, 3 seconds each, forever:
//   1 bar  = panel V1, backlight LOW      4 bars = panel V1, backlight HIGH
//   2 bars = panel V2, backlight LOW      5 bars = panel V2, backlight HIGH
//   3 bars = panel V3, backlight LOW      6 bars = panel V3, backlight HIGH
//
// Watch the screen and note the bar count (and colour) that shows a clean picture:
// solid background colour with white horizontal bars. The Serial Monitor (115200)
// prints which config is showing at each moment.
//
// Then in ProximitySpheres.ino set PANEL_VERSION and BACKLIGHT_ON to match.

#include <Arduino.h>
#include <SPI.h>
#include "tqt_display.h"

static inline uint16_t be(uint16_t c) { return (uint16_t)((c << 8) | (c >> 8)); }

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\nPanelTest starting");
}

void loop() {
  const int blLevels[2] = {LOW, HIGH};
  const uint16_t bg[3] = {0xF800 /*red*/, 0x07E0 /*green*/, 0x001F /*blue*/};
  int config = 1;
  for (int b = 0; b < 2; b++) {
    for (int panel = 1; panel <= 3; panel++, config++) {
      Serial.printf("Config %d: %d bar(s)  ->  PANEL_VERSION %d, BACKLIGHT_ON %s  (background should be %s)\n",
                    config, config, panel, blLevels[b] == LOW ? "LOW" : "HIGH",
                    panel == 1 ? "red" : panel == 2 ? "green" : "blue");
      tqt::begin(panel, blLevels[b]);
      tqt::fillRaw(be(bg[panel - 1]), config, 0xFFFF);
      delay(3000);
    }
  }
}
