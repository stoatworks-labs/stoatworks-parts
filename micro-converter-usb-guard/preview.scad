// README pictures, from the STLs. Run ./previews.sh.
//   view = "part":   the guard as printed, logo in navy
//   view = "fitted": on a stand-in converter, cables in, LED lit
// The STLs are in their print pose, which is also the converter lying label
// up with its HDMI end towards -Y, so the stand-in is turned the same way.

include <micro_converter_usb_guard.scad>   // for the converter's numbers only

view = "part";
part = "none";                   // stops the include drawing the guard itself

pale = [0.86, 0.86, 0.84];
navy = [14, 41, 66] / 255;

module guard() {
    color(pale) import("micro_converter_usb_guard_v0.1-body.stl", convexity = 10);
    color(navy) import("micro_converter_usb_guard_v0.1-logo.stl", convexity = 10);
}

// Not to scale beyond what the guard touches: the case, its recessed end
// panel, the ports and LED, the side screws, and the two plugs and cables.
case_l = 60.2;
recess = 0.8;
rim    = [1.2, 0.9];
module converter() {
    color([0.32, 0.33, 0.35]) difference() {
        translate([-case_w / 2, YB, -case_l]) cube([case_w, case_h, case_l]);
        translate([-case_w / 2 + rim[0], YB + rim[1], -recess])
            cube([case_w - 2 * rim[0], case_h - 2 * rim[1], 1]);
        translate([hdmi[0], hdmi[1], -6]) linear_extrude(6) offset(r = 0.4) square([14.2, 4.6], center = true);
        translate([usbc[0], usbc[1], -6]) linear_extrude(6)
            hull() for (s = [-1, 1]) translate([s * 2.85, 0]) circle(d = 3.2);
    }
    color([1, 0.95, 0.75]) translate([led[0], led[1], -recess - 0.05]) cylinder(d = led_d, h = 0.1);
    // the side screws: this end's pair through the arms, the far pair in the case
    color([0.75, 0.75, 0.78]) for (s = [-1, 1]) {
        translate([s * XO, screw_y, screw_z]) rotate([0, s * 90, 0]) translate([0, 0, -1.7])
            cylinder(d1 = 3, d2 = 6, h = 1.5);
        translate([s * case_w / 2, screw_y, -52.1]) rotate([0, s * 90, 0]) translate([0, 0, -1.5])
            cylinder(d1 = 3, d2 = 6, h = 1.5);
    }
    color([0.1, 0.1, 0.1]) {
        translate([usbc[0] - 6.2, usbc[1] - 3.4, -recess]) cube([12.4, 6.8, 18.0]);
        translate([usbc[0], usbc[1], 16]) cylinder(d = 4, h = 40);
        translate([hdmi[0] - 10.5, hdmi[1] - 5.5, -recess]) cube([21, 11, 32]);
        translate([hdmi[0], hdmi[1], 30]) cylinder(d = 7, h = 26);
    }
}

if (view == "part") guard();
else { guard(); translate([0, 0, -YB]) rotate([90, 0, 0]) converter(); }
