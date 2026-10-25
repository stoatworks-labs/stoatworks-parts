// Micro Converter USB guard: a cover for the HDMI end of Blackmagic's one-way
// Micro Converters (SDI to HDMI and HDMI to SDI, 3G and 12G, the USB-C
// models). A tower round the USB-C plug stops a tug on the cable levering the
// port. This end has no BNC nuts to clamp a plate, so the guard wraps round
// both corners of the case, and its two arms take the case's own side screws,
// the pair nearest this end.
//
// Origin: centre of the HDMI end, Z = 0 on the case's front edge, Z out along
// the cables. X runs across the end (USB-C at +X), Y up it (the label side is
// +Y). The STL is turned to print: the converter's underside goes on the bed,
// and every part of the guard starts there (see posed()).
//
//   openscad -o micro_converter_usb_guard_v0.1.stl micro_converter_usb_guard.scad
//   openscad -o micro_converter_usb_guard_v0.1-body.stl -D 'part="body"' micro_converter_usb_guard.scad
//   openscad -o micro_converter_usb_guard_v0.1-logo.stl -D 'part="logo"' micro_converter_usb_guard.scad

include <stoatworks_mark.scad>

part = "guard";   // guard | body (no logo) | logo (for a second colour) | none
pose = "print";   // print | fitted (the converter's frame, for pictures and checks)

/* [Fit] */
pocket_h = 18.2;  // case front edge to the cap's underside: Blackmagic's own
                  // USB-C plug body, as in the BiDi guard
screw_z  = -19.6; // the side screws nearest this end, back from the front edge
side_gap = 0.2;   // between the case and each arm

// ---- the converter (see README for where each number came from) ----
case_w  = 45.72;          // 1.80 in
case_h  = 24.89;          // 0.98 in
usbc    = [10.99, -3.47]; // USB-C port centre
led     = [18.27, -3.97]; // power LED
led_d   = 2.1;
hdmi    = [-10.66, -0.60];// HDMI port centre
screw_y = 0;              // the side screws are at mid-height
pocket  = [13.6, 8.0];    // the plug body: Blackmagic's supply's is under 13.5 x 7.5
hdmi_room = [12.5, 7.25]; // half-sizes: the opening passes an HDMI plug moulding
                          //   up to 25 x 14.5 mm, so it still reaches the port

// ---- plate and arms ----
plate_t = 2.0;
arm_t   = 2.0;    // the screw in each arm must be this much longer than the original
arm_l   = 26.0;   // the arms reach this far back from the front edge
arm_ch  = 3.0;    // chamfers on the arms' back corners
corner  = 2.0;    // 45 degree bevel where the plate wraps round the case's corners
lip_w   = 1.0;    // raised rim round the outer face
lip_h   = 1.0;
vee     = 1.2;    // depth of the 90 degree notches along the top edge
vee_x   = [-16, -6, 6, 16];
hole_d  = 3.4;    // M3 clearance
csink_d = 6.4;    // 90 degree countersink: an M3 flat head (6.0) sits just under flush
slot    = 1.2;    // each screw hole is a slot, +/- this along the case
relief  = 0.5;    // groove in each inside corner, for the case's edge

// ---- tower ----
wall    = 1.6;
cap_t   = 2.0;
slot_w  = 8.0;    // cable slot in the cap: the cap overlaps both ends of the plug body
edge_ch = 0.6;    // chamfer on the tower's upright edges
top_ch  = 0.8;    // and round the top of the cap
gusset  = 1.5;    // 45 degree fillet along the foot of the tower's top face
well_r  = 1.7;    // light well down the tower over the power LED. The LED is right
                  //   beside the plug body, so a wider well eats the cap's overlap

// ---- logo ----
logo_raise = 0.5;
logo_z     = -7.6;  // on both arms, between the bevel and the screw

XA  = case_w / 2 + side_gap;  // the arms' inside faces
XO  = XA + arm_t;             // and outside
X1  = XO - corner;            // the plate's outer face, and the tower's +X face
YB  = -case_h / 2;
YT  = case_h / 2;
PX  = [usbc[0] - pocket[0] / 2, usbc[0] + pocket[0] / 2];
PY  = [usbc[1] - pocket[1] / 2, usbc[1] + pocket[1] / 2];
TX  = PX[0] - wall;           // the tower's -X face
TY  = PY[1] + wall;           // its top face; it reaches down to the bed
top = pocket_h + cap_t;

$fn = 96;

// -------------------------------------------------------------- 2D

module pocket2d() translate([PX[0], PY[0]]) square([pocket[0], pocket[1]]);

module cable_slot() translate(usbc) {
    circle(d = slot_w);
    translate([-slot_w / 2, 0]) square([slot_w, YT]);
}

// A teardrop, so the well's roof prints without support.
module well() translate(led) { circle(r = well_r); rotate(45) square(well_r); }

// Above the plate the well opens out of the tower's side. The window's roof
// rises at 45 degrees, just under the line of the teardrop's edge, so it
// prints, and comes out through the tower's top corner. It starts inside the
// well rather than on its outline, so the two share no edges.
module window() {
    l    = led[0] - 0.6;
    roof = led[1] + well_r * sqrt(2) - 0.1 - led[0];  // roof: y = x + roof
    polygon([[l, led[1] - well_r + 0.3], [XO + 5, led[1] - well_r + 0.3], [XO + 5, TY],
             [TY - roof, TY], [l, l + roof]]);
}

