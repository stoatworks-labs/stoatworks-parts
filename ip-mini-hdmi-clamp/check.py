"""Checks for ip_mini_hdmi_clamp_v0.1.stl.

    python -I check.py

Reads the numbers the checks need from the .scad, so the two stay in step. The
STL is in its print pose; the checks turn it back into the converter's frame
(origin at the centre of the HDMI end, Z out of it, Y up to the vents) and test
it against a stand-in converter: the case, the vents, the screws, the HDMI plug
and its cable, and a cable tie. Draws three sections into check_sections.png.
"""
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
STL = HERE / "ip_mini_hdmi_clamp_v0.1.stl"
SCAD = (HERE / "ip_mini_hdmi_clamp.scad").read_text()


def v(name):
    m = re.search(rf"^{name}\s*=\s*([^;]+);", SCAD, re.M)
    s = m.group(1).split("//")[0].strip()
    return eval(s.replace("[", "(").replace("]", ")").replace("true", "True"))


END = v("end")
YB = -END[1] / 2
HDMI = v("hdmi")
MOULD = v("moulding")
WI = MOULD[0] / 2 + v("gap")
WO = WI + v("wall_t")
TIE_Z, BAR_L, BAR_BOT = v("tie_z"), v("bar_l"), v("bar_bot")
L = TIE_Z + BAR_L
CSINK = {n: (h, c) for n, h, c in v("csinks")}[v("screw")]


def to_converter(m):
    """Print pose -> converter frame: x = x, y = z + YB, z = -y."""
    m = m.copy()
    p = m.vertices
    m.vertices = np.c_[p[:, 0], p[:, 2] + YB, -p[:, 1]]
    return m


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


def zcyl(c, r, z0, z1):
    c3 = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=96)
    c3.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return c3


def rounded_box(c, w, h, r, z0, z1):
    from shapely.geometry import box as sbox
    poly = sbox(c[0] - w / 2 + r, c[1] - h / 2 + r, c[0] + w / 2 - r, c[1] + h / 2 - r).buffer(r, 32)
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


