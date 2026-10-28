# LilyGo official shell for the T-QT Pro — vendor reference

Screenshots of LilyGo's own retail listing for the stock plastic shell, kept as
reference for the custom case in `case/`. **Not our design** — this is the
vendor part, for comparison and for the features their shell gets right.

| File | View |
|---|---|
| `lilygo-tqt-pro-official-shell-front-2026-10-27.png` | Straight-on front |
| `lilygo-tqt-pro-official-shell-angled-buttons-usb-2026-10-27.png` | Three-quarter front, shows button ledge and USB side |
| `lilygo-tqt-pro-official-shell-rear-pin-slots-2026-10-27.png` | Rear, shows header slots and connector openings |

## Product identification (verbatim from the listing)

- **Title:** LILYGO T-QT PRO ESP32-S3 TTGO Development Board (ESP32-S3FN4R2 Wth Shell)
- **Display:** 0.85 inch **GC9107** TFT IPS LCD
- **MCU / variant shown:** ESP32-S3FN4R2 (4 MB flash, 2 MB PSRAM, per the FN4R2 part code)
- **Variants on the listing:** `...4R2 Solder`, `ESP32-S3FN4R2 Wth Shell` (selected),
  and a third (truncated). A line above reads "Last purchased Oct 13, 2026 —
  ESP32-S3FN4R2 **Non-Solder Pin**", i.e. the previously ordered variant was the
  non-solder-pin one.

**This confirms the board is the T-QT Pro**, which matches `tqt_display.h` in every
sketch here and the `tqt_pro_case.*` filenames in `case/`. The display controller is
GC9107 at 0.85 in — treat 128×128 as the panel geometry unless the driver header says
otherwise. It is **not** the taller rectangular T-Display-class board shown in the
TikTok reference one directory up; that one has a different aspect ratio and a
different controller, so geometry constants from that video do not port directly.

## Shell features visible in the images

Front:
- Two-piece molded plastic shell, rounded rectangle, matte black. Material is not
  stated on the listing.
- Rectangular display window, with a white `LILYGO®` label strip on the bezel
  directly above the window.
- Below the display, a recessed ledge carrying **two square face buttons**
  (the board's BOOT/IO0 and reset buttons, brought out through the shell).
- USB-C opening on one **long side** (visible in the angled shot), not the end.

Rear:
- Two vertical columns of square cut-outs, roughly 7 per side, aligned with the
  board's pin headers — the shell leaves the header pins accessible without
  opening it.
- Small circular opening near the top-left corner.
- Two round holes at the bottom-left.
- A rectangular opening at bottom-center exposing a white JST-style connector on
  the PCB (battery connector on this board).

## Not available from these images

No dimensions, wall thickness, screw/boss positions, tolerances, or material spec —
the listing photos carry none of that. Anything dimensional for `case/tqt_pro_case.scad`
still has to come from calipers on the actual board, or from LilyGo's published
mechanical drawing / STEP if one exists.

Source: vendor retail listing, screenshotted 2026-10-27.
