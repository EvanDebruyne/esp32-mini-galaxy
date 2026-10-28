// =====================================================================
//  LilyGO T-QT Pro (ESP32-S3, 0.85" 128x128 GC9107)  -  snap-fit case
//  Two parts: base + lid.  Parametric OpenSCAD, prints without supports.
//
//  Board frame used everywhere in this file:
//    X = across the board   0 = edge with BOOT(IO0)+RESET, 17.78 = edge with KEY(IO47)
//    Y = along the board    0 = USB-C edge,                 31.6  = antenna end
//    Z = height             0 = PCB underside,              1.0   = PCB top
//
//  Board geometry was taken from LilyGO's own files in
//  https://github.com/Xinyuan-LilyGO/T-QT/tree/main/3D_file
//  (T_QT.DXF = PCB drawing, T_QT_Pro.stp = full 3D model).
//  Anything tagged "CHECK" below was inferred rather than read directly
//  from those files - verify with calipers before printing.
//
//  V4 (2026-10-27): the BOOT and KEY switches are pressed from the TOP (round plunger
//  on top of a 2.75 x 4 x 2.5 mm switch). Like LilyGO's own case, the buttons are a
//  separate third part ("keys"): two caps joined by a thin bar. It is dropped into the
//  lid from the inside, each cap pokes up through a square hole in the lid top, a
//  flange under the lid keeps it in, and a stem under each flange reaches the plunger.
//  Three parts: base, lid, keys.  button_style = "top" gives the V3 flexing paddles,
//  "side" the (wrong) V2 side flaps, "notch" the V1 side notches.
//
//  Printing:  part = "both_for_print"  ->  base upright, lid face-down.
//  Previews:  part = "assembly" / "exploded" show the case with a board mock-up.
// =====================================================================

/* [Part to render] */
part = "assembly"; // [base, lid, keys, both_for_print, assembly, exploded, board]

/* [Print / fit settings] */
wall      = 1.6;   // side wall thickness
floor_t   = 1.6;   // base floor thickness
top_t     = 1.6;   // lid top thickness
clr       = 0.25;  // XY clearance, PCB edge -> cavity wall (PETG: 0.2-0.3)
top_clr   = 0.25;  // Z clearance above the LCD glass / acrylic bracket
bot_clr   = 0.30;  // Z clearance under the lowest underside part (JST-SH socket)
corner_r  = 2.0;   // outer vertical corner radius
$fn = 48;

/* [Snap joint] */
lip_h       = 2.5;   // height of the base lip that enters the lid
lip_t       = 0.8;   // lip thickness (inner part of the wall)
lip_gap     = 0.15;  // clearance between lip and lid skirt
snap_bump   = 0.30;  // how far the catch bumps stand off the lip
snap_len    = 6.0;   // length of each catch bump
snap_ys     = [12.5, 22.5]; // Y positions of the catches (both long sides)
snap_window = true;  // true: through-window in lid skirt (strong, always prints)
                     // false: blind groove -> leaves only ~0.4 mm of skirt, risky
snap_groove_depth = 0.35;