// From the case's own side (no moulding gets past that) to clear of the HDMI
// plug's moulding.
module hdmi_opening() hull() {
    translate([-case_w / 2, hdmi[1] - hdmi_room[1]]) square([1, 2 * hdmi_room[1]]);
    for (s = [-1, 1])
        translate([hdmi[0] + hdmi_room[0] - 1.5, hdmi[1] + s * (hdmi_room[1] - 1.5)]) circle(r = 1.5);
}

module vees() for (x = vee_x)
    polygon([[x - vee - 1, YT + 1], [x + vee + 1, YT + 1], [x, YT - vee]]);

module face() translate([-X1, YB]) square([2 * X1, case_h]);

module tower_foot()
    polygon([[TX, YB], [X1, YB], [X1, TY - edge_ch], [X1 - edge_ch, TY],
             [TX + edge_ch, TY], [TX, TY - edge_ch]]);

// -------------------------------------------------------------- 3D

// The plate and both arms as one profile across the case, full height so the
// converter still sits flat either way up: the plate over the end, bevelled
// round the two upright corners, and the arms back along the sides to the
// screws. Their back corners are chamfered.
module wrap() difference() {
    rotate([90, 0, 0]) linear_extrude(case_h, center = true)
        polygon([[-XO, -arm_l], [-XA, -arm_l], [-XA, 0], [XA, 0], [XA, -arm_l], [XO, -arm_l],
                 [XO, 0], [X1, plate_t], [-X1, plate_t], [-XO, 0]]);
    for (s = [-1, 1]) translate([-XO - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(2 * XO + 2)
        polygon([[s * (case_h / 2 - arm_ch - 1), -arm_l - 1], [s * (case_h / 2 + 1), -arm_l - 1],
                 [s * (case_h / 2 + 1), -arm_l + arm_ch + 1]]);
}

module lip() translate([0, 0, plate_t - 0.5]) linear_extrude(lip_h + 0.5)
    difference() { face(); offset(delta = -lip_w) face(); }

// The tower stands on the bed beside the HDMI opening and runs out to the
// right arm, so it is solid under and beside the plug.
module tower() hull() {
    linear_extrude(top - top_ch) tower_foot();
    translate([0, 0, top - top_ch]) linear_extrude(top_ch) offset(delta = -top_ch) tower_foot();
}

// Its ends stop short of the tower's chamfered corners.
module gusset() translate([TX + edge_ch + 0.3, 0, 0]) rotate([90, 0, 90])
    linear_extrude(X1 - TX - 2 * edge_ch - 0.6)
        polygon([[TY - 0.5, 0], [TY + gusset, 0], [TY + gusset, plate_t],
                 [TY - 0.5, plate_t + gusset + 0.5]]);

// The right arm's screw: a slot along the case, countersunk on the outside.
// The countersink's cone starts inside the bore and overshoots the face, half
// a facet round, so it leaves no slivers where it meets them.
csink_in  = (csink_d - hole_d) / 2 + 0.2;  // cone starts 0.2 mm into the bore
csink_out = 0.5;                           // and ends this far outside the face
module screw_slot() rotate([0, 90, 0]) {
    hull() for (u = [-slot, slot]) translate([-screw_z + u, screw_y, XA - 1])
        cylinder(d = hole_d, h = arm_t + 2);
    hull() for (u = [-slot, slot]) translate([-screw_z + u, screw_y, XO - csink_in])
        rotate(180 / $fn) cylinder(d1 = hole_d - 0.4, d2 = csink_d + 2 * csink_out,
                                   h = csink_in + csink_out);
}

module reliefs() for (s = [-1, 1]) translate([s * XA, YT + 1, 0]) rotate([90, 0, 0])
    rotate(45) cylinder(r = relief, h = case_h + 2, $fn = 4);

// Upright to someone looking at the side of the converter, label up.
module logo(depth_in = 0.3) for (s = [-1, 1])
    translate([s * XO, 0, logo_z]) rotate([0, s * 90, 0])
        translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();

module body() difference() {
    union() { wrap(); lip(); tower(); gusset(); }
    // the plug goes through the plate to the port, its cable through the cap
    translate([0, 0, -1]) linear_extrude(pocket_h + 1) pocket2d();
    translate([0, 0, pocket_h]) linear_extrude(cap_t + 1) cable_slot();
    // the LED shows down the well, and from the USB-C side and above through
    // the window
    translate([0, 0, -1]) linear_extrude(top + 2) well();
    translate([0, 0, plate_t]) linear_extrude(top) window();
    translate([0, 0, -1]) linear_extrude(plate_t + lip_h + 2) { hdmi_opening(); vees(); }
    screw_slot();
    mirror([1, 0, 0]) screw_slot();
    reliefs();
}

module posed() if (pose == "print") translate([0, 0, -YB]) rotate([90, 0, 0]) children();
               else children();

if (part == "guard") posed() union() { body(); logo(); }
else if (part == "body") posed() body();
else if (part == "logo") posed() logo(0);
