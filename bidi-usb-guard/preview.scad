// README pictures, from the STLs. Run ./previews.sh.
//   view = "part":   the guard as printed, logo in navy
//   view = "fitted": on a stand-in converter end, plug in, LEDs lit

include <bidi_usb_guard.scad>   // for the converter's numbers only

view = "part";
part = "none";                   // stops the include drawing the guard itself

pale = [0.86, 0.86, 0.84];
navy = [14, 41, 66] / 255;

module guard() {
    color(pale) import("bidi_usb_guard_v0.1-body.stl", convexity = 10);
    color(navy) import("bidi_usb_guard_v0.1-logo.stl", convexity = 10);
}

// Not to scale beyond what the guard touches: the end panel, the BNC nuts and
// barrels, the plug body and cable, and the two LEDs.
module converter() {
    color([0.32, 0.33, 0.35]) translate([-58.93 / 2, -24.89 / 2, -40]) cube([58.93, 24.89, 39.9]);
    for (b = bnc) translate([b[0], b[1], 0]) {
        color([0.8, 0.8, 0.82]) translate([0, 0, plate_t + 0.05]) cylinder(d = 15.4, h = 2.5, $fn = 6);
        color([0.75, 0.75, 0.78]) cylinder(d = 10.8, h = 14);
    }
    color([0.1, 0.1, 0.1]) {
        translate([pocket_x[0] + 0.5, pocket_y0 + 0.3, 0]) cube([12.4, 6.8, pocket_h - 0.4]);
        translate([slot_c[0], slot_c[1] + 0.2, pocket_h - 1]) cylinder(d = 4, h = 30);
    }
    for (l = [led_lock, led_pwr]) color([1, 0.95, 0.75]) translate([l[0], l[1], -0.05])
        cylinder(d = led_d, h = 0.1);
}

if (view == "part") guard();
else { guard(); converter(); }
