// Decimator micro-USB guard: a cover for the SDI end of a Decimator Design
// MD-LX (the micro-USB model, before the USB-C one). It is the USB-C guard's
// design with the pocket, lips and back wall moved and resized for a micro-USB
// plug: a tower round the plug stops a tug on the cable levering the port; the
// housing's own two end screws hold it on. A window keeps the small hole between
// the BNCs open.
//
// Origin: centre of the MD-LX's SDI end panel, Z = 0 on the panel.
// X runs along the panel (micro-USB at -X), Y up it (the label side is +Y).
// It prints as modelled: plate on the bed, tower up.
//
//   openscad -o decimator_microusb_guard_v0.1.stl decimator_microusb_guard.scad
//   openscad -o decimator_microusb_guard_v0.1-body.stl -D 'part="body"' decimator_microusb_guard.scad
//   openscad -o decimator_microusb_guard_v0.1-logo.stl -D 'part="logo"' decimator_microusb_guard.scad

include <stoatworks_mark.scad>

part = "guard";   // guard | body (no logo) | logo (for a second colour)

// ---- the MD-LX (see README for where each number came from) ----
screws   = [[-26.45, -2.27], [26.42, -2.30]];  // the housing's end screws, reused
screw_d  = 4.0;              // clearance through the plate
csink_d  = 6.4;              // 90 degree countersink, flush at the top
head_d   = 6.6;              // kept clear above the countersink, for head and driver
bnc      = [[-1.85, 1.10], [13.95, 1.10]];     // SDI OUTPUT, SDI INPUT
flange_d = 14.3;             // BNC flange at the panel
bnc_r    = 8.35;             // each BNC hole: 1.2 mm clear of its flange, as the original
usb      = [-16.25, -2.5];   // the micro-USB socket's centre
plug     = [10.6, 6.8];      // the plug body the pocket is sized for: Decimator's and
                             // Blackmagic's stock micro-USB plugs, as near as photos tell
body_h   = 13.2;             // the plug body's height off the panel
pocket_x = [usb[0] - plug[0] / 2 - 0.3, usb[0] + plug[0] / 2 + 0.3]; // open at +X, towards the BNCs
pocket_y = [usb[1] - plug[1] / 2 - 0.3, usb[1] + plug[1] / 2 + 0.3];
// The back wall's inside face, as [x, z] from the panel up: straight up past
// the plug body's far end, then leaning in over it at 45 degrees.
back_face = [[pocket_x[0], 0], [pocket_x[0], body_h], [pocket_x[0] + 1.5, body_h + 1.5],
             [pocket_x[0] + 1.5, 30]];
lip_x    = pocket_x[1] - 1.05; // lips across the open end start here
lip_c    = usb[1];           //   and close in round the cable's line, leaving
lip_gap  = [for (g = [[0, 3.50], [0.2, 3.37], [0.7, 3.14], [1.2, 2.89], [1.7, 2.68],
                      [2.2, 2.51], [2.7, 2.37], [3.2, 2.26], [3.7, 2.18], [4.2, 2.12],
                      [4.7, 2.07], [5.2, 2.04], [5.7, 2.01], [14.7, 2.0]])
            [body_h + g[0], g[1]]];
                             //   this half-gap [z, mm] at each height above the body:
                             //   the USB-C guard's profile, lowered to the shorter plug
hole_led = [5.4, -3.3];      // the small hole between the BNCs, kept open
window_r = 1.65;

// ---- plate ----
plate     = [59.9, 22.5];
plate_t   = 2.5;
corner    = 2.0;
lip_w     = 1.0;     // raised rim round the outer face
lip_h     = 1.0;
vee       = 1.2;     // 90 degree notches in the long edges
vee_x     = [-24, -8, 8, 24];  // clear of the BNC holes' thin strips and the screws
cusp      = 0.6;     // blunts the points where the two BNC holes meet

// ---- tower ----
back_x  = -23.45;   // outer face of the back wall: the left screw's head clears it
wall_y  = 2.0;      // side walls
tower_h = 21.0;
edge_ch = 0.6;
top_ch  = 0.8;
gusset  = 2.45;     // 45 degree fillet at the foot of each side wall, into the lip

// ---- logo ----
logo_raise = 0.5;

Y0 = pocket_y[0] - wall_y;
Y1 = pocket_y[1] + wall_y;
X1 = pocket_x[1];   // the walls stop at the open end
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

module pocket2d() translate([pocket_x[0], pocket_y[0]])
    square([pocket_x[1] - pocket_x[0], pocket_y[1] - pocket_y[0]]);

