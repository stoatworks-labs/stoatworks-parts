"""Checks for decimator_microusb_guard_v0.1.stl.

    python -I check.py

Reads the numbers the checks need from the .scad, so the two stay in step. The
STL prints as modelled (plate on the bed, tower up), which is also the MD-LX's
frame: origin at the centre of the SDI end panel, Z out of it. It is tested
against a stand-in end: the BNC flanges and barrels, the end screws, the
micro-USB plug body and its cable, and the small hole between the BNCs. Draws
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
STL = HERE / "decimator_microusb_guard_v0.1.stl"
SCAD = (HERE / "decimator_microusb_guard.scad").read_text()


def v(name):
    m = re.search(rf"^{name}\s*=\s*([^;]+);", SCAD, re.M)
    s = m.group(1).split("//")[0].strip()
    return eval(s.replace("[", "(").replace("]", ")"))


USB, PLUG, BODY_H = v("usb"), v("plug"), v("body_h")
PLATE, PLATE_T, TOWER_H = v("plate"), v("plate_t"), v("tower_h")


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


def zcyl(c, r, z0, z1):
    c3 = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=96)
    c3.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return c3


def common(a, b):
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.0 if r.is_empty else float(r.volume)


def full(m, b):
    return abs(common(m, b) - b.volume) < 0.02 * b.volume


def reimports(path):
    with tempfile.TemporaryDirectory() as d:
        scad = Path(d) / "r.scad"
        scad.write_text(f'import("{path}", convexity = 10);\n')
        r = subprocess.run(["openscad", "-o", str(Path(d) / "r.off"), str(scad)], capture_output=True, text=True)
        log = r.stdout + r.stderr
        return r.returncode == 0 and "not closed" not in log and "ERROR" not in log


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
    s = m.section(plane_origin=[0, 0, 0.1], plane_normal=[0, 0, 1])
    area = s.to_2D(to_2D=np.eye(4))[0].area
    report("as printed: plate on the bed", abs(lo[2]) < 1e-6,
           f"({hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm, {area:.0f} mm2 on the bed)")
    pairs = len(cKDTree(m.vertices).query_pairs(0.01))
    report("no near-duplicate vertices (slivers)", pairs == 0, f"({pairs} pairs within 0.01 mm)")
    report(f"inside the {PLATE[0]} x {PLATE[1]} mm end", hi[0] - lo[0] <= PLATE[0] + 1e-6
           and hi[1] - lo[1] <= PLATE[1] + 1e-6, f"(x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f})")

    for b in v("bnc"):
        vol = common(m, zcyl(b, v("flange_d") / 2 + 0.9, -1, TOWER_H + 5))
        report(f"BNC at x {b[0]:+.2f}: 0.9 mm clear of its flange, all the way up", vol < 1e-6)
    for sc in v("screws"):
        head = trimesh.creation.cone(radius=v("csink_d") / 2 - 0.25, height=v("csink_d") / 2 - 0.25, sections=96)
        head.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        head.apply_translation([sc[0], sc[1], PLATE_T - 0.05])
        head = trimesh.boolean.intersection([head, box(-99, 99, -99, 99, PLATE_T - (v("csink_d") - v("screw_d")) / 2, 9)],
                                            engine="manifold")
        report(f"screw at x {sc[0]:+.2f}: a flat head seats in its countersink", common(m, head) < 1e-3)
        report(f"screw at x {sc[0]:+.2f}: head and driver clear above the plate",
               common(m, zcyl(sc, v("head_d") / 2 - 0.05, PLATE_T + 0.01, 60)) < 1e-6)
    report("the small hole between the BNCs is left open",
           common(m, zcyl(v("hole_led"), 1.2, -1, TOWER_H + 5)) < 1e-6)

    pw, pt = PLUG
    plug = box(USB[0] - pw / 2, USB[0] + pw / 2, USB[1] - pt / 2, USB[1] + pt / 2, -1, BODY_H - 0.01)
    report(f"a {pw} x {pt} mm plug body, {BODY_H} mm long, goes in", common(m, plug) < 1e-6)
    report("a 3.8 mm cable passes between the lips", common(m, zcyl(USB, 1.9, BODY_H, TOWER_H + 10)) < 1e-6)
    # what keeps it in: how far the plug body could back out before one of its
    # corners meets a lip (its near, +X end) or the leaning back wall (its far end)
    def first_hit(x, y):
        hits, _, _ = m.ray.intersects_location([[x, y, 1.0]], [[0, 0, 1]])
        return min((h[2] for h in hits), default=None)
    for name, dx, dys in (("lips over the body's near end", pw / 2 - 0.5, (-(pt / 2 - 0.05), pt / 2 - 0.05)),
                          ("back wall over the body's far end", -(pw / 2 - 0.05), (-2.0, 0.0, 2.0))):
        zs = [first_hit(USB[0] + dx, USB[1] + dy) for dy in dys]
        out = max(z - BODY_H for z in zs) if all(z is not None for z in zs) else None
        report(name, out is not None and out <= 0.5,
               "(the plug could back out " + ("for ever" if out is None else f"{out:.2f} mm") + ")")
    below = box(USB[0] - 3, USB[0] + 3, USB[1] - pt / 2 - 1.5, USB[1] - pt / 2 - 0.35, 3, BODY_H - 1)
    above = box(USB[0] - 3, USB[0] + 3, USB[1] + pt / 2 + 0.35, USB[1] + pt / 2 + 1.5, 3, BODY_H - 1)
    report("walls under and over the plug body, so it can't be levered", full(m, below) and full(m, above))

    for f in (STL, HERE / "decimator_microusb_guard_v0.1-body.stl", HERE / "decimator_microusb_guard_v0.1-logo.stl"):
        report(f"{f.name} re-imports into OpenSCAD", reimports(f))

    sections_png(m)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, axs = plt.subplots(3, 1, figsize=(9, 12))
    pw, pt = PLUG
    for ax, z in zip(axs, (1.0, 8.0, BODY_H + 2.5)):
        s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        for e in s.entities:
            p = s.vertices[e.points]
            ax.plot(p[:, 0], p[:, 1], "-", color="#0e2942", lw=1.2)
        ax.add_patch(Rectangle((-PLATE[0] / 2, -PLATE[1] / 2), PLATE[0], PLATE[1], fill=False, ls=":", color="grey"))
        for b in v("bnc"):
            ax.add_patch(Circle(b, v("flange_d") / 2, fill=False, color="#7a7a7a"))
        for sc in v("screws"):
            ax.add_patch(Circle(sc, v("head_d") / 2, fill=False, color="#7a7a7a", ls="--"))
        ax.add_patch(Rectangle((USB[0] - pw / 2, USB[1] - pt / 2), pw, pt, fill=False, color="#c0392b"))
        ax.add_patch(Circle(v("hole_led"), 0.9, color="#e6a700"))
        ax.set_aspect("equal")
        ax.grid(True, lw=0.3)
        ax.set_title(f"z = {z} mm off the panel (dotted: the plate; grey: BNC flanges, screw heads dashed; "
                     f"red: plug body; amber: the small hole)", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
