"""Checks for bidi_microusb_guard_v0.1.stl.

    python -I check.py

Reads the numbers the checks need from the .scad, so the two stay in step. The
STL prints as modelled (plate on the bed, tower up), which is also the converter's
frame: origin at the centre of the SDI end panel, Z out of it. It is tested
against a stand-in end: the BNC nuts and barrels, the micro-USB plug body and its
cable, and both LEDs. Draws three sections into check_sections.png.
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
STL = HERE / "bidi_microusb_guard_v0.1.stl"
SCAD = (HERE / "bidi_microusb_guard.scad").read_text()
END = (58.93, 24.89)


def v(name):
    m = re.search(rf"^{name}\s*=\s*([^;]+);", SCAD, re.M)
    s = m.group(1).split("//")[0].strip()
    return eval(s.replace("[", "(").replace("]", ")"))


USB, PLUG, PH = v("usb"), v("plug"), v("pocket_h")
TOP = PH + v("cap_t")


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


def zcyl(c, r, z0, z1, sections=96):
    c3 = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    c3.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return c3


def common(a, b):
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.0 if r.is_empty else float(r.volume)


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
    report("inside the converter's end", -END[0] / 2 <= lo[0] and hi[0] <= END[0] / 2
           and -END[1] / 2 <= lo[1] and hi[1] <= END[1] / 2,
           f"(x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f})")

    for name in ("led_lock", "led_pwr"):
        p = v(name)
        vol = common(m, zcyl(p, v("led_d") / 2 + 0.3, -1, TOP + 5))
        report(f"nothing over the {name.split('_')[1]} LED (+0.3 mm), all the way up", vol < 1e-6)

    nut_r = v("nut_r")
    for b in v("bnc"):
        vol = common(m, zcyl(b, nut_r + 0.3, v("plate_t") + 0.01, TOP + 5, sections=6 * 16))
        report(f"the BNC nut at x {b[0]:+.1f} turns freely (0.3 mm round its corners)", vol < 1e-6)
        # it seats on the plate at its corners, as on the USB-C guard: the hole is
        # wider than the nut across its flats
        hexa = zcyl(b, nut_r, v("plate_t") - 0.2, v("plate_t") - 0.05, sections=6)
        ring = trimesh.boolean.difference([hexa, zcyl(b, v("bnc_d") / 2 + 0.05, -1, 9)], engine="manifold")
        report(f"the BNC nut at x {b[0]:+.1f} seats on the plate at its corners",
               ring.volume > 0 and abs(common(m, ring) - ring.volume) < 0.02 * ring.volume,
               f"({ring.volume / 0.15:.1f} mm2 of bearing)")

    pw, pt = PLUG
    plug = box(USB[0] - pw / 2, USB[0] + pw / 2, USB[1] - pt / 2, USB[1] + pt / 2, -1, PH - 0.01)
    report(f"a {pw} x {pt} mm plug body, {PH} mm long, goes in", common(m, plug) < 1e-6)
    report("a 4.5 mm cable passes the cap", common(m, zcyl(USB, 2.25, PH - 1, TOP + 10)) < 1e-6)
    for dx in (-(pw / 2 - 0.7), pw / 2 - 0.7):
        zs = []
        for dy in (-2.0, 0.0):
            hits, _, _ = m.ray.intersects_location([[USB[0] + dx, USB[1] + dy, 1.0]], [[0, 0, 1]])
            zs.append(min((h[2] for h in hits), default=None))
        report(f"cap over the plug body's end at x {USB[0] + dx:.2f}",
               all(z is not None and abs(z - PH) < 0.02 for z in zs),
               f"(first solid at z = {', '.join('none' if z is None else f'{z:.2f}' for z in zs)})")
    # the plug can't be levered: wall below it, and walls or hooks above, beside and on either side
    below = box(USB[0] - 3, USB[0] + 3, USB[1] - pt / 2 - 1.5, USB[1] - pt / 2 - 0.35, 3, PH - 1)
    report("solid under the plug body", abs(common(m, below) - below.volume) < 0.02 * below.volume)
    led, wr = v("led_pwr"), v("well_r")
    for side, y0, y1, where in ((-1, USB[1] - pt / 2, USB[1] + pt / 2, "its full height"),
                                (1, led[1] + wr + 0.1, USB[1] + pt / 2, "above the LED slot"),
                                (1, USB[1] - pt / 2, led[1] - wr - 0.1, "below the LED slot")):
        x = USB[0] + side * (pw / 2 + 0.8)
        wall = box(x - 0.4, x + 0.4, y0, y1, 3, PH - 1)
        report(f"wall on the {'-X' if side < 0 else '+X'} side of the plug body, {where}",
               abs(common(m, wall) - wall.volume) < 0.02 * wall.volume, f"(y {y0:.1f}..{y1:.1f})")
    hook = box(USB[0] - pw / 2 + 0.5, USB[0] - v("slot_w") / 2 - 0.2, USB[1] + pt / 2 + 0.4,
               USB[1] + pt / 2 + 1.0, PH - 1.5, PH - 0.5)
    report("hooks across the top of the open side", abs(common(m, hook) - hook.volume) < 0.02 * hook.volume)

    for f in (STL, HERE / "bidi_microusb_guard_v0.1-body.stl", HERE / "bidi_microusb_guard_v0.1-logo.stl"):
        report(f"{f.name} re-imports into OpenSCAD", reimports(f))

    sections_png(m)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, RegularPolygon
    fig, axs = plt.subplots(3, 1, figsize=(9, 12))
    pw, pt = PLUG
    for ax, z in zip(axs, (1.0, 8.0, PH + 1.0)):
        s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        for e in s.entities:
            p = s.vertices[e.points]
            ax.plot(p[:, 0], p[:, 1], "-", color="#0e2942", lw=1.2)
        ax.add_patch(Rectangle((-END[0] / 2, -END[1] / 2), END[0], END[1], fill=False, ls=":", color="grey"))
        for b in v("bnc"):
            ax.add_patch(RegularPolygon(b, 6, radius=v("nut_r"), fill=False, color="#7a7a7a"))
        ax.add_patch(Rectangle((USB[0] - pw / 2, USB[1] - pt / 2), pw, pt, fill=False, color="#c0392b"))
        for name in ("led_lock", "led_pwr"):
            ax.add_patch(Circle(v(name), v("led_d") / 2, color="#e6a700"))
        ax.set_aspect("equal")
        ax.grid(True, lw=0.3)
        ax.set_title(f"z = {z} mm off the panel (dotted: the end; grey: BNC nuts; red: plug body; amber: LEDs)",
                     fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
