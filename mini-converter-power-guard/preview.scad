// README pictures, from the STLs. Run ./previews.sh.
//   view = "part":   the guard as printed, logo in navy
//   view = "fitted": on a stand-in converter (model = "da" or "sync"), with
//                    the 12 V plug tied in and BNC plugs in the BNCs
// The STLs are in their print pose, which is also the converter lying on its
// underside with its power end towards -Y, so the stand-in is turned the same way.

include <mini_converter_power_guard.scad>   // for the converter's numbers only

view  = "part";
model = "da";
part  = "none";                              // stops the include drawing the guard itself
stl   = "mini_converter_power_guard_v0.1";   // which STLs to show (previews.sh points it at a bnc_holes pair)

pale  = [0.86, 0.86, 0.84];
navy  = [14, 41, 66] / 255;
dark  = [0.12, 0.12, 0.13];
metal = [0.72, 0.72, 0.74];
black = [0.08, 0.08, 0.08];

bncs  = bnc_x;                                // and bnc_y, from the include
plugged = model == "da" ? [0, 1, 3] : [0, 2];   // which BNCs have a plug in

module guard() {
    color(pale) import(str(stl, "-body.stl"), convexity = 10);
    color(navy) import(str(stl, "-logo.stl"), convexity = 10);
}

// Not to scale beyond what the guard touches: the case and its recessed end
// panel, the jack, the BNCs with their nuts, the USB port, the side screws,
// the 12 V plug and its tie, and the BNC plugs.
module converter() {
    color(dark) difference() {
        translate([0, 0, -case_l]) cube([case_w, case_h, case_l]);
        translate([0.9, -1, -recess]) cube([case_w - 1.8, case_h - 0.9 + 1, recess + 1]);
        translate([jack[0], jack[1], -recess - 5]) cylinder(d = 8.8, h = 6);
        if (model == "sync") translate([79.4 - 3.9, 8.8 - 2, -recess - 5]) cube([7.8, 4, 6]);
    }
    color(metal) {
        for (x = bncs) translate([x, bnc_y, -recess]) {
            cylinder(d = 12.7 / cos(30), h = 2.4, $fn = 6);
            cylinder(d = 9.6, h = 14.4);
        }
        for (x = [XO + 0.2, FO - 0.2]) translate([x, screw_y, -screw_z])
            rotate([0, x < 0 ? 90 : -90, 0]) cylinder(d1 = 6.0, d2 = 3.0, h = 1.5);
    }
    // BNC plugs and their coax
    for (i = plugged) translate([bncs[i], bnc_y, 0]) {
        color([0.55, 0.55, 0.58]) cylinder(d = 14.3, h = 14);
        color(black) translate([0, 0, 14]) {
            cylinder(d = 10, h = 18);
            translate([0, 0, 18]) cylinder(d1 = 10, d2 = 6.5, h = 22);
            cylinder(d = 6, h = 75);
        }
    }
    // Blackmagic's locking 12 V plug: barrel, knurled collar, body, ribbed boot, cable
    translate([jack[0], jack[1], -recess]) {
        color(metal) cylinder(d = 10.4, h = 9);
        color(black) {
            translate([0, 0, 9]) cylinder(d = 9, h = 12);
            translate([0, 0, 21]) cylinder(d1 = 8, d2 = 5, h = 12);
            cylinder(d = 3.8, h = 80);
        }
    }
    tie_();
}

// The cable tie: in at the outer face through the upper tunnel, round the
// plug's boot (pulled against the pocket's outer side), back through the lower
// tunnel, buckle on the outer face.
boot_d = 7.0;
module tie_() color([0.95, 0.95, 0.92]) translate([0, 0, TZ + 0.3]) linear_extrude(tie[1] - 0.6) {
    up = jack[1] + tie_y;
    lo = jack[1] - tie_y;
    cx = jack[0] - plug_r + boot_d / 2;
    ex = jack[0] - plug_r + 1.2;
    for (y = [up, lo]) translate([XO - 0.6, y - 0.55]) square([ex - XO + 0.6, 1.1]);
    difference() {
        hull() { translate([cx, jack[1]]) circle(d = boot_d + 2.2); translate([ex - 0.1, lo - 0.55]) square([0.1, up - lo + 1.1]); }
        hull() { translate([cx, jack[1]]) circle(d = boot_d + 0.1); translate([ex - 1, lo + 0.55]) square([0.1, up - lo - 1.1]); }
        translate([XO - 5, lo + 0.55]) square([ex - XO + 4.9, up - lo - 1.1]);
    }
    translate([XO - 0.6 - 1.1, lo - 0.55]) square([1.1, up - lo + 1.1]);
    translate([XO - 0.6 - 4.5, (up + lo) / 2 - 2.5]) square([3.4, 5]);   // the buckle
}

if (view == "part") guard();
else { guard(); rotate([90, 0, 0]) converter(); }
