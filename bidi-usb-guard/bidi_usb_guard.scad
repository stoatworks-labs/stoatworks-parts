// BiDi USB guard: a cover for the SDI end of a Blackmagic Micro Converter
// BiDirectional SDI/HDMI 3G (the USB-C model). A tower round the USB-C plug
// stops a tug on the cable levering the port; the SDI BNC nuts clamp it on;
// windows show the SDI lock and power LEDs.
//
// Origin: centre of the converter's SDI end panel, Z = 0 on the panel.
// X runs along the panel (USB-C at +X), Y up it (the label side is +Y).
// It prints as modelled: plate on the bed, tower up.
//
//   openscad -o bidi_usb_guard_v0.1.stl bidi_usb_guard.scad
//   openscad -o bidi_usb_guard_v0.1-body.stl -D 'part="body"' bidi_usb_guard.scad
//   openscad -o bidi_usb_guard_v0.1-logo.stl -D 'part="logo"' bidi_usb_guard.scad

include <stoatworks_mark.scad>

part = "guard";   // guard | body (no logo) | logo (for a second colour)

/* [Fit] */
pocket_h = 18.2;  // panel to the cap's underside, as dj12bas's "16.7 mm" part
                  // (its straight walls stop at 16.7; its roof is at 18.2).
                  // Their longer version, for other plugs, is 22.8 / 24.3.

// ---- the converter (see README for where each number came from) ----
bnc      = [[-15.80, 2.05], [2.00, 2.06]];  // SDI IN, SDI OUT
bnc_d    = 14.2;            // the BNC nut (13.7 across flats) seats on its corners
nut_r    = 7.7;             // half the nut's width across corners
led_lock = [-6.83, -7.36];  // SDI lock LED, between the BNCs
led_pwr  = [24.78, -7.37];  // power LED, beyond the USB-C port
led_d    = 2.1;
pocket_x  = [11.8, 25.3];   // the plug body's pocket, open towards +Y
pocket_y0 = -6.99;
hook_y    = 0.5;            // hooks at the top of the open side start here,
hook_z    = 11.4;           //   0.3 mm past the plug body, and this high up
opening_y = 3.5;            // the plate's opening for the plug reaches this far

// ---- plate ----
plate     = [56, 23];
plate_t   = 2.0;     // all the BNC thread leaves room for: do not thicken
corner    = 2.0;     // corner chamfers
lip_w     = 1.0;     // raised rim round the outer face. 1.0 wide keeps it
lip_h     = 1.0;     //   0.7 mm clear of the nuts' corners
vee       = 1.2;     // depth of the 90 degree notches in the long edges
vee_x     = [-21, -7, 7, 21];  // both edges; clear of the BNC bridges, nuts,
                               //   LED windows and corners. -7 points at the lock LED
window_r  = 1.8;
window_cs = 0.5;     // 45 degree countersink round the lock window

// ---- tower ----
wall_mx = 1.2;    // -X wall: 0.9 mm clear of the SDI OUT nut's corners
wall_px = 1.8;    // +X wall: runs into the lip
wall_my = 1.6;
arm_y   = 2.5;    // where the side walls stop; the pocket is open beyond
cap_t   = 2.0;
slot_w  = 9.0;    // cable slot in the cap: narrower than the plug body
slot_c  = [18.55, -2.3];
edge_ch = 0.6;    // chamfer on the tower's upright edges
top_ch  = 0.8;    // and round the top of the cap
gusset  = 1.95;   // 45 degree fillet along the foot of the -Y wall, into the lip
well_r  = 2.0;    // light well cut down the tower's corner over the power LED

// ---- logo ----
logo_raise = 0.5;

X0 = pocket_x[0] - wall_mx;
X1 = pocket_x[1] + wall_px;
Y0 = pocket_y0 - wall_my;
Y1 = arm_y;
top = pocket_h + cap_t;
eps = 0.01;

$fn = 96;

// -------------------------------------------------------------- 2D

module chamfered_rect(x0, y0, x1, y1, c)
    polygon([[x0 + c, y0], [x1 - c, y0], [x1, y0 + c], [x1, y1 - c],
             [x1 - c, y1], [x0 + c, y1], [x0, y1 - c], [x0, y0 + c]]);

