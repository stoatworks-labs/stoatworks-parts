// Mini Converter power guard: a cover for the power end of Blackmagic's Mini
// Converter SDI Distribution, SDI Distribution 4K and Sync Generator. A plate
// spans the whole end and wraps round both corners into arms that take the
// nearest case screw on each side. A tower round the 12 V plug holds it
// straight, and a cable tie through the top of the tower holds the plug's boot,
// so a tug on the lead pulls on the case's screws, not on the jack. One window
// over the BNCs (and the Sync Generator's USB port) leaves them free: they fill
// most of the end's height, so the plate is a frame round them.
//
// Origin: the case's corner by the power jack, on its underside. X runs across
// the end from the side the jack is near (+X towards the BNCs), Y up, Z = 0 on
// the case's front edge and out along the cables. The STL is turned to print:
// the converter's underside goes on the bed, and every part of the guard starts
// there (see posed()).
//
//   openscad -o mini_converter_power_guard_v0.1.stl mini_converter_power_guard.scad
//   openscad -o mini_converter_power_guard_v0.1-body.stl -D 'part="body"' mini_converter_power_guard.scad
//   openscad -o mini_converter_power_guard_v0.1-logo.stl -D 'part="logo"' mini_converter_power_guard.scad

include <stoatworks_mark.scad>

part = "guard";   // guard | body (no logo) | logo (for a second colour) | none
pose = "print";   // print | fitted (the converter's frame, for pictures and checks)

/* [Fit] */
bnc_holes = false; // false: one window over the BNCs, open at the top, which fits whatever
                   //   their height. true: a hole per BNC and a strip across the top, once
                   //   bnc_y has been measured on a real converter
model    = "da";  // with bnc_holes only: "da" (SDI Distribution, 4K) or "sync" (Sync Generator)
bnc_y    = 12.4;  // the BNCs' height off the underside; only bnc_holes uses it
screw_z  = 24.3;  // the side screws nearest this end, back from the case's front edge
screw_y  = 11.45; // their height off the underside
tower_h  = 28;    // the tower reaches this far out; the tie sits just under its top
side_gap = 0.2;   // between the case and each arm

// ---- the converter (see README for where each number came from) ----
case_h  = 22.9;          // 0.90 in
case_w  = 92.2;          // across the end, 3.63 in
case_l  = 96.9;          // along the side, without the BNCs
jack    = [11.9, 12.4];  // the DC jack's centre, from the side and the underside
recess  = 1.5;           // the end panel sits about this far behind the case's front edge
bnc_x   = model == "da" ? [29.29, 44.25, 58.48, 72.99] : [24.15, 38.74, 53.34];
usb     = [79.4, 8.8];   // the Sync Generator's mini-B USB port
small   = [[18.8, 8.1], [84.6, 7.8]];  // small holes in the panel: beside the jack, beside the USB

// ---- plate and arms ----
plate_t = 2.0;
arm_t   = 2.0;    // the screw in each arm must be this much longer than the original
arm_l   = 30;     // the arms reach this far back from the front edge
arm_ch  = 3.0;    // chamfers on the arms' back corners
corner  = 2.0;    // 45 degree bevel where the plate wraps round the far corner
lip_w   = 1.0;    // raised rim round the plate's outer face
lip_h   = 1.0;
window  = [16.5, 87.0];  // the window's ends: the tower's face, and past the Sync Generator's USB port
rail_h  = 3.4;    // the rail under the window: clear of a BNC plug's sleeve 1.5 mm lower than measured
hole_r  = 8.1;    // with bnc_holes: a 1/2 in nut (14.7 across corners) and a BNC plug (14.3), 0.75 mm round
usb_room = [72.9, 87.0, 4.3, 13.3];  // with bnc_holes on the Sync Generator: room for a USB plug
window_r = 1.8;   // with bnc_holes: windows over the small holes
hole_d  = 3.6;    // M3
csink_d = 6.4;    // 90 degree countersink: an M3 flat head (6.0) sits just under flush
slot    = 1.5;    // each screw hole is a slot, +/- this along the case
slot_y  = 0.4;    //   and +/- this up and down
relief  = 0.6;    // groove in each inside corner, for the case's edge
vee     = 1.2;    // 90 degree notches along the arms' top edges
vee_z   = [-8, -14];

// ---- tower ----
plug_r  = 6.0;    // the plug's pocket: plug mouldings and locking collars up to 12 mm across
tie     = [1.8, 5.4];  // the two tunnels for the tie: ties up to 5 x 1.5 mm
tie_y   = 4.5;    // the tunnels open this far above and below the jack's axis
top_ch  = 1.0;    // chamfer round the tower's top

// ---- logo ----
logo_raise = 0.5;
logo_z     = [10, -12];  // the tower's outer face, and the far arm

XI  = -side_gap;            // the near arm's inside face
XO  = -side_gap - arm_t;    // the guard's outer face on the jack's side
FI  = case_w + side_gap;    // the far arm's inside face
FO  = FI + arm_t;           // and outside
YT  = case_h;
TX  = window[0];            // the tower's face towards the BNCs
TZ  = tower_h - top_ch - tie[1] - 0.8;  // the tunnels' near side

$fn = 96;

// -------------------------------------------------------------- 2D

// The plug's pocket, with a 45 degree roof so it prints unsupported.
module pocket2d() translate(jack) {
    circle(r = plug_r);
    rotate(45) square(plug_r);
}

