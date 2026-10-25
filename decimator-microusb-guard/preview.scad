// README pictures, from the STLs. Run ./previews.sh.
//   view = "part":   the guard as printed, logo in navy
//   view = "fitted": on a stand-in MD-LX end, plug in, screws in

include <decimator_microusb_guard.scad>   // for the MD-LX's numbers only

view = "part";
part = "none";                        // stops the include drawing the guard itself

pale = [0.86, 0.86, 0.84];
navy = [14, 41, 66] / 255;

module guard() {
    color(pale) import("decimator_microusb_guard_v0.1-body.stl", convexity = 10);
    color(navy) import("decimator_microusb_guard_v0.1-logo.stl", convexity = 10);
}

// Only what the guard touches: the end panel, the BNCs, the plug and the screws.
module mdlx() {
    color([0.78, 0.12, 0.12]) translate([-30, -11.5, -40]) cube([60, 23, 39.9]);
    for (b = bnc) translate([b[0], b[1], 0]) color([0.85, 0.68, 0.25]) {
        cylinder(d = flange_d, h = 2.2);
        cylinder(d = 11, h = 16);
    }
    color([0.1, 0.1, 0.1]) {
        translate([usb[0] - plug[0] / 2 + 0.2, usb[1] - plug[1] / 2 + 0.2, 0])
            cube([plug[0] - 0.4, plug[1] - 0.4, body_h - 0.2]);
        translate([usb[0], usb[1], body_h - 0.2]) cylinder(d1 = 5.6, d2 = 3.6, h = 8);
        translate([usb[0], usb[1], body_h]) cylinder(d = 3.6, h = 30);
    }
    color([0.95, 0.85, 0.6]) translate([hole_led[0], hole_led[1], -0.05]) cylinder(d = 1.8, h = 0.1);
    for (s = screws) color([0.8, 0.8, 0.82]) translate([s[0], s[1], plate_t - 1.2])
        cylinder(d1 = screw_d, d2 = csink_d - 0.1, h = 1.19);
}

if (view == "part") guard();
else { guard(); mdlx(); }
