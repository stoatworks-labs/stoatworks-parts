// IP Mini HDMI clamp: an HDMI cable clamp for the HDMI end of a Blackmagic
// 2110 IP Mini IP to HDMI (and its SFP version). A plate takes the two screws
// either side of the HDMI port, below the vents. From it a channel runs out
// under the HDMI plug, a wall either side of the plug's moulding, to a bar
// beyond it. The cable is tied to the bar, in a trough at its own height, so
// a tug on the lead pulls on the case's screws, not on the port.
//
// Origin: centre of the HDMI end, Z = 0 on the end panel, Z out along the
// cable. X runs across the end, Y up it (the vents and the label side are +Y).
// The STL is turned to print: the converter's underside goes on the bed, and
// every part of the clamp starts there (see posed()).
//
//   openscad -o ip_mini_hdmi_clamp_v0.1.stl ip_mini_hdmi_clamp.scad
//   openscad -o ip_mini_hdmi_clamp_v0.1-body.stl -D 'part="body"' ip_mini_hdmi_clamp.scad
//   openscad -o ip_mini_hdmi_clamp_v0.1-logo.stl -D 'part="logo"' ip_mini_hdmi_clamp.scad

include <stoatworks_mark.scad>

part = "clamp";   // clamp | body (no logo) | logo (for a second colour) | none
pose = "print";   // print | fitted (the converter's frame, for pictures and checks)

/* [Fit] */
screw   = "M2.5"; // the end panel's two screws: "M2", "M2.5" or "M3"
cable_d = 7.0;    // the HDMI cable's diameter where it is tied
tie_z   = 42;     // the tie bar starts this far out: past the end of the plug's moulding

// ---- the converter (see README for where each number came from) ----
end      = [66.04, 27.94];  // 2.6 x 1.1 in
rim      = 1.24;            // the case's sides stand round the end panel this wide
hdmi     = [0.11, -3.83];   // HDMI port centre
screws   = [[-19.89, -3.68], [19.89, -3.68]];
vents_y  = 1.7;             // the vents start this far up and run to the top
moulding = [24.2, 14.2];    // the biggest HDMI plug moulding the channel takes

// ---- plate ----
plate_t   = 2.0;    // the screws must be this much longer than the originals
plate_x   = 31.0;   // half-width: 0.8 mm inside the case's rim
plate_top = 1.0;    // 0.7 mm under the vents; the walls stop here too
corner    = 2.0;    // chamfers on the plate's corners
lip_w     = 1.0;    // raised rim round the outer face
lip_h     = 1.0;
vee       = 1.2;    // 90 degree notches along the bottom edge
vee_x     = [-28, -22, 22, 28];
// clearance hole and 90 degree countersink for each size of flat head
csinks = [["M2", 2.4, 4.0], ["M2.5", 2.9, 5.0], ["M3", 3.4, 6.4]];

// ---- channel ----
gap     = 0.3;      // round the biggest moulding
wall_t  = 2.0;
wall_ch = 3.0;      // chamfer on the walls' far top corners
gusset  = 2.5;      // 45 degree fillet at each wall's outside foot; stops clear of the screw heads
fillet  = 1.0;      // and inside, between wall and floor
floor_gap = 3.0;    // the floor stops this far short of the bar, for the tie

// ---- tie bar ----
bar_l    = 9.0;     // along the cable
bar_bot  = -10.8;   // the tie passes under the bar's middle, through the gap to the bed
trough_r = 5.0;     // takes cables up to 10 mm
slot     = [1.8, 5.4];  // tie slots either side of the trough: ties up to 5 x 1.5 mm

// ---- logo ----
logo_raise = 0.5;
logo_z     = 22;    // on both walls' outer faces

YB = -end[1] / 2;
WI = moulding[0] / 2 + gap;   // the walls' inside faces, from the HDMI's centre line
WO = WI + wall_t;             // and outside
floor_top = hdmi[1] - moulding[1] / 2 - gap;
L  = tie_z + bar_l;           // the channel's length
trough_y  = hdmi[1] - cable_d / 2;  // the cable rests here, centred on the port
cs = csinks[search([screw], csinks)[0]];
hole_d  = cs[1];
csink_d = cs[2];

$fn = 96;

// -------------------------------------------------------------- 2D

module chamfered_rect(x0, y0, x1, y1, c)
    polygon([[x0 + c, y0], [x1 - c, y0], [x1, y0 + c], [x1, y1 - c],
             [x1 - c, y1], [x0 + c, y1], [x0, y1 - c], [x0, y0 + c]]);

module face() chamfered_rect(-plate_x, YB, plate_x, plate_top, corner);

