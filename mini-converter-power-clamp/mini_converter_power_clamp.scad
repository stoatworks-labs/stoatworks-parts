// Mini Converter power clamp: a strain relief for the 12 V lead of Blackmagic's
// Mini Converter SDI Distribution, SDI Distribution 4K and Sync Generator. Their
// power jack is unlatched, in the corner of a BNC end. An arm takes the two case
// screws on the jack's side. From it a spine runs out beside the plug, with a
// floor under it, to a block past the plug's moulding. The cable is tied into a
// groove in the block on the jack's own axis, so a tug on the lead pulls on the
// case's screws, not on the jack. Everything stays on the jack's side of its
// axis or below the plug: on the Sync Generator the nearest BNC is 12 mm away.
//
// Origin: the case's corner at the power end, on its underside. X runs across
// the end from the side the jack is near (+X towards the BNCs), Y up, Z = 0 on
// the case's front edge and out along the cable. The STL is turned to print: the
// converter's underside goes on the bed, and every part of the clamp starts there
// (see posed()).
//
//   openscad -o mini_converter_power_clamp_v0.1.stl mini_converter_power_clamp.scad
//   openscad -o mini_converter_power_clamp_v0.1-body.stl -D 'part="body"' mini_converter_power_clamp.scad
//   openscad -o mini_converter_power_clamp_v0.1-logo.stl -D 'part="logo"' mini_converter_power_clamp.scad

include <stoatworks_mark.scad>

part = "clamp";   // clamp | body (no logo) | logo (for a second colour) | none
pose = "print";   // print | fitted (the converter's frame, for pictures and checks)

/* [Fit] */
screw_z  = [24.1, 72.5]; // the two side screws on the jack's side, back from the front edge
screw_y  = 11.8;         // their height off the underside (the far one measures higher)
cable_d  = 4.5;          // the DC cable's diameter where it is tied
tie_z    = 40;           // the tie block starts this far out: past the plug's moulding and boot
side_gap = 0.2;          // between the case and the arm

// ---- the converter (see README for where each number came from) ----
case_h  = 22.9;          // 0.90 in
case_w  = 92.2;          // across the end, 3.63 in
case_l  = 96.9;          // along the side, without the BNCs
jack    = [11.9, 12.4];  // the DC jack's centre, from the side and the underside
recess  = 1.5;           // the end panel sits about this far behind the case's front edge

// ---- arm ----
arm_t   = 2.0;    // the screws must be this much longer than the originals
arm_l   = 78;     // back along the side from the front edge, past the far screw
arm_ch  = 3.0;    // chamfers on its back corners
hole_d  = 3.6;    // M3
csink_d = 6.4;    // 90 degree countersink: an M3 flat head (6.0) sits just under flush
slot    = 1.5;    // each screw hole is a slot, +/- this along the case
slot_y  = 0.6;    //   and +/- this up and down
relief  = 0.6;    // groove in the inside corner, for the case's edge
vee     = 1.2;    // 90 degree notches along the arm's top edge
vee_z   = [-34, -40, -56, -62];

// ---- channel ----
plug_r  = 6.5;    // kept clear round the jack's axis: plug mouldings up to 13 mm across
floor_x = 17.5;   // the floor's inner edge, under the far side of the plug
fillet  = 1.5;    // 45 degree fillet where the floor meets the spine
edge_ch = 1.0;    // chamfer on the floor's top inner edge and round the block's front

// ---- tie block ----
block_l  = 9.0;   // along the cable
groove_r = 3.5;   // the cable's groove: cables 3.5 to 6 mm
groove_d = 2.5;   // its depth, so even a 3.5 mm cable stands 1 mm proud for the tie
tie      = [1.8, 5.4];  // the two tunnels for the tie: ties up to 5 x 1.5 mm

// ---- logo ----
logo_raise = 0.5;
logo_z     = [20, -48.3];  // on the outer face: the spine, and the arm between the screws

XI  = -side_gap;            // the arm's inside face
XO  = -side_gap - arm_t;    // the clamp's outer face, arm and spine alike
YT  = case_h;
SI  = jack[0] - plug_r;     // the spine's inside face
FT  = jack[1] - plug_r;     // the floor's top
L   = tie_z + block_l;      // how far the clamp reaches out
GB  = jack[0] - cable_d / 2;    // the groove's deepest point: a cable_d cable lies on the jack's axis
GC  = [GB + groove_r, jack[1]]; // the groove's centre
GF  = GB + groove_d;            // the block's inside face, where the groove opens
g45 = groove_r / sqrt(2);
G_TOP = jack[1] + g45 + (GF - (GC[0] - g45));          // the groove's roof meets the face here
G_BOT = jack[1] - sqrt(pow(groove_r, 2) - pow(GC[0] - GF, 2));  // and its floor here
TZ  = tie_z + (block_l - tie[1]) / 2;  // the tunnels' near side

$fn = 96;

// -------------------------------------------------------------- 2D

