"""Checks for decimator_usb_guard_v0.1.stl.

    python -I check.py [original.stl]

Reads its numbers from the .scad. With joren's original STL it also compares the
interface this design took from it (screw holes, the plug's space and what holds
the plug in) and draws both outlines into check_sections.png.
"""
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
STL = HERE / "decimator_usb_guard_v0.1.stl"
ORIGIN = (29.45, 0.25)   # centre of joren's plate, in its own coordinates


def scad_value(name):
    src = (HERE / "decimator_usb_guard.scad").read_text()
    m = re.search(rf"^{name}\s*=\s*([^;]+);", src, re.M)
    v = m.group(1).split("//")[0].strip()
    return eval(v.replace("[", "(").replace("]", ")"))


def cylinder(c, r, z0, z1):
    cyl = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=96)
    cyl.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return cyl


def common(a, b):
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.0 if r.is_empty else float(r.volume)


def original(path):
    o = trimesh.load(path, force="mesh")
    o.apply_translation([-ORIGIN[0], -ORIGIN[1], -o.bounds[0, 2]])
    return o


def first_above(mesh, xy, z0):
    hits, _, _ = mesh.ray.intersects_location([[xy[0], xy[1], z0]], [[0, 0, 1]])
    return min((h[2] for h in hits if h[2] > z0 + 1e-6), default=None)


def main():
    m = trimesh.load(STL, force="mesh")
    ok = True

    def report(name, good, detail=""):
        nonlocal ok
        ok &= bool(good)
        print(f"{'ok  ' if good else 'FAIL'} {name} {detail}")

    report("closed, one body", m.is_watertight and m.is_winding_consistent
           and len(m.split(only_watertight=False)) == 1,
           f"({len(m.faces)} faces, {m.volume:.0f} mm3, ~{m.volume * 1.14e-3:.1f} g PA6-GF solid)")
    lo, hi = m.bounds
    plate = scad_value("plate")
    report("inside the MD-LX's end", hi[0] - lo[0] <= plate[0] + 1e-6 and hi[1] - lo[1] <= plate[1] + 1e-6,
           f"(x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f}, z {lo[2]:.2f}..{hi[2]:.2f})")

    fr = scad_value("flange_d") / 2
    for c in scad_value("bnc"):
        v = common(m, cylinder(c, fr + 0.9, -1, 12))
        report(f"BNC at {c}: 0.9 mm clear of its flange", v < 1e-6, f"({v:.4f} mm3 in the way)")
    hr = scad_value("head_d") / 2
    pt = scad_value("plate_t")
    for c in scad_value("screws"):
        v = common(m, cylinder(c, hr - 0.05, pt + 0.01, hi[2] + 5))
        report(f"screw at {c}: head and driver clear above the plate", v < 1e-6, f"({v:.4f} mm3 in the way)")

    if len(sys.argv) > 1:
        o = original(Path(sys.argv[1]))
        # the screw holes and countersinks, by section
        for z in (1.0, 2.4):
            for c in scad_value("screws"):
                widths = []
                for mesh in (m, o):
                    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
                    p, _ = s.to_2D(to_2D=np.eye(4))
                    from shapely.geometry import Point, Polygon
                    w = [Polygon(h).bounds for poly in p.polygons_full for h in poly.interiors
                         if Polygon(h).contains(Point(c))]
                    widths.append(round(w[0][2] - w[0][0], 2) if w else None)
                print(f"     screw hole at {c}, z={z}: new {widths[0]} mm, original {widths[1]} mm")
        # what holds the plug: first solid above points in the plug space
        px, py = scad_value("pocket_x"), scad_value("pocket_y")
        probes = {
            "plug body's far end (back wall leans over it)": (px[0] + 0.5, sum(py) / 2),
            "plug body's near end, top corner (lip)": (px[1] - 0.5, py[1] - 0.4),
            "plug body's near end, bottom corner (lip)": (px[1] - 0.5, py[0] + 0.4),
            "the cable's way out (should be open)": (sum(px) / 2, sum(py) / 2),
        }
        for what, xy in probes.items():
            a, b = first_above(m, xy, 3.0), first_above(o, xy, 3.0)
            fmt = lambda v: "open" if v is None else f"{v:.2f}"
            print(f"     {what} at ({xy[0]:.2f}, {xy[1]:.2f}): new {fmt(a)}, original {fmt(b)}")
        # Below the plug body's top, this part must be empty wherever the original
        # is (the plug fits at least as well); above it, the lips and lean hold it.
        top = 22.5   # below the original's top chamfer
        box = trimesh.creation.box(extents=[px[1] - px[0], py[1] - py[0], top])
        box.apply_translation([sum(px) / 2, sum(py) / 2, top / 2])
        # only the original's empty space joined to the pocket: behind its back
        # wall, whose outside also leans in, is open air, not room for the plug
        inside = [sum(px) / 2, sum(py) / 2, 5.0]
        orig_space = [s for s in trimesh.boolean.difference([box, o], engine="manifold")
                      .split(only_watertight=False) if s.contains([inside])[0]][0]
        v = common(m, orig_space)
        report(f"room for the plug and cable (to z {top}) at least the original's", v < 1e-3,
               f"({v:.4f} mm3 of this part where the original is empty)")
        sections_png(m, o)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m, o):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    zs = (1.0, 10.0, 20.0)
    fig, axs = plt.subplots(len(zs), 1, figsize=(11, 4.6 * len(zs)))
    for ax, z in zip(axs, zs):
        for mesh, col, lab in ((o, "#c0392b", "original"), (m, "#0e2942", "this design")):
            s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
            if s is None:
                continue
            for e in s.entities:
                p = s.vertices[e.points]
                ax.plot(p[:, 0], p[:, 1], "-", color=col, lw=1.2, label=lab)
                lab = None
        for c in scad_value("bnc"):
            ax.add_patch(plt.Circle(c, scad_value("flange_d") / 2, fill=False, ls=":", color="#b8860b"))
        ax.set_aspect("equal"); ax.grid(True, lw=0.3)
        ax.set_title(f"z = {z} mm   (red: original part, navy: this design, dotted: BNC flanges)",
                     fontsize=9)
        ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