// Between the walls, above the floor: where the HDMI plug goes.
module opening() translate([hdmi[0] - WI, floor_top]) square([2 * WI, plate_top - floor_top + 1]);

module vees() for (x = vee_x)
    polygon([[x - vee - 1, YB - 1], [x + vee + 1, YB - 1], [x, YB + vee]]);

// A U, round at the bottom where the cable rests, open at the top.
module trough() translate([hdmi[0], trough_y + trough_r]) {
    circle(r = trough_r);
    translate([-trough_r, 0]) square([2 * trough_r, plate_top - trough_y]);
}

// -------------------------------------------------------------- 3D

module plate() difference() {
    union() {
        linear_extrude(plate_t) face();
        translate([0, 0, plate_t - 0.5]) linear_extrude(lip_h + 0.5)
            difference() { face(); offset(delta = -lip_w) face(); }
    }
    translate([0, 0, -1]) linear_extrude(plate_t + lip_h + 1) opening();
}

module walls() for (s = [-1, 1]) difference() {
    translate([hdmi[0] + (s > 0 ? WI : -WO), YB, 0]) cube([wall_t, plate_top - YB, L]);
    // the far top corner
    translate([hdmi[0] - WO - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(2 * WO + 2)
        polygon([[plate_top - wall_ch - 1, L + 1], [plate_top + 1, L + 1],
                 [plate_top + 1, L - wall_ch - 1]]);
}

module floor_() translate([hdmi[0] - WO, YB, 0]) cube([2 * WO, floor_top - YB, tie_z - floor_gap]);

// 45 degree fillets: outside, where each wall meets the plate; inside, where
// it meets the floor.
module fillets() for (s = [-1, 1]) {
    xo = hdmi[0] + s * WO;
    xi = hdmi[0] + s * WI;
    // from the underside up, so its bottom face lands exactly on the walls'
    translate([0, YB, 0]) rotate([-90, 0, 0]) linear_extrude(plate_top - YB)
        polygon([[xo - s * 0.5, 0.5 - plate_t], [xo + s * gusset, 0.5 - plate_t],
                 [xo + s * gusset, -plate_t], [xo, -plate_t - gusset],
                 [xo - s * 0.5, -plate_t - gusset - 0.5]]);
    linear_extrude(tie_z - floor_gap)
        polygon([[xi + s * 0.3, floor_top - 0.3], [xi + s * 0.3, floor_top + fillet + 0.3],
                 [xi, floor_top + fillet], [xi - s * fillet, floor_top],
                 [xi - s * fillet, floor_top - 0.3]]);
}

// Across the channel's far end. The cable lies in the trough; a cable tie goes
// over it, down one slot, under the bar's middle and up the other.
module bar() difference() {
    translate([hdmi[0] - WI - 0.5, bar_bot, tie_z]) cube([2 * WI + 1, plate_top - bar_bot, bar_l]);
    translate([0, 0, tie_z - 1]) linear_extrude(bar_l + 2) trough();
    for (s = [-1, 1])
        translate([hdmi[0] + s * (trough_r + slot[0] / 2) - slot[0] / 2, bar_bot - 1,
                   tie_z + (bar_l - slot[1]) / 2])
            cube([slot[0], plate_top - bar_bot + 2, slot[1]]);
}

// The countersink's cone starts inside the bore and overshoots the face, half
// a facet round, so it leaves no slivers where it meets them.
csink_in  = (csink_d - hole_d) / 2 + 0.2;
csink_out = 0.5;
module screw_holes() for (p = screws) translate([p[0], p[1], 0]) {
    translate([0, 0, -1]) cylinder(d = hole_d, h = plate_t + 2);
    translate([0, 0, plate_t - csink_in]) rotate(180 / $fn)
        cylinder(d1 = hole_d - 0.4, d2 = csink_d + 2 * csink_out, h = csink_in + csink_out);
}

// Upright to someone looking at the side of the converter, label up.
module logo(depth_in = 0.3) for (s = [-1, 1])
    translate([hdmi[0] + s * WO, (YB + plate_top) / 2, logo_z]) rotate([0, s * 90, 0])
        translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();

module body() difference() {
    union() { plate(); walls(); floor_(); fillets(); bar(); }
    screw_holes();
    translate([0, 0, -1]) linear_extrude(plate_t + lip_h + 2) vees();
}

module posed() if (pose == "print") translate([0, 0, -YB]) rotate([90, 0, 0]) children();
               else children();

if (part == "clamp") posed() union() { body(); logo(); }
else if (part == "body") posed() body();
else if (part == "logo") posed() logo(0);
