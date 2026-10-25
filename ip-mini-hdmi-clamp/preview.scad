// README pictures, from the STLs. Run ./previews.sh.
//   view = "part":   the clamp as printed, logo in navy
//   view = "fitted": on a stand-in converter, HDMI plugged in and tied
// The STLs are in their print pose, which is also the converter lying label
// up with its HDMI end towards -Y, so the stand-in is turned the same way.

include <ip_mini_hdmi_clamp.scad>   // for the converter's numbers only

view = "part";
part = "none";                       // stops the include drawing the clamp itself

pale = [0.86, 0.86, 0.84];
navy = [14, 41, 66] / 255;

module clamp() {
    color(pale) import("ip_mini_hdmi_clamp_v0.1-body.stl", convexity = 10);
    color(navy) import("ip_mini_hdmi_clamp_v0.1-logo.stl", convexity = 10);
}

// Not to scale beyond what the clamp touches: the case and its recessed end
// panel, the vents, the port, the screws, and the plug, cable and cable tie.
case_l = 119.4;
recess = 0.5;
module converter() {
    color([0.12, 0.12, 0.13]) difference() {
        translate([-end[0] / 2, YB, -case_l]) cube([end[0], end[1], case_l]);
        translate([-end[0] / 2 + rim, YB - 1, -recess]) cube([end[0] - 2 * rim, end[1] - rim + 1 - 0.1, 1]);
        for (row = [0:2], i = [-9:9]) {
            x = i * 3.45 + (row % 2) * 1.725;
            y = 3.3 + row * 3.0;
            if (abs(x) < 29) translate([x, y, -4]) rotate(30) cylinder(d = 2.9, h = 5, $fn = 6);
        }
        translate([hdmi[0], hdmi[1], -6]) linear_extrude(6) offset(r = 0.3) square([14.4, 4.7], center = true);
    }
    color([0.6, 0.6, 0.62]) for (p = screws)
        translate([p[0], p[1], plate_t - 0.2 - (csink_d - 0.6 - 2) / 2])
            cylinder(d1 = 2.4, d2 = csink_d - 0.6, h = (csink_d - 0.6 - 2.4) / 2);
    color([0.08, 0.08, 0.08]) {
        translate([hdmi[0] - 10, hdmi[1] - 5.5, -recess]) cube([20, 11, 34]);
        translate([hdmi[0], hdmi[1], 33]) cylinder(d = cable_d, h = 60);
    }
    // the cable tie: over the cable, down the slots, under the bar's middle
    tz = tie_z + bar_l / 2;
    sx = trough_r + slot[0] / 2;
    color([0.95, 0.95, 0.92]) translate([hdmi[0], 0, tz - 2.3]) {
        intersection() {
            translate([0, hdmi[1], 0]) difference() {
                cylinder(r = cable_d / 2 + 1.1, h = 4.6);
                translate([0, 0, -1]) cylinder(r = cable_d / 2 + 0.05, h = 7);
            }
            translate([-20, hdmi[1], -1]) cube([40, 20, 7]);
        }
        for (s = [-1, 1]) hull() {
            translate([s * (cable_d / 2 + 0.55) - 0.55, hdmi[1] - 0.01, 0]) cube([1.1, 0.01, 4.6]);
            translate([s * sx - 0.55, trough_y, 0]) cube([1.1, 0.01, 4.6]);
        }
        for (s = [-1, 1]) translate([s * sx - 0.55, bar_bot - 1.1, 0]) cube([1.1, trough_y - bar_bot + 1.1, 4.6]);
        translate([-sx - 0.55, bar_bot - 1.1, 0]) cube([2 * sx + 1.1, 1.1, 4.6]);
    }
}

if (view == "part") clamp();
else { clamp(); translate([0, 0, -YB]) rotate([90, 0, 0]) converter(); }