// The plate, less the window: the frame the lip runs round. At the near end
// both start inside the tower, so none of their faces lands on the tower's.
module face2d() difference() {
    translate([XI - 0.5, 0]) square([FI - XI + 0.5, YT]);
    if (!bnc_holes)
        translate([window[0] - 0.5, rail_h]) square([window[1] - window[0] + 0.5, YT]);
    else {
        for (x = bnc_x) translate([x, bnc_y]) circle(r = hole_r);
        // open from the tower to the first BNC, so no thin crescent is left
        // between them; the band stops short of the hole's top and bottom so
        // its edges cut the circle cleanly
        translate([window[0] - 0.5, bnc_y - hole_r + 1]) square([bnc_x[0] - window[0] + 0.5, 2 * hole_r - 2]);
        if (model == "sync")
            translate([usb_room[0], usb_room[2]]) square([usb_room[1] - usb_room[0], usb_room[3] - usb_room[2]]);
        for (p = small) translate(p) circle(r = window_r);
    }
}

// -------------------------------------------------------------- 3D

// 2D (a, b) becomes (X = a, Z = b), extruded over the case's height.
module xz() rotate([90, 0, 0]) translate([0, 0, -YT]) linear_extrude(YT) children();
// 2D (a, b) becomes (Y = a, Z = b), extruded along +X from x0.
module yz(x0, h) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(h) children();

// The plate across the end, and the arms back along both sides to the screws,
// full height so the converter still sits flat. The near corner is inside the
// tower; the far one is bevelled at 45 degrees.
module plate() linear_extrude(plate_t) face2d();
module arms() xz() {
    polygon([[XO, -arm_l], [XI, -arm_l], [XI, 0.5], [XO, 0.5]]);
    polygon([[FI, -arm_l], [FO, -arm_l], [FO, 0], [FO - corner, plate_t],
             [FI - 0.5, plate_t], [FI - 0.5, 0], [FI, 0]]);
}

module lip() translate([0, 0, plate_t - 0.5]) linear_extrude(lip_h + 0.5)
    difference() { face2d(); offset(delta = -lip_w) face2d(); }

module tower() hull() {
    translate([XO, 0, 0]) cube([TX - XO, YT, tower_h - top_ch]);
    translate([XO + top_ch, 0, 0]) cube([TX - XO - 2 * top_ch, YT - top_ch, tower_h]);
}

// The tie goes in at the outer face, through one tunnel to the pocket, round
// the plug's boot and back out through the other.
module tunnels() for (y = [jack[1] + tie_y, jack[1] - tie_y])
    translate([XO - 1, y - tie[0] / 2, TZ]) cube([jack[0] - XO + 1, tie[0], tie[1]]);

module arm_chamfers() for (x = [XO - 1, FI - 1]) yz(x, arm_t + 2) for (s = [0, 1])
    polygon(s == 0 ? [[-1, -arm_l - 1], [arm_ch + 1, -arm_l - 1], [-1, -arm_l + arm_ch + 1]]
                   : [[YT + 1, -arm_l - 1], [YT - arm_ch - 1, -arm_l - 1], [YT + 1, -arm_l + arm_ch + 1]]);

// Each arm's screw: a slot along the case, countersunk on the outside. The
// countersink's cone starts inside the bore and overshoots the face, half a
// facet round, so it leaves no slivers where it meets them.
csink_in  = (csink_d - hole_d) / 2 + 0.2;  // cone starts 0.2 mm into the bore
csink_out = 0.5;                           // and ends this far outside the face
module screw_slot(x_out, dir) {  // dir: +1 when the outside faces +X
    hull() for (u = [-slot, slot], w = [-slot_y, slot_y])
        translate([x_out - dir * (arm_t + 1), screw_y + w, -screw_z + u])
            rotate([0, dir * 90, 0]) cylinder(d = hole_d, h = arm_t + 2);
    hull() for (u = [-slot, slot], w = [-slot_y, slot_y])
        translate([x_out - dir * csink_in, screw_y + w, -screw_z + u])
            rotate([0, dir * 90, 0]) rotate(180 / $fn)
                cylinder(d1 = hole_d - 0.4, d2 = csink_d + 2 * csink_out, h = csink_in + csink_out);
}

module vees() for (x = [XO - 1, FI - 1]) yz(x, arm_t + 2) for (z = vee_z)
    polygon([[YT + 1, z - vee - 1], [YT + 1, z + vee + 1], [YT - vee, z]]);

module reliefs() for (x = [XI, FI]) translate([x, -1, 0]) rotate([-90, 0, 0]) rotate(45)
    cylinder(r = relief, h = YT + 2, $fn = 4);

// Upright to someone looking at that side of the converter, label up.
module logo(depth_in = 0.3) {
    translate([XO, YT / 2, logo_z[0]]) rotate([0, -90, 0])
        translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();
    translate([FO, YT / 2, logo_z[1]]) rotate([0, 90, 0])
        translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();
}

module body() difference() {
    union() { plate(); arms(); lip(); tower(); }
    translate([0, 0, -1]) linear_extrude(tower_h + 2) pocket2d();
    tunnels();
    arm_chamfers();
    screw_slot(XO, -1);
    screw_slot(FO, 1);
    vees();
    reliefs();
}

module posed() if (pose == "print") rotate([90, 0, 0]) children();
               else children();

if (part == "guard") posed() union() { body(); logo(); }
else if (part == "body") posed() body();
else if (part == "logo") posed() logo(0);