/* [Openings] */
win_w   = 16.4;  // screen window width  (visible area is 16.0, active 15.21)
win_l   = 16.4;  // screen window length
win_r   = 1.0;   // window corner radius
usb_cut_w     = 10.2; // USB-C opening width (receptacle is 8.9)
usb_cut_above = 0.6;  // extra height above the receptacle top
usb_cut_below = 0.5;  // notch depth into the base rim below the receptacle
btn_cut_margin = 0.35; // extra length each side of the button body
btn_cut_above  = 0.40; // extra height above the button body
/* [Buttons] */
button_style = "keycap"; // [keycap, top, side, notch]
plunger_top_z = 3.5;   // top of the switch plunger above the PCB underside  (CHECK: 2.5 mm switch on a 1.0 mm PCB)
stem_gap      = 0.15;  // rest gap between stem and plunger  (CHECK: raise if a button is held down)
// --- V4 separate keycap bridge (third printed part) ---
key_cap_w     = 4.0;   // square cap size (LilyGO's are ~4 mm)
key_hole_w    = 4.4;   // square hole in the lid top (0.2 mm clearance per side)
key_cap_above = 0.8;   // how far the cap stands above the lid top
key_flange_t  = 1.0;   // flange thickness under the lid top
key_flange_out = 0.35; // flange overlap beyond the hole, toward the PCB edge (limited by the cavity wall)
key_flange_in  = 1.0;  // flange overlap toward the board centre
key_flange_y   = 0.6;  // flange overlap along the board
key_stem_w    = 2.2;   // stem under the flange, pressing the plunger
key_bar_w     = 2.0;   // bar joining the two caps
// --- V3 top paddles (only for button_style = "top") ---
stem_w        = 2.4;   // stem cross-section (plunger is ~1.8 round)
top_flap_t    = 0.8;   // paddle thickness (lid top is thinned from the inside)
top_flap_w    = 5.5;   // paddle width along the board (switch body is 4.0)
top_hinge_x   = 8.0;   // paddle hinge line, measured from the BOOT-side PCB edge (mirrored for KEY)
top_slit_w    = 0.5;   // slit width around the paddle
top_cap_d     = 3.4;   // round cap on the outside
top_cap_h     = 0.6;   // cap height above the lid
// --- V2 side flaps (only for button_style = "side") ---
flex_buttons = (button_style == "side");
flap_t    = 0.8;   // flap / hinge thickness (wall is thinned from the inside)
flap_w    = 5.0;   // flap width along the board
slit_w    = 0.5;   // slit width around the flap
flap_gap  = 0.3;   // gap between the flap's free bottom edge and the base rim
nub_w     = 2.0;   // inner nub width (plunger is ~2.4 wide)
nub_gap   = 0.10;  // rest gap between nub tip and plunger tip  (CHECK: raise if a button is held down)
cap_w     = 3.0;   // outer button cap width
cap_h     = 0.8;   // outer button cap height above the wall

/* [Openings] */
reset_hole_d    = 2.4;  // round RESET pin hole, like LilyGO's keyhole
reset_slot_w    = 1.2;  // narrow slit from the hole up to the base rim (keeps it bridge-free)
reset_slot_open = true; // false: round hole only (needs a 2.4 mm bridge)
jst_cutout = false;     // open the end wall for the JST-SH (STEMMA QT) socket too
header_h   = 0;         // 0 = no pin headers. ~8.5 if headers are soldered pointing down  (CHECK)

/* [Board - from LilyGO DXF/STEP] */
pcb_w = 17.78;  pcb_l = 31.6;  pcb_t = 1.0;
pcb_ch_usb = 2.54;   // corner chamfer at the USB end
pcb_ch_ant = 1.06;   // corner chamfer at the antenna end
// LCD glass + visible area (STEP: glass 17.6 x 20.9, top at Z 5.62, 16x16 polarizer recess)
lcd_x0 = 0.11;  lcd_x1 = 17.71;  lcd_y0 = 7.55;  lcd_y1 = 28.45;  lcd_z0 = 3.8;  lcd_top = 5.62;
win_cx = 8.91;  win_cy = 19.65;   // centre of the 16x16 visible area
// clear acrylic (PMMA) bracket under the LCD, with a lip at the antenna end
pm_x0 = 0;  pm_x1 = 17.8;  pm_y0 = 8.45;  pm_y1 = 31.55;  pm_z0 = 2.37;  pm_z1 = 3.62;
pm_tab_y0 = 26.2;  pm_tab2_y0 = 28.7;  pm_tab_y1 = 31.2;
// USB-C receptacle (top side, centred, protrudes 1.0 past the PCB edge)
usb_cx = 8.89;  usb_w = 8.9;  usb_h = 3.26;  usb_len = 7.3;  usb_out = 1.0;
// side tactile switches BOOT (left) / KEY (right): 2.75 x 4.0 x 2.5 mm, plungers point outward
btn_y0 = 2.25;  btn_y1 = 6.25;  btn_h = 2.5;  btn_body_w = 2.75;  btn_inset = 1.0;
btn_plunger_recess = 0.8;   // plunger tip sits this far INSIDE the PCB edge  (CHECK)
// RESET switch, underside of the left edge, plunger pokes 0.35 past the edge
rst_y0 = 3.25;  rst_y1 = 5.0;  rst_z0 = -1.25;  rst_z1 = -0.5;  rst_out = 0.35;
rst_body_x1 = 3.15;  rst_body_z0 = -1.75;
// JST-SH 1.0 mm 4-pin (STEMMA QT) on the underside at the USB end - lowest part of the board
jst_x0 = 5.15;  jst_x1 = 11.15;  jst_y0 = 2.0;  jst_y1 = 6.5;  jst_h = 3.0;
// U.FL antenna jack (underside, antenna end, left) and ESP32-S3 (underside)
ufl_x = 2.4;  ufl_y = 30.0;  ufl_h = 1.45;
esp_x0 = 7.0;  esp_x1 = 14.0;  esp_y0 = 9.0;  esp_y1 = 16.0;  esp_h = 1.0;
// header pad rows (through-holes, flat when no headers fitted)
hdr_x0 = 0.24;  hdr_x1 = 2.28;  hdr_y0 = 7.34;  hdr_y1 = 24.91;

