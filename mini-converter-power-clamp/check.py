"""Checks for mini_converter_power_clamp_v0.1.stl.

    python -I check.py

Reads the numbers the checks need from the .scad, so the two stay in step. The
STL is in its print pose; the checks turn it back into the converter's frame
(origin at the case's corner by the power jack, on its underside: X across the
end, Y up, Z out of the end) and test it against a stand-in converter: the case
and its recessed end panel, the jack and a DC plug, the nearest BNC on each
model with a BNC plug in it, the side screws, the cable and a cable tie. Draws
three sections into check_sections.png.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
STL = HERE / "mini_converter_power_clamp_v0.1.stl"
SCAD = (HERE / "mini_converter_power_clamp.scad").read_text()


def v(name):
    m = re.search(rf"^{name}\s*=\s*([^;]+);", SCAD, re.M)
    s = m.group(1).split("//")[0].strip()
    return eval(s.replace("[", "(").replace("]", ")").replace("true", "True"))


H, W, LEN, RECESS = v("case_h"), v("case_w"), v("case_l"), v("recess")
JACK = v("jack")
GAP, ARM_T = v("side_gap"), v("arm_t")
XO = -GAP - ARM_T
PLUG_R, TIE_Z, BLOCK_L = v("plug_r"), v("tie_z"), v("block_l")
L = TIE_Z + BLOCK_L
CABLE_D, GROOVE_R, GROOVE_D = v("cable_d"), v("groove_r"), v("groove_d")
GB = JACK[0] - CABLE_D / 2
GF = GB + GROOVE_D
TIE = v("tie")

# The nearest BNC to the jack on each model, from Blackmagic's top views (README).
# A BNC plug: coupling sleeve 14.3 mm (7.5 with room), crimp body and boot 10 mm,
# coax up to 8 mm. The nut is 15.4 mm across its corners.
BNCS = {"Sync Generator": 24.15, "SDI Distribution (and 4K)": 29.29}
BNC_YS = (10.9, 12.4, 13.9)  # their height is the least certain number: checked at three
SLEEVE_R, SLEEVE_Z, BOOT_R, BOOT_Z, COAX_R, NUT_R = 7.5, 32, 5.0, 55, 4.0, 7.7


def to_converter(m):
    """Print pose -> converter frame: x = x, y = z, z = -y."""
    m = m.copy()
    p = m.vertices
    m.vertices = np.c_[p[:, 0], p[:, 2], -p[:, 1]]
    return m


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


def zcyl(c, r, z0, z1):
    c3 = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=96)
    c3.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return c3


def xcyl(y, z, r, x0, x1):
    c3 = trimesh.creation.cylinder(radius=r, height=x1 - x0, sections=96)
    c3.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    c3.apply_translation([(x0 + x1) / 2, y, z])
    return c3


def common(a, b):
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.0 if r.is_empty else float(r.volume)


def reimports(path):
    """OpenSCAD 2021 refuses an STL with slivers ('mesh is not closed')."""
    with tempfile.TemporaryDirectory() as d:
        scad = Path(d) / "r.scad"
        scad.write_text(f'import("{path}", convexity = 10);\n')
        r = subprocess.run(["openscad", "-o", str(Path(d) / "r.off"), str(scad)],
                           capture_output=True, text=True)
        log = r.stdout + r.stderr
        return r.returncode == 0 and "not closed" not in log and "ERROR" not in log


def main():
    raw = trimesh.load(STL, force="mesh")
    m = to_converter(raw)
    ok = True

    def report(name, good, detail=""):
        nonlocal ok
        ok &= bool(good)
        print(f"{'ok  ' if good else 'FAIL'} {name} {detail}")

    report("closed, one body", m.is_watertight and m.is_winding_consistent
           and len(m.split(only_watertight=False)) == 1,
           f"({len(m.faces)} faces, {m.volume:.0f} mm3, ~{m.volume * 1.14e-3:.1f} g PA6-GF solid)")
    lo, hi = raw.bounds
    s = raw.section(plane_origin=[0, 0, 0.1], plane_normal=[0, 0, 1])
    area = s.to_2D(to_2D=np.eye(4))[0].area if s is not None else 0
    report("as printed: on the bed, nothing below it", abs(lo[2]) < 1e-6,
           f"({hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm, {area:.0f} mm2 on the bed)")
    pairs = cKDTree(raw.vertices).query_pairs(0.01)
    report("no near-duplicate vertices (slivers)", len(pairs) == 0, f"({len(pairs)} pairs within 0.01 mm)")

    lo, hi = m.bounds
    print(f"     overall x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f}, z {lo[2]:.2f}..{hi[2]:.2f}")
    report("flush with the case's underside and top", abs(lo[1]) < 1e-6 and abs(hi[1] - H) < 1e-6)
    case = box(-GAP + 0.01, W, 0, H, -LEN, 0)
    report(f"nothing inside the case, the arm {GAP} mm off its side", common(m, case) < 1e-6)
    panel = box(0, W, 0, H, -RECESS, 0)
    rim = trimesh.boolean.difference([box(0, W, 0, H, -0.05, 0.05), box(0.9, W - 0.9, -1, H - 1.0, -1, 1)],
                                     engine="manifold")
    sl = trimesh.boolean.intersection([m, box(-5, 30, -1, H + 1, 0, 0.05)], engine="manifold")
    on_rim = common(sl, trimesh.boolean.union([rim, box(-5, 0, 0, H, -1, 1)], engine="manifold"))
    report("it bears on the case's front edge round the corner", on_rim > 0,
           f"({on_rim / 0.05:.0f} mm2 at the edge; the end panel is about {RECESS} mm behind it)")

    plug = zcyl(JACK, PLUG_R - 0.01, -RECESS, TIE_Z - 0.01)
    vol = common(m, plug)
    report(f"a plug moulding up to {2 * PLUG_R:.0f} mm across and {TIE_Z:.0f} mm long fits", vol < 1e-6,
           f"({vol:.4f} mm3 in the way)")
    vol = common(m, zcyl(JACK, 4.5, -RECESS, 1))
    report("the jack's opening in the panel is clear", vol < 1e-6)

    for (model, bx), bnc_y in ((mb, y) for mb in BNCS.items() for y in BNC_YS):
        c = (bx, bnc_y)
        env = trimesh.boolean.union([zcyl(c, NUT_R, -RECESS, 1.5), zcyl(c, SLEEVE_R, -RECESS, SLEEVE_Z),
                                     zcyl(c, BOOT_R, SLEEVE_Z - 1, BOOT_Z), zcyl(c, COAX_R, BOOT_Z - 1, 120)],
                                    engine="manifold")
        vol = common(m, env)
        # how close: grow the envelope until it touches
        gap = 0.0
        for g in np.arange(0.1, 6.0, 0.1):
            grown = trimesh.boolean.union([zcyl(c, NUT_R + g, -RECESS, 1.5), zcyl(c, SLEEVE_R + g, -RECESS, SLEEVE_Z),
                                           zcyl(c, BOOT_R + g, SLEEVE_Z - 1, BOOT_Z),
                                           zcyl(c, COAX_R + g, BOOT_Z - 1, 120)], engine="manifold")
            if common(m, grown) > 1e-6:
                break
            gap = g
        report(f"{model}: its nearest BNC (x = {bx}, {bnc_y} up) with a plug in it is clear", vol < 1e-6,
               f"(at least {gap:.1f} mm to spare)")

    # the cable lies in the groove, round its deepest point
    for d in (3.5, 4.0, 4.5, 5.0, 6.0):
        c = (GB + d / 2 + 0.02, JACK[1])
        vol = common(m, zcyl(c, d / 2, TIE_Z - 2, L + 20))
        proud = c[0] + d / 2 - GF
        report(f"a {d} mm cable lies in the groove", vol < 1e-6 and proud >= 0.9,
               f"(its centre {c[0] - JACK[0]:+.2f} mm off the jack's axis, {proud:.1f} mm proud of the face "
               f"for the tie; {vol:.4f} mm3 in the way)")

    # the tie's path: each tunnel clear from the outer face to the groove
    tz = TIE_Z + BLOCK_L / 2
    g45 = GROOVE_R / np.sqrt(2)
    gtop = JACK[1] + g45 + (GF - (GB + GROOVE_R - g45))
    gbot = JACK[1] - np.sqrt(GROOVE_R ** 2 - (GB + GROOVE_R - GF) ** 2)
    for name, y0 in (("upper", gtop - 0.4), ("lower", gbot + 0.4 - TIE[0])):
        vol = common(m, box(XO - 1, GF + 1, y0 + 0.2, y0 + TIE[0] - 0.2, tz - 2.4, tz + 2.4))
        report(f"{name} tie tunnel is clear (1.4 x 4.8 mm)", vol < 1e-6, f"(opens at y {y0:.2f}..{y0 + TIE[0]:.2f})")
    # the tie's loop round a 6 mm cable, 1.5 mm thick, against the BNC boots
    loop_x = GB + 6.0 + 1.5
    sg = BNCS["Sync Generator"] - BOOT_R
    report("the tie's loop stays clear of the Sync Generator's BNC boot", loop_x < sg,
           f"(loop to x = {loop_x:.1f}, boot from {sg:.1f})")

    hole, csd, sl_, sy = v("hole_d"), v("csink_d"), v("slot"), v("slot_y")
    for z in v("screw_z"):
        for u, w in ((u, w) for u in (-sl_, 0, sl_) for w in (-sy, sy)):
            head = trimesh.creation.cone(radius=csd / 2 - 0.2, height=csd / 2 - 0.2, sections=96)
            # wide end just inside the outer face, narrowing into the hole (+x)
            head.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
            head.apply_translation([XO + 0.15, v("screw_y") + w, -z + u])
            head = trimesh.boolean.intersection([head, box(XO - 1, XO + (csd - hole) / 2, -99, 99, -999, 999)],
                                                engine="manifold")
            vol = common(m, head)
            report(f"M3 flat head seats, screw at {z} mm {u:+.1f}, {w:+.1f}", vol < 1e-3, f"({vol:.4f} mm3 in the way)")
        vol = common(m, xcyl(v("screw_y"), -z, csd / 2, XO - 60, XO - 0.01))
        report(f"screwdriver reaches the screw at {z} mm", vol < 1e-6)

    # Blackmagic's own tie point and the small hole beside the jack stay open
    vol = common(m, box(9.0, 13.0, H - 3.0, H, -1, 3))
    report("Blackmagic's cable tie point is left free", vol < 1e-6)
    vol = common(m, zcyl((18.8, 8.1), 1.5, -RECESS, 10))
    report("the small hole beside the jack is not covered", vol < 1e-6)

    for f in (STL, HERE / "mini_converter_power_clamp_v0.1-body.stl", HERE / "mini_converter_power_clamp_v0.1-logo.stl"):
        report(f"{f.name} re-imports into OpenSCAD", reimports(f))

    sections_png(m)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, axs = plt.subplots(3, 1, figsize=(9, 13))

    def draw(ax, origin, normal, project):
        s = m.section(plane_origin=origin, plane_normal=normal)
        for e in s.entities:
            p = project(s.vertices[e.points])
            ax.plot(p[:, 0], p[:, 1], "-", color="#0e2942", lw=1.2)

    for ax, z in zip(axs[:2], (10.0, TIE_Z + BLOCK_L / 2)):
        draw(ax, [0, 0, z], [0, 0, 1], lambda p: p[:, :2])
        ax.add_patch(Rectangle((0, 0), 35, H, fill=False, ls=":", color="grey"))
        for name, bx in BNCS.items():
            r = SLEEVE_R if z < SLEEVE_Z else BOOT_R
            ax.add_patch(Circle((bx, BNC_YS[1]), r, fill=False, color="#7a7a7a",
                                ls="-" if "Sync" in name else "--"))
        if z < TIE_Z:
            ax.add_patch(Circle(JACK, PLUG_R, fill=False, color="#c0392b"))
        else:
            ax.add_patch(Circle((GB + CABLE_D / 2, JACK[1]), CABLE_D / 2, fill=False, color="#c0392b"))
        ax.set_xlim(-6, 36)
        ax.set_title(f"z = {z} mm out from the case's front edge (dotted: the case's end; grey: a BNC plug on "
                     f"the Sync Generator, dashed: on the DA; red: biggest plug moulding / the cable)", fontsize=8)
    draw(axs[2], [0, JACK[1], 0], [0, 1, 0], lambda p: p[:, [2, 0]])
    axs[2].add_patch(Rectangle((-LEN, 0), LEN, 35, fill=False, ls=":", color="grey"))
    axs[2].add_patch(Rectangle((-RECESS, JACK[0] - PLUG_R), TIE_Z + RECESS, 2 * PLUG_R, fill=False, color="#c0392b"))
    for z in v("screw_z"):
        axs[2].plot([-z], [-1.2], "v", color="#c0392b")
    axs[2].set_ylim(-6, 36)
    axs[2].set_title("y = the jack's height, from above: the arm and its screws (red marks), the plug's room "
                     "(red) and the tie block", fontsize=8)
    for ax in axs:
        ax.set_aspect("equal")
        ax.grid(True, lw=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