// The plate's opening: the plug's pocket running into two overlapping BNC
// holes. The BNC flanges are only ~1.3 mm apart, too little for a web between
// two separate holes, so the holes meet at a waist instead of an oval.
// The pocket is 0.3 mm bigger here than in the tower, back and sides, so the
// plate's edges sit under the tower's walls instead of on them.
module opening() offset(r = -cusp) offset(r = cusp) union() {
    translate([pocket_x[0] - 0.3, pocket_y[0] - 0.3])
        square([pocket_x[1] - pocket_x[0] - 0.2, pocket_y[1] - pocket_y[0] + 0.6]);
    pocket2d();
    hull() {
        translate([pocket_x[1] - 2, pocket_y[0]]) square([2.6, pocket_y[1] - pocket_y[0]]);
        translate(bnc[0]) circle(r = bnc_r);
    }
    translate(bnc[1]) circle(r = bnc_r);
    translate(hole_led) rotate(180 / $fn) circle(r = window_r);
}

module tower_foot() chamfered_rect(back_x, Y0, X1, Y1, edge_ch);

// -------------------------------------------------------------- 3D

module plate() difference() {
    union() {
        linear_extrude(plate_t) plate_outline();
        linear_extrude(plate_t + lip_h) difference() {
            plate_outline();
            offset(delta = -lip_w) plate_outline();
        }
    }
    translate([0, 0, -1]) linear_extrude(plate_t + 2) opening();
}

module gussets() for (s = [[Y0, -1], [Y1, 1]]) translate([back_x, 0, 0]) rotate([90, 0, 90])
    linear_extrude(X1 - back_x)
        polygon([[s[0] - s[1] * eps, 0], [s[0] + s[1] * gusset, 0],
                 [s[0] + s[1] * gusset, plate_t], [s[0] - s[1] * eps, plate_t + gusset]]);

// The space the plug needs: the pocket, bounded at the back by the back wall's
// drafted face and open at the front, less two lips that close in over the plug
// body's near end and leave a gap for the cable. The lips' undersides are
// steeper than 45 degrees, so they print unsupported.
module plug_space() difference() {
    translate([0, pocket_y[1], 0]) rotate([90, 0, 0])
        linear_extrude(pocket_y[1] - pocket_y[0])
            polygon(concat([[pocket_x[1] + 5, -1]], [for (p = back_face) p],
                           [[pocket_x[1] + 5, 30]]));
    for (s = [1, -1]) {
        wall = s > 0 ? pocket_y[1] : pocket_y[0];
        translate([lip_x, 0, 0]) rotate([90, 0, 90]) linear_extrude(pocket_x[1] - lip_x + 1)
            polygon(concat([[wall + s, body_h]],
                           [for (g = lip_gap) [lip_c + s * g[1], g[0]]],
                           [[wall + s, 30]]));
    }
}

module tower() difference() {
    union() {
        hull() {
            linear_extrude(tower_h - top_ch) tower_foot();
            translate([0, 0, tower_h - top_ch]) linear_extrude(top_ch)
                offset(delta = -top_ch) tower_foot();
        }
        gussets();
    }
    plug_space();
}

module screw_holes() for (s = screws) translate([s[0], s[1], 0]) {
    translate([0, 0, -1]) cylinder(d = screw_d, h = plate_t + 2);
    // the countersink's cone starts inside the bore and overshoots the face, half
    // a facet round, so it leaves no slivers where it meets them
    // (it stops 0.05 mm past the face, inside the head's clearance)
    translate([0, 0, plate_t - (csink_d - screw_d) / 2 - 0.2]) rotate(180 / $fn)
        cylinder(d1 = screw_d - 0.4, d2 = csink_d + 0.1, h = (csink_d - screw_d) / 2 + 0.25);
    // the head's clearance, carried out through the lip to the edge. It starts
    // 0.1 mm below the plate's face, so the two never share a plane
    translate([0, 0, plate_t - 0.1]) linear_extrude(tower_h + 0.1) hull() {
        circle(d = head_d);
        translate([sign(s[0]) * 10, 0]) circle(d = head_d);
    }
}

// The mark on both side faces, upright to someone looking down at the tower
// from in front of the box: its top points back at the panel (-Z).
logo_cx = (back_x + edge_ch + X1 - edge_ch) / 2;
logo_cz = (plate_t + gusset + tower_h - top_ch) / 2;
module logo(depth_in = 0.3) for (side = [-1, 1])
    translate([logo_cx, side < 0 ? Y0 : Y1, logo_cz])
        rotate([side < 0 ? 90 : -90, 0, 0]) rotate([0, 0, side < 0 ? 180 : 0])
            translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();

module body() difference() {
    union() { plate(); tower(); }
    screw_holes();
    translate([0, 0, -1]) linear_extrude(plate_t + gusset + 2) vees();
}

if (part == "guard") union() { body(); logo(); }
else if (part == "body") body();
else if (part == "logo") logo(0);