// The groove's profile across the cable: round where the cable lies, with a
// 45 degree roof from the round's upper back quarter, so it prints unsupported.
module groove2d() {
    translate(GC) circle(r = groove_r);
    polygon([[GC[0] - g45, GC[1] + g45], [GC[0] - g45 + 20, GC[1] + g45 + 20],
             [GC[0] + 20, GC[1]], [GC[0] - g45, GC[1]]]);
}

// The floor, chamfered along its top inner edge.
module floor2d()
    polygon([[SI - 0.5, 0], [floor_x, 0], [floor_x, FT - edge_ch],
             [floor_x - edge_ch, FT], [SI - 0.5, FT]]);

// A 45 degree fillet between the floor's top and the spine's inside face.
module fillet2d()
    polygon([[SI - 0.5, FT - 0.5], [SI + fillet + 0.5, FT - 0.5], [SI + fillet, FT],
             [SI, FT + fillet], [SI - 0.5, FT + fillet + 0.5]]);

// -------------------------------------------------------------- 3D

// 2D (a, b) becomes (Y = a, Z = b), extruded along +X.
module yz(x0, h) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(h) children();
// 2D (a, b) becomes (X = a, Z = b), extruded along -Y from y0.
module xz(y0, h) translate([0, y0, 0]) rotate([90, 0, 0]) linear_extrude(h) children();

// Along the case's side, back past both screws. Its back corners are chamfered.
module arm() yz(XO, arm_t)
    polygon([[0, -arm_l + arm_ch], [arm_ch, -arm_l], [YT - arm_ch, -arm_l],
             [YT, -arm_l + arm_ch], [YT, 0.5], [0, 0.5]]);

// From the case's front edge out beside the plug, full height, with the floor
// under the plug and the block at the far end.
module spine() translate([XO, 0, 0]) cube([SI - XO, YT, L]);
module floor_() linear_extrude(tie_z + 0.5) { floor2d(); fillet2d(); }
module block() translate([XO, 0, tie_z]) cube([GF - XO, YT, block_l]);

// The tie goes in at the outer face, through one tunnel to the groove, round
// the cable and back through the other: above and below the cable, each
// opening on the groove's edge.
module tunnels() for (y0 = [G_TOP - 0.4, G_BOT + 0.4 - tie[0]])
    translate([XO - 1, y0, TZ]) cube([GF - XO + 2, tie[0], tie[1]]);

module groove() translate([0, 0, tie_z - 1]) linear_extrude(block_l + 2) groove2d();

// The block's front edges.
module chamfers() {
    xz(YT + 1, YT + 2) {
        polygon([[XO - 1, L - edge_ch - 1], [XO + edge_ch + 1, L + 1], [XO - 1, L + 1]]);
        polygon([[GF + 1, L - edge_ch - 1], [GF + 1, L + 1], [GF - edge_ch - 1, L + 1]]);
    }
    yz(XO - 1, GF - XO + 2)
        polygon([[YT - edge_ch - 1, L + 1], [YT + 1, L + 1], [YT + 1, L - edge_ch - 1]]);
}

// Each screw: a slot along the case, countersunk on the outside. The
// countersink's cone starts inside the bore and overshoots the face, half a
// facet round, so it leaves no slivers where it meets them.
csink_in  = (csink_d - hole_d) / 2 + 0.2;  // cone starts 0.2 mm into the bore
csink_out = 0.5;                           // and ends this far outside the face
module screw_slots() for (z = screw_z) {
    hull() for (u = [-slot, slot], w = [-slot_y, slot_y]) translate([XO - 1, screw_y + w, -z + u])
        rotate([0, 90, 0]) cylinder(d = hole_d, h = arm_t + 2);
    hull() for (u = [-slot, slot], w = [-slot_y, slot_y]) translate([XO + csink_in, screw_y + w, -z + u])
        rotate([0, -90, 0]) rotate(180 / $fn)
            cylinder(d1 = hole_d - 0.4, d2 = csink_d + 2 * csink_out, h = csink_in + csink_out);
}

module vees() yz(XO - 1, arm_t + 2) for (z = vee_z)
    polygon([[YT + 1, z - vee - 1], [YT + 1, z + vee + 1], [YT - vee, z]]);

module relief_() translate([XI, -1, 0]) rotate([-90, 0, 0]) rotate(45)
    cylinder(r = relief, h = YT + 2, $fn = 4);

// Upright to someone looking at the side of the converter, label up.
module logo(depth_in = 0.3) for (z = logo_z)
    translate([XO, case_h / 2, z]) rotate([0, -90, 0])
        translate([0, 0, -depth_in]) linear_extrude(logo_raise + depth_in) stoatworks_mark();

module body() difference() {
    union() { arm(); spine(); floor_(); block(); }
    groove();
    tunnels();
    chamfers();
    screw_slots();
    vees();
    relief_();
}

module posed() if (pose == "print") rotate([90, 0, 0]) children();
               else children();

if (part == "clamp") posed() union() { body(); logo(); }
else if (part == "body") posed() body();
else if (part == "logo") posed() logo(0);