def common(a, b):
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.0 if r.is_empty else float(r.volume)


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

    lo, hi = m.bounds
    print(f"     overall x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f}, z {lo[2]:.2f}..{hi[2]:.2f}")
    report("nothing below the case's underside", lo[1] >= YB - 1e-6)
    report("nothing over the vents (0.5 mm clear)", hi[1] <= v("vents_y") - 0.5,
           f"(top {hi[1]:.2f}, vents from {v('vents_y'):.2f})")
    case = box(-END[0] / 2, END[0] / 2, YB, END[1] / 2, -125, 0)
    report("nothing inside the case", common(m, case) < 1e-6)
    inner = END[0] / 2 - v("rim")
    near = box(-50, 50, -50, 50, 0, 1.0)
    sl = trimesh.boolean.intersection([m, near], engine="manifold")
    report("the plate sits inside the case's rim", sl.bounds[1][0] < inner and sl.bounds[0][0] > -inner,
           f"(plate x {sl.bounds[0][0]:.2f}..{sl.bounds[1][0]:.2f}, rim inside +/-{inner:.2f})")
    s0 = m.section(plane_origin=[0, 0, 0.05], plane_normal=[0, 0, 1])
    print(f"     on the panel: {s0.to_2D(to_2D=np.eye(4))[0].area:.0f} mm2")

    mould = rounded_box(HDMI, MOULD[0], MOULD[1], 2.0, -1, TIE_Z - 0.5)
    vol = common(m, mould)
    report(f"a {MOULD[0]} x {MOULD[1]} mm HDMI moulding up to {TIE_Z - 0.5:.1f} mm long fits",
           vol < 1e-6, f"({vol:.4f} mm3 in the way)")

    # the cable lies in the trough: centred on the port for the design size,
    # within a millimetre or so for others
    tb = HDMI[1] - v("cable_d") / 2
    for d in (5.0, 6.0, v("cable_d"), 8.0, 9.0, 10.0):
        c = (HDMI[0], tb + d / 2 + 0.02)
        vol = common(m, zcyl(c, d / 2, TIE_Z - 2, L + 20))
        report(f"a {d:.0f} mm cable lies in the trough", vol < 1e-6,
               f"(its centre {c[1] - HDMI[1]:+.2f} mm off the port's; {vol:.4f} mm3 in the way)")

    # the tie's path: down each slot, under the bar's middle
    tr, sw, sz = v("trough_r"), *v("slot")
    zc = TIE_Z + BAR_L / 2
    for side in (-1, 1):
        x = HDMI[0] + side * (tr + sw / 2)
        vol = common(m, box(x - 0.7, x + 0.7, BAR_BOT - 1, 2, zc - 2.4, zc + 2.4))
        report(f"tie slot {'left' if side < 0 else 'right'} is clear (1.4 x 4.8 mm)", vol < 1e-6)
    vol = common(m, box(HDMI[0] - tr - sw, HDMI[0] + tr + sw, YB + 0.2, BAR_BOT - 0.2, zc - 2.4, zc + 2.4))
    report("room for the tie under the bar", vol < 1e-6, f"({BAR_BOT - YB:.1f} mm)")

    hole, csd = CSINK
    for p in v("screws"):
        head = trimesh.creation.cone(radius=csd / 2 - 0.2, height=csd / 2 - 0.2, sections=96)  # 0.05 mm clear of the countersink
        head.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        head.apply_translation([p[0], p[1], v("plate_t") - 0.15])
        head = trimesh.boolean.difference([head, box(-99, 99, -99, 99, -9, v("plate_t") - (csd - hole) / 2)],
                                          engine="manifold")
        vol = common(m, head)
        report(f"{v('screw')} flat head seats at {p[0]:+.1f}", vol < 1e-3, f"({vol:.4f} mm3 in the way)")
        vol = common(m, zcyl(p, csd / 2, v("plate_t") + 0.01, 80))
        report(f"screwdriver reaches the screw at {p[0]:+.1f}", vol < 1e-6)

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

    tb = HDMI[1] - v("cable_d") / 2
    for ax, z in zip(axs[:2], (1.0, TIE_Z + BAR_L / 2)):
        draw(ax, [0, 0, z], [0, 0, 1], lambda p: p[:, :2])
        ax.add_patch(Rectangle((-END[0] / 2, YB), END[0], END[1], fill=False, ls=":", color="grey"))
        ax.add_patch(Rectangle((-END[0] / 2, v("vents_y")), END[0], 9.0, color="#cccccc", alpha=0.5))
        if z < 2:
            ax.add_patch(Rectangle((HDMI[0] - MOULD[0] / 2, HDMI[1] - MOULD[1] / 2), MOULD[0], MOULD[1],
                                   fill=False, color="#7a7a7a"))
            for p in v("screws"):
                ax.add_patch(Circle(p, CSINK[1] / 2, fill=False, color="#c0392b"))
        else:
            ax.add_patch(Circle((HDMI[0], tb + v("cable_d") / 2), v("cable_d") / 2, fill=False, color="#c0392b"))
        ax.set_title(f"z = {z} mm off the end panel (dotted: the case; shaded: vents; "
                     f"grey: biggest HDMI moulding; red: screw heads / cable)", fontsize=8)
    draw(axs[2], [HDMI[0], 0, 0], [1, 0, 0], lambda p: p[:, [2, 1]])
    axs[2].add_patch(Rectangle((-20, YB), 20, END[1], fill=False, ls=":", color="grey"))
    axs[2].add_patch(Rectangle((0, HDMI[1] - MOULD[1] / 2), TIE_Z - 0.5, MOULD[1], fill=False, color="#7a7a7a"))
    axs[2].set_title("x = the HDMI's centre line: the channel, the moulding (grey) and the tie bar", fontsize=8)
    for ax in axs:
        ax.set_aspect("equal")
        ax.grid(True, lw=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