module plate_outline()
    chamfered_rect(-plate[0] / 2, -plate[1] / 2, plate[0] / 2, plate[1] / 2, corner);

module vees() for (x = vee_x, s = [-1, 1])
    translate([x, s * plate[1] / 2]) rotate(45) square(vee * sqrt(2), center = true);

module tower_foot() chamfered_rect(X0, Y0, X1, Y1, edge_ch);

module pocket() translate([pocket_x[0], pocket_y0])
    square([pocket_x[1] - pocket_x[0], Y1 - pocket_y0 + 1]);

module slot() translate(slot_c) {
    circle(d = slot_w);
    translate([-slot_w / 2, 0]) square([slot_w, 20]);
}

// Everything within well_r of the quarter beyond the power LED: an L-shaped
// bite out of the tower's corner whose inside corner is a circle round the LED.
module light_well() translate(led_pwr) offset(r = well_r) translate([0, -100]) square(100);

// -------------------------------------------------------------- 3D

module plate() {
    linear_extrude(plate_t) plate_outline();
    linear_extrude(plate_t + lip_h) difference() {
        plate_outline();
        offset(delta = -lip_w) plate_outline();
    }
}

module gusset() translate([X0, 0, 0]) rotate([90, 0, 90])
    linear_extrude(X1 - X0)
        polygon([[Y0 + eps, 0], [Y0 - gusset, 0], [Y0 - gusset, plate_t],
                 [Y0 + eps, plate_t + gusset]]);

module tower() difference() {
    union() {
        hull() {
            linear_extrude(top - top_ch) tower_foot();
            translate([0, 0, top - top_ch]) linear_extrude(top_ch)
                offset(delta = -top_ch) tower_foot();
        }
        gusset();
    }
    translate([0, 0, -1]) linear_extrude(pocket_h + 1) pocket();
    translate([0, 0, pocket_h - eps]) linear_extrude(cap_t + 1) slot();
    translate([0, 0, -1]) linear_extrude(top + 2) light_well();
}

// Two hooks across the top of the open side, either side of the cable, so the
// plug body cannot tip out towards +Y. 45 degree undersides print unsupported.
module hooks() for (side = [[pocket_x[0] - eps, slot_c[0] - slot_w / 2],
                            [pocket_x[1] + eps, slot_c[0] + slot_w / 2]]) {
    w = abs(side[1] - side[0]);
    translate([0, Y1, 0]) rotate([90, 0, 0]) linear_extrude(Y1 - hook_y)
        polygon([[side[0], hook_z], [side[1], hook_z + w],
                 [side[1], pocket_h + eps], [side[0], pocket_h + eps]]);
}

module windows() {
    for (p = [led_lock, led_pwr]) translate([p[0], p[1], -1])
        cylinder(r = window_r, h = plate_t + 2);
    translate([led_lock[0], led_lock[1], plate_t - window_cs])
        cylinder(r1 = window_r, r2 = window_r + window_cs + eps, h = window_cs + eps);
}

// Raised mark on the -Y face, between the chamfered edge and the light well.
logo_cx = (X0 + edge_ch + led_pwr[0] - well_r) / 2;
logo_cz = (plate_t + gusset + top - top_ch) / 2;
module logo(depth_in = 0.3)
    translate([logo_cx, Y0, logo_cz]) rotate([90, 0, 0])
        translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();

module body() difference() {
    union() { plate(); tower(); hooks(); }
    for (b = bnc) translate([b[0], b[1], -1]) cylinder(d = bnc_d, h = top + 2);
    // the plug goes through the plate to the port
    translate([0, 0, -1]) linear_extrude(plate_t + 1 + eps)
        translate([pocket_x[0], pocket_y0]) square([pocket_x[1] - pocket_x[0], opening_y - pocket_y0]);
    windows();
    translate([0, 0, -1]) linear_extrude(plate_t + gusset + 2) vees();
}

if (part == "guard") union() { body(); logo(); }
else if (part == "body") body();
else if (part == "logo") logo(0);
