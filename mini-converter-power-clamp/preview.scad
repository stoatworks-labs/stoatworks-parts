// README pictures, from the STLs. Run ./previews.sh.
//   view = "part":   the clamp as printed, logo in navy
//   view = "fitted": on a stand-in Sync Generator, the tightest of the three,
//                    with the DC plug tied in and a BNC plug in the nearest REF OUT
// The STLs are in their print pose, which is also the converter lying on its
// underside with its power end towards -Y, so the stand-in is turned the same way.

include <mini_converter_power_clamp.scad>   // for the converter's numbers only

view = "part";
part = "none";                               // stops the include drawing the clamp itself

pale = [0.86, 0.86, 0.84];
navy = [14, 41, 66] / 255;
dark = [0.12, 0.12, 0.13];
metal = [0.72, 0.72, 0.74];
black = [0.08, 0.08, 0.08];

module clamp() {
    color(pale) import("mini_converter_power_clamp_v0.1-body.stl", convexity = 10);
    color(navy) import("mini_converter_power_clamp_v0.1-logo.stl", convexity = 10);
}

bncs = [24.15, 38.74, 53.34];   // the Sync Generator's REF OUTs on this end
bnc_y = 12.4;

// Not to scale beyond what the clamp touches: the case and its recessed end
// panel, the jack, the BNCs, the side screws, the DC plug, its cable and tie,
// and a BNC plug.
module converter() {
    color(dark) difference() {
        translate([0, 0, -case_l]) cube([case_w, case_h, case_l]);
        translate([0.9, -1, -recess]) cube([case_w - 1.8, case_h - 1.0 + 1, recess + 1]);
        translate([jack[0], jack[1], -recess - 5]) cylinder(d = 8, h = 6);
    }
    color(metal) {
        for (x = bncs) translate([x, bnc_y, -recess]) {
            cylinder(d = 13.7 / cos(30), h = 2.2, $fn = 6);
            cylinder(d = 9.6, h = 13);
        }
        // the side screws' heads, flush in the arm's countersinks
        for (z = screw_z) translate([XO + 0.2, screw_y, -z]) rotate([0, 90, 0]) cylinder(d1 = 6.0, d2 = 3.0, h = 1.5);
    }
    // the DC plug, its boot and cable, on the jack's axis
    color(black) translate([jack[0], jack[1], -recess]) {
        cylinder(d = 10, h = 28);
        translate([0, 0, 28]) cylinder(d1 = 8, d2 = cable_d, h = 8);
        cylinder(d = cable_d, h = L + 30);
    }
    // a BNC plug in the nearest REF OUT, and its coax
    color([0.55, 0.55, 0.58]) translate([bncs[0], bnc_y, 0]) cylinder(d = 14.3, h = 14);
    color(black) translate([bncs[0], bnc_y, 14]) {
        cylinder(d = 10, h = 18);
        translate([0, 0, 18]) cylinder(d1 = 10, d2 = 6.5, h = 22);
        cylinder(d = 6, h = 75);
    }
    tie_();
}

// The cable tie: in at the outer face through the upper tunnel, round the
// cable, back through the lower one, buckle on the outer face.
module tie_() color([0.95, 0.95, 0.92]) translate([0, 0, TZ + 0.3]) linear_extrude(tie[1] - 0.6) {
    up = G_TOP - 0.4 + tie[0] / 2;
    lo = G_BOT + 0.4 - tie[0] / 2;
    cx = GB + cable_d / 2;
    for (y = [up, lo]) translate([XO - 0.6, y - 0.55]) square([GF - XO + 0.6, 1.1]);
    difference() {
        hull() { translate([cx, jack[1]]) circle(d = cable_d + 2.2); translate([GF - 0.1, lo - 0.55]) square([0.1, up - lo + 1.1]); }
        hull() { translate([cx, jack[1]]) circle(d = cable_d + 0.1); translate([GF - 1, lo + 0.55]) square([0.1, up - lo - 1.1]); }
        translate([XO - 5, lo + 0.55]) square([GF - XO + 4.9, up - lo - 1.1]);
    }
    translate([XO - 0.6 - 1.1, lo - 0.55]) square([1.1, up - lo + 1.1]);
    translate([XO - 0.6 - 4.5, (up + lo) / 2 - 2.5]) square([3.4, 5]);   // the buckle
}

if (view == "part") clamp();
else { clamp(); rotate([90, 0, 0]) converter(); }
