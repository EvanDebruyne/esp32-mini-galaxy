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
//  Printing:  part = "both_for_print"  ->  base upright, lid face-down.
//  Previews:  part = "assembly" / "exploded" show the case with a board mock-up.
// =====================================================================

/* [Part to render] */
part = "assembly"; // [base, lid, both_for_print, assembly, exploded, board]

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
reset_slot_w    = 2.6;  // width of the RESET pin-hole / slot
reset_slot_open = true; // true: slot open to the base rim (no bridging). false: closed hole (2.6 mm bridge)
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
// side buttons: through both long walls, from z0 to z1
module button_cuts(z0, z1) {
    for (x = [out_x0 - 1, cav_x1 - 1])
        translate([x, 0, 0]) rotate([90, 0, 90]) linear_extrude(wall + 2)
            rrect(btn_y0 - btn_cut_margin, z0, btn_y1 + btn_cut_margin, z1, 0.8);
}
// RESET: pin hole / slot in the left wall of the base
module reset_cut() {
    top = reset_slot_open ? BIG : -0.2;
    translate([out_x0 - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(wall + 2)
        rrect(rst_cy - reset_slot_w / 2, rst_slot_bot, rst_cy + reset_slot_w / 2, top, 0.8);
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
        button_cuts(split_z - 0.01, BIG);                               // keep the lip clear of the plungers
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
        button_cuts(-BIG / 2, btn_cut_top);
        snap_recesses();
    }
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
        translate([x0, btn_y0, pcb_t]) cube([btn_body_w, btn_y1 - btn_y0, btn_h]);
    color("white") {
        translate([btn_plunger_recess, btn_y0 + 0.8, pcb_t + 0.6]) cube([btn_inset - btn_plunger_recess + 0.01, 2.4, 1.3]);
        translate([pcb_w - btn_inset - 0.01, btn_y0 + 0.8, pcb_t + 0.6]) cube([btn_inset - btn_plunger_recess + 0.01, 2.4, 1.3]);
    }
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

// ---------------------------------------------------------------- dispatch
if (part == "base")           base_print();
else if (part == "lid")       lid_print();
else if (part == "both_for_print") { base_print(); translate([out_x1 - out_x0 + 6, 0, 0]) lid_print(); }
else if (part == "board")     board();
else if (part == "assembly")  { color("tan") base(); color("tan", 0.6) lid(); board(); }
else if (part == "exploded")  { color("tan") base(); translate([0, 0, 14]) color("tan", 0.6) lid(); translate([0, 0, 6]) board(); }