/* [PCB support ledges inside the base] */
ledge_w  = 1.1;   // width from the PCB edge inward (rests on the header pad rows)
ledge_y0 = 7.6;
ledge_y1 = 24.8;

// ---------------------------------------------------------------- derived
split_z = pcb_t;                                   // parting plane = PCB top
lowest  = max(jst_h, header_h);
floor_z = -(lowest + bot_clr);                     // top of the base floor
base_z0 = floor_z - floor_t;                       // bottom of the base
ceil_z  = lcd_top + top_clr;                       // underside of the lid top
lid_z1  = ceil_z + top_t;                          // top of the lid
cav_x0 = -clr;  cav_x1 = pcb_w + clr;  cav_y0 = -clr;  cav_y1 = pcb_l + clr;
out_x0 = cav_x0 - wall;  out_x1 = cav_x1 + wall;  out_y0 = cav_y0 - wall;  out_y1 = cav_y1 + wall;
skirt_t = wall - lip_t - lip_gap;                  // lid skirt thickness
bump_z0 = split_z + 1.1;                           // bottom of the catch bumps
bump_h  = 1.0;
usb_cut_top = pcb_t + usb_h + usb_cut_above;
usb_cut_bot = pcb_t - usb_cut_below;
btn_cut_top = pcb_t + btn_h + btn_cut_above;
rst_cy = (rst_y0 + rst_y1) / 2;
btn_cy = (btn_y0 + btn_y1) / 2;                    // plunger centre along the board (4.25)
btn_cz = pcb_t + btn_h / 2;                        // plunger centre height (2.25)
// Y range the base lip must stay clear of (flap + slits, or the V1 notch)
btn_zone_y0 = flex_buttons ? btn_cy - flap_w / 2 - slit_w : btn_y0 - btn_cut_margin;
btn_zone_y1 = flex_buttons ? btn_cy + flap_w / 2 + slit_w : btn_y1 + btn_cut_margin;
rst_slot_bot = rst_z0 - 0.45;
BIG = 100;

echo(str("Outer size: ", out_x1 - out_x0, " x ", out_y1 - out_y0, " x ", lid_z1 - base_z0,
         " mm   (base ", split_z - base_z0, " + lid ", lid_z1 - split_z, ")  skirt ", skirt_t, " mm"));

// ---------------------------------------------------------------- 2D helpers
module rrect(x0, y0, x1, y1, r) {
    rr = min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01);
    translate([x0 + rr, y0 + rr]) offset(r = rr) square([x1 - x0 - 2 * rr, y1 - y0 - 2 * rr]);
}
module outer_2d()       rrect(out_x0, out_y0, out_x1, out_y1, corner_r);
module cavity_2d()      rrect(cav_x0, cav_y0, cav_x1, cav_y1, max(corner_r - wall, 0.3));
module lip_outer_2d()   rrect(cav_x0 - lip_t, cav_y0 - lip_t, cav_x1 + lip_t, cav_y1 + lip_t,
                              max(corner_r - wall + lip_t, 0.3));
