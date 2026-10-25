"""Checks for bidi_usb_guard_v0.1.stl.

    python -I check.py [original.3mf]

Reads the numbers the checks need from the .scad, so the two stay in step.
With dj12bas's original 3MF it also compares the converter interface (BNC holes,
the plug's opening and pocket, the pocket's height), which this design took
from that part, and draws both outlines into check_sections.png.
"""
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
STL = HERE / "bidi_usb_guard_v0.1.stl"


def scad_value(name):
    src = (HERE / "bidi_usb_guard.scad").read_text()
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
    """dj12bas's mesh, turned into this design's frame (panel centre, Z on the panel)."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("3D/Objects/object_1.model"))
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    mesh = root.find(".//m:mesh", ns)
    v = np.array([[float(e.get(k)) for k in "xyz"] for e in mesh.find("m:vertices", ns)])
    f = np.array([[int(e.get(k)) for k in ("v1", "v2", "v3")] for e in mesh.find("m:triangles", ns)])
    v = np.c_[-v[:, 1], v[:, 0], v[:, 2] - v[:, 2].min()]  # 90 degrees about Z, onto Z = 0
    return trimesh.Trimesh(v, f)


def holes_at(m, z):
    from shapely.geometry import Polygon
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4))
    out = []
    for poly in p.polygons_full:
        for h in poly.interiors:
            hp = Polygon(h)
            out.append((round(hp.centroid.x, 2), round(hp.centroid.y, 2),
                        round(hp.bounds[2] - hp.bounds[0], 2), round(hp.bounds[3] - hp.bounds[1], 2)))
    return sorted(out)


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
    report("inside the converter's end", hi[0] - lo[0] <= plate[0] + 1e-6 and hi[1] - lo[1] <= plate[1] + 1e-6,
           f"(x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f}, z {lo[2]:.2f}..{hi[2]:.2f})")

    led_d = scad_value("led_d")
    for name in ("led_lock", "led_pwr"):
        c = scad_value(name)
        v = common(m, cylinder(c, led_d / 2 + 0.3, -1, hi[2] + 5))
        report(f"nothing over {name} (+0.3 mm)", v < 1e-6, f"({v:.4f} mm3 in the way)")

    nut_r, plate_t = scad_value("nut_r"), scad_value("plate_t")
    for c in scad_value("bnc"):
        v = common(m, cylinder(c, nut_r + 0.3, plate_t + 0.01, plate_t + 8))
        report(f"nut at {c} turns freely (corners +0.3 mm)", v < 1e-6, f"({v:.4f} mm3 in the way)")
        ring = cylinder(c, nut_r, 0, plate_t)
        hole = cylinder(c, scad_value("bnc_d") / 2, -1, plate_t + 1)
        seat = trimesh.boolean.difference([ring, hole], engine="manifold")
        report(f"nut at {c} seats on the full plate thickness",
               abs(common(m, seat) - seat.volume) < 1e-3 * seat.volume)

    if len(sys.argv) > 1:
        o = original(Path(sys.argv[1]))
        for z, what in ((1.0, "through the plate"), (8.0, "pocket, mid-height")):
            print(f"     {what} (z={z}) holes, new:  {holes_at(m, z)}")
            print(f"     {what} (z={z}) holes, orig: {holes_at(o, z)}")
        # first solid above: the cap's underside beside the cable slot, and the
        # undersides of the hooks across the open side
        x0 = scad_value("pocket_x")[0]
        for what, c in (("pocket roof", (x0 + 0.8, -3.0)), ("hook underside", (x0 + 0.5, 1.2))):
            zs = {}
            for mesh, name in ((m, "new"), (o, "orig")):
                hits, _, _ = mesh.ray.intersects_location([[c[0], c[1], 0.5]], [[0, 0, 1]])
                zs[name] = min((h[2] for h in hits if h[2] > 2.5), default=None)
            print(f"     {what} over {c}: new z = {zs['new']:.2f}, original z = {zs['orig']:.2f}")
        sections_png(m, o)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m, o):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    zs = (1.0, 8.0, 17.7)
    fig, axs = plt.subplots(len(zs), 1, figsize=(10, 4.2 * len(zs)))
    for ax, z in zip(axs, zs):
        for mesh, col, lab in ((o, "#c0392b", "original"), (m, "#0e2942", "this design")):
            s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
            if s is None:
                continue
            for e in s.entities:
                p = s.vertices[e.points]
                ax.plot(p[:, 0], p[:, 1], "-", color=col, lw=1.2, label=lab)
                lab = None
        for name, col in (("led_lock", "#e6a700"), ("led_pwr", "#e6a700")):
            c = scad_value(name)
            ax.add_patch(plt.Circle(c, scad_value("led_d") / 2, color=col))
        for c in scad_value("bnc"):
            ax.add_patch(plt.Circle(c, scad_value("nut_r"), fill=False, ls=":", color="grey"))
        ax.set_aspect("equal"); ax.grid(True, lw=0.3)
        ax.set_title(f"z = {z} mm   (red: original part, navy: this design, "
                     f"amber: LEDs, dotted: nut corners)", fontsize=9)
        ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