module skirt_inner_2d() rrect(cav_x0 - lip_t - lip_gap, cav_y0 - lip_t - lip_gap,
                              cav_x1 + lip_t + lip_gap, cav_y1 + lip_t + lip_gap,
                              max(corner_r - wall + lip_t + lip_gap, 0.3));

// ---------------------------------------------------------------- cut-outs
// USB-C: through the Y=0 end wall, rounded, from z0 to z1
module usb_cut(z0, z1) {
    translate([0, 2, 0]) rotate([90, 0, 0]) linear_extrude(2 - out_y0 + 1)
        rrect(usb_cx - usb_cut_w / 2, z0, usb_cx + usb_cut_w / 2, z1, 1.2);
}
// side buttons (V1 style): notches through both long walls, from z0 to z1
module button_cuts(z0, z1, y0 = btn_y0 - btn_cut_margin, y1 = btn_y1 + btn_cut_margin) {
    for (x = [out_x0 - 1, cav_x1 - 1])
        translate([x, 0, 0]) rotate([90, 0, 90]) linear_extrude(wall + 2)
            rrect(y0, z0, y1, z1, 0.8);
}
// mirror a left-side feature to the right side
module both_sides() { children(); translate([pcb_w, 0, 0]) mirror([1, 0, 0]) children(); }
// V2 flap: slits on both sides, gap at the bottom, wall thinned to flap_t from the inside
module flap_cut_left() {
    y0 = btn_cy - flap_w / 2;  y1 = btn_cy + flap_w / 2;  h = ceil_z - split_z + 1;
    for (y = [y0 - slit_w, y1]) translate([out_x0 - 1, y, split_z - 1]) cube([wall + 2, slit_w, h]);
    translate([out_x0 - 1, y0 - slit_w, split_z - 1]) cube([wall + 2, flap_w + 2 * slit_w, flap_gap + 1]);
    translate([out_x0 + flap_t, y0 - slit_w, split_z - 1]) cube([wall - flap_t + 1, flap_w + 2 * slit_w, h]);
}
// V2 inner nub: reaches from the flap to just short of the plunger; +Z face sloped 45 deg for face-down printing
module nub_left() {
    tip = btn_plunger_recess - nub_gap;  root = out_x0 + 0.3;
    translate([0, btn_cy + nub_w / 2, 0]) rotate([90, 0, 0]) linear_extrude(nub_w)
        polygon([[root, btn_cz - 0.65], [tip, btn_cz - 0.65], [tip, btn_cz + 0.45], [root, btn_cz + 0.45 + (tip - root)]]);
}
// V3 top paddle (BOOT side): U-slits through the lid top, paddle thinned from the inside
module top_flap_cut_left() {
    y0 = btn_cy - top_flap_w / 2;  y1 = btn_cy + top_flap_w / 2;
    x0 = cav_x0;                                   // outer slit starts at the cavity edge
    translate([x0, y0 - top_slit_w, ceil_z - 1]) cube([top_slit_w, top_flap_w + 2 * top_slit_w, top_t + 3]);   // outer slit
    for (y = [y0 - top_slit_w, y1])
        translate([x0, y, ceil_z - 1]) cube([top_hinge_x - x0, top_slit_w, top_t + 3]);                         // side slits
    translate([x0, y0 - top_slit_w, ceil_z - 1]) cube([top_hinge_x - x0, top_flap_w + 2 * top_slit_w, 1 + top_t - top_flap_t]); // thinning
}
module top_stem_left() {
    cx = btn_inset + btn_body_w / 2;
    translate([cx - stem_w / 2, btn_cy - stem_w / 2, plunger_top_z + stem_gap])
        cube([stem_w, stem_w, lid_z1 - top_flap_t - (plunger_top_z + stem_gap) + 0.01]);
}
module top_cap_left() {
    cx = btn_inset + btn_body_w / 2;
    translate([cx, btn_cy, lid_z1 - 0.01]) cylinder(d = top_cap_d, h = top_cap_h + 0.01);
}
// V4 keycap bridge: square holes in the lid top ...
key_cx_l = btn_inset + btn_body_w / 2;          // BOOT switch centre X (2.375); KEY is mirrored
module key_hole_left() {
    translate([key_cx_l - key_hole_w / 2, btn_cy - key_hole_w / 2, ceil_z - 1]) linear_extrude(top_t + 2)
        rrect(0, 0, key_hole_w, key_hole_w, 0.6);
}
// ... and the loose part itself, in board coordinates (at rest: flange touching the lid underside)
module key_half_left() {
    fx0 = key_cx_l - key_hole_w / 2 - key_flange_out;  fx1 = key_cx_l + key_hole_w / 2 + key_flange_in;
    fy0 = btn_cy - key_hole_w / 2 - key_flange_y;      fy1 = btn_cy + key_hole_w / 2 + key_flange_y;
    translate([fx0, fy0, ceil_z - key_flange_t]) cube([fx1 - fx0, fy1 - fy0, key_flange_t]);             // flange
    translate([key_cx_l - key_cap_w / 2, btn_cy - key_cap_w / 2, ceil_z - 0.01]) linear_extrude(top_t + key_cap_above + 0.01)
        rrect(0, 0, key_cap_w, key_cap_w, 0.5);                                                            // cap
    translate([key_cx_l - key_stem_w / 2, btn_cy - key_stem_w / 2, plunger_top_z + stem_gap])
        cube([key_stem_w, key_stem_w, ceil_z - key_flange_t - plunger_top_z - stem_gap + 0.01]);           // stem
}
module keys() {
    both_sides() key_half_left();
    translate([key_cx_l, btn_cy - key_bar_w / 2, ceil_z - key_flange_t]) cube([pcb_w - 2 * key_cx_l, key_bar_w, key_flange_t]); // bar
}
// V2 outer cap on the flap, same 45 deg rule
module cap_left() {
    translate([0, btn_cy + cap_w / 2, 0]) rotate([90, 0, 0]) linear_extrude(cap_w)
        polygon([[out_x0 + 0.01, btn_cz - 1.2], [out_x0 - cap_h, btn_cz - 1.2], [out_x0 - cap_h, btn_cz + 1.2 - cap_h], [out_x0 + 0.01, btn_cz + 1.2]]);
}
// RESET: keyhole in the left wall of the base - round pin hole at the plunger, slit up to the rim
module reset_cut() {
    rst_cz = (rst_z0 + rst_z1) / 2;
    translate([out_x0 - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(wall + 2) {
        translate([rst_cy, rst_cz]) circle(d = reset_hole_d);
        if (reset_slot_open) translate([rst_cy - reset_slot_w / 2, rst_cz]) square([reset_slot_w, BIG]);
    }
}
// JST-SH: opening in the USB end wall, merged with the USB notch above it
module jst_cut() {
    translate([0, 2, 0]) rotate([90, 0, 0]) linear_extrude(2 - out_y0 + 1)
        rrect(jst_x0 - 0.5, floor_z - 0.01, jst_x1 + 0.5, usb_cut_bot + 1, 0.8);
}
// screen window through the lid top
module window_cut() {
    translate([0, 0, ceil_z - 1]) linear_extrude(top_t + 2)
        rrect(win_cx - win_w / 2, win_cy - win_l / 2, win_cx + win_w / 2, win_cy + win_l / 2, win_r);
}

// ---------------------------------------------------------------- snap features
// catch bump profile: flat underside (catch), ramped top (lead-in). +x = outward.
module bump_profile() {
    polygon([[-0.01, bump_z0], [snap_bump, bump_z0], [snap_bump, bump_z0 + 0.35], [-0.01, bump_z0 + bump_h]]);
}
module snap_bumps() {
    for (y = snap_ys) {
        // right side (+x outward)
        translate([cav_x1 + lip_t, y + snap_len / 2, 0]) rotate([90, 0, 0]) linear_extrude(snap_len) bump_profile();
        // left side (mirrored)
        translate([cav_x0 - lip_t, y + snap_len / 2, 0]) mirror([1, 0, 0]) rotate([90, 0, 0]) linear_extrude(snap_len) bump_profile();
    }
}
module snap_recesses() {
    zl = bump_z0 - 0.15;  zh = bump_z0 + bump_h + 0.3;
    depth = snap_window ? wall + 1 : snap_groove_depth;
    for (y = snap_ys) {
        // right skirt: inner face at cav_x1 + lip_t + lip_gap
        translate([cav_x1 + lip_t + lip_gap - 0.5, y - snap_len / 2 - 0.3, zl])
            cube([depth + 0.5, snap_len + 0.6, zh - zl]);
        // left skirt
        translate([cav_x0 - lip_t - lip_gap - depth, y - snap_len / 2 - 0.3, zl])
            cube([depth + 0.5, snap_len + 0.6, zh - zl]);
    }
}

// ---------------------------------------------------------------- BASE
module base() {
    difference() {
        union() {
            translate([0, 0, base_z0]) linear_extrude(split_z - base_z0) outer_2d();
            translate([0, 0, split_z - 0.01]) linear_extrude(lip_h + 0.01) lip_outer_2d();
            snap_bumps();
        }
        translate([0, 0, floor_z]) linear_extrude(BIG) cavity_2d();   // cavity
        usb_cut(usb_cut_bot, BIG);                                      // USB notch (lower part)
        button_cuts(split_z - 0.01, BIG, btn_zone_y0, btn_zone_y1);     // keep the lip clear of the plungers / flaps
        reset_cut();
        if (jst_cutout) jst_cut();
    }
    // PCB support ledges (only when no headers are fitted)
    if (header_h == 0) for (x = [cav_x0 - 0.01, pcb_w - ledge_w])
        translate([x, ledge_y0, floor_z - 0.01]) cube([ledge_w + clr + 0.01, ledge_y1 - ledge_y0, -floor_z + 0.01]);
}

// ---------------------------------------------------------------- LID
module lid() {
    difference() {
        translate([0, 0, split_z]) linear_extrude(lid_z1 - split_z) outer_2d();
        translate([0, 0, split_z - 0.01]) linear_extrude(lip_h + lip_gap + 0.01) skirt_inner_2d();  // skirt pocket for the lip
        translate([0, 0, split_z - 0.02]) linear_extrude(ceil_z - split_z + 0.02) cavity_2d();      // cavity
        window_cut();
        usb_cut(-BIG / 2, usb_cut_top);
        if (button_style == "keycap") both_sides() key_hole_left();
        else if (button_style == "top") both_sides() top_flap_cut_left();
        else if (button_style == "side") both_sides() flap_cut_left();
        else button_cuts(-BIG / 2, btn_cut_top);
        snap_recesses();
    }
    if (button_style == "top") both_sides() { top_stem_left(); top_cap_left(); }
    if (button_style == "side") both_sides() { nub_left(); cap_left(); }
}

// ---------------------------------------------------------------- board mock-up (preview only)
module board() {
    // PCB with chamfered corners
    color("darkgreen") linear_extrude(pcb_t) polygon([
        [pcb_ch_usb, 0], [pcb_w - pcb_ch_usb, 0], [pcb_w, pcb_ch_usb], [pcb_w, pcb_l - pcb_ch_ant],
        [pcb_w - pcb_ch_ant, pcb_l], [pcb_ch_ant, pcb_l], [0, pcb_l - pcb_ch_ant], [0, pcb_ch_usb]]);
    // acrylic bracket
    color("lightcyan", 0.5) {
        translate([pm_x0, pm_y0, pm_z0]) cube([pm_x1 - pm_x0, pm_y1 - pm_y0, pm_z1 - pm_z0]);
        translate([pm_x0, pm_tab_y0, pcb_t]) cube([pm_x1 - pm_x0, pm_tab_y1 - pm_tab_y0, pm_z1 - pcb_t]);
        translate([pm_x0, pm_tab2_y0, pm_z1]) cube([pm_x1 - pm_x0, pm_tab_y1 - pm_tab2_y0, lcd_top - pm_z1]);
    }
    // LCD glass + visible area
    color("black") translate([lcd_x0, lcd_y0, lcd_z0]) cube([lcd_x1 - lcd_x0, lcd_y1 - lcd_y0, lcd_top - 0.05 - lcd_z0]);
    color("royalblue") translate([win_cx - 8, win_cy - 8, lcd_top - 0.2]) cube([16, 16, 0.2]);
    // USB-C
    color("silver") translate([usb_cx - usb_w / 2, -usb_out, pcb_t]) cube([usb_w, usb_len, usb_h]);
    // side buttons (body + plunger)
    color("gray") for (x0 = [btn_inset, pcb_w - btn_inset - btn_body_w])
        translate([x0, btn_y0, pcb_t]) cube([btn_body_w, btn_y1 - btn_y0, btn_h - 0.4]);
    // round plungers on TOP of the switches (body 2.1 high, plunger to plunger_top_z)
    color("white") for (cx = [btn_inset + btn_body_w / 2, pcb_w - btn_inset - btn_body_w / 2])
        translate([cx, btn_cy, pcb_t + btn_h - 0.4]) cylinder(d = 1.8, h = plunger_top_z - (pcb_t + btn_h - 0.4));
    // RESET (underside, left edge)
    color("gray")  translate([0.65, rst_y0 - 1.0, rst_body_z0]) cube([rst_body_x1 - 0.65, rst_y1 - rst_y0 + 2.0, -rst_body_z0]);
    color("white") translate([-rst_out, rst_y0, rst_z0]) cube([0.65 + rst_out + 0.01, rst_y1 - rst_y0, rst_z1 - rst_z0]);
    // JST-SH, U.FL, ESP32-S3
    color("ivory")  translate([jst_x0, jst_y0, -jst_h]) cube([jst_x1 - jst_x0, jst_y1 - jst_y0, jst_h]);
    color("gold")   translate([ufl_x, ufl_y, -ufl_h]) cylinder(d = 2.0, h = ufl_h);
    color("dimgray") translate([esp_x0, esp_y0, -esp_h]) cube([esp_x1 - esp_x0, esp_y1 - esp_y0, esp_h]);
    // header pad rows
    color("goldenrod") for (x0 = [hdr_x0, pcb_w - hdr_x1])
        translate([x0, hdr_y0, pcb_t]) cube([hdr_x1 - hdr_x0, hdr_y1 - hdr_y0, 0.02]);
    if (header_h > 0) color("black") for (x0 = [hdr_x0, pcb_w - hdr_x1])
        translate([x0, hdr_y0, -header_h]) cube([hdr_x1 - hdr_x0, hdr_y1 - hdr_y0, header_h]);
}

// ---------------------------------------------------------------- print orientations
module base_print() translate([0, 0, -base_z0]) base();
module lid_print()  translate([0, out_y0 + out_y1, lid_z1]) rotate([180, 0, 0]) lid();   // top face on the bed
module keys_print() translate([0, 2 * btn_cy, lid_z1 + key_cap_above]) rotate([180, 0, 0]) keys();   // cap faces on the bed

// ---------------------------------------------------------------- dispatch
if (part == "base")           base_print();
else if (part == "lid")       lid_print();
else if (part == "keys")      keys_print();
else if (part == "both_for_print") {
    base_print(); translate([out_x1 - out_x0 + 6, 0, 0]) lid_print();
    if (button_style == "keycap") translate([0, out_y1 - out_y0 + 4, 0]) keys_print();
}
else if (part == "board")     board();
else if (part == "assembly")  { color("tan") base(); color("tan", 0.6) lid(); if (button_style == "keycap") color("orangered") keys(); board(); }
else if (part == "exploded")  { color("tan") base(); translate([0, 0, 14]) color("tan", 0.6) lid(); if (button_style == "keycap") translate([0, 0, 10]) color("orangered") keys(); translate([0, 0, 6]) board(); }
