"""Checks for micro_converter_usb_guard_v0.1.stl.

    python -I check.py

Reads the numbers the checks need from the .scad, so the two stay in step. The
STL is in its print pose; the checks turn it back into the converter's frame
(origin at the centre of the HDMI end, Z out of it, Y up to the label) and test
it against a stand-in converter: the case, the plugs, the LED and the screws.
Draws three sections into check_sections.png.
"""
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
STL = HERE / "micro_converter_usb_guard_v0.1.stl"
SCAD = (HERE / "micro_converter_usb_guard.scad").read_text()


def v(name):
    m = re.search(rf"^{name}\s*=\s*([^;]+);", SCAD, re.M)
    s = m.group(1).split("//")[0].strip()
    return eval(s.replace("[", "(").replace("]", ")"))


CASE = (v("case_w"), v("case_h"))
YB, YT = -CASE[1] / 2, CASE[1] / 2
XA = CASE[0] / 2 + v("side_gap")
XO = XA + v("arm_t")
TOP = v("pocket_h") + v("cap_t")


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


def screw(side, z):
    """An M3 flat head (6.0 mm, 90 degrees) seated flush in an arm, and its shank."""
    head = trimesh.creation.cone(radius=3.0, height=3.0, sections=96)  # apex 3 mm in
    head.apply_translation([0, 0, -3.0])
    head = trimesh.boolean.difference([head, box(-4, 4, -4, 4, -4, -1.5)], engine="manifold")
    shank = zcyl((0, 0), 1.5, -8, -1.4)
    s = trimesh.boolean.union([head, shank], engine="manifold")
    # local +Z points out of the arm
    rot = trimesh.transformations.rotation_matrix(side * np.pi / 2, [0, 1, 0])
    s.apply_transform(rot)
    s.apply_translation([side * XO, v("screw_y"), z])
    return s


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
    report("flush with the case's top and underside", lo[1] >= YB - 1e-6 and hi[1] <= YT + 1e-6,
           f"(y {lo[1]:.2f}..{hi[1]:.2f}, case {YB:.2f}..{YT:.2f})")
    print(f"     overall x {lo[0]:.2f}..{hi[0]:.2f}, z {lo[2]:.2f}..{hi[2]:.2f} "
          f"(arms {XO - XA:.1f} mm thick, {XA - CASE[0] / 2:.2f} mm off the case each side)")

    case = box(-CASE[0] / 2, CASE[0] / 2, YB, YT, -62, 0)
    report("nothing inside the case", common(m, case) < 1e-6)
    wide = box(-XA + 0.05, XA - 0.05, YB, YT, -62, -0.05)
    report("arms clear the case's sides by the side gap", common(m, wide) < 1e-6)

    led, led_d = v("led"), v("led_d")
    vol = common(m, zcyl(led, led_d / 2 + 0.3, -1, TOP + 5))
    report("nothing over the LED (+0.3 mm), all the way up", vol < 1e-6, f"({vol:.4f} mm3 in the way)")

    # how far off the cable's line the LED can be seen: rays from its centre,
    # 0.8 mm into the case (the end panel looks recessed that far)
    def clear(direction):
        o = np.array([led[0], led[1], -0.8])
        d = np.array(direction, float)
        d /= np.linalg.norm(d)
        hits, _, _ = m.ray.intersects_location([o], [d])
        return len(hits) == 0

    def widest(axis, sign):
        best = 0
        for deg in range(0, 90):
            t = np.radians(deg)
            d = [0.0, 0.0, np.cos(t)]
            d[axis] = sign * np.sin(t)
            if not clear(d):
                break
            best = deg
        return best

    seen = {name: widest(a, s) for name, a, s in
            (("USB-C side", 0, 1), ("HDMI side", 0, -1), ("up", 1, 1), ("down", 1, -1))}
    report("LED visible along the cable", seen["USB-C side"] >= 0 and clear([0, 0, 1]),
           "(off the cable line, clear to: " + ", ".join(f"{k} {d} deg" for k, d in seen.items()) + ")")

    usbc = v("usbc")
    plug = box(usbc[0] - 6.75, usbc[0] + 6.75, usbc[1] - 3.75, usbc[1] + 3.75, -1, v("pocket_h") - 0.01)
    report("a 13.5 x 7.5 mm plug body, 18.2 mm long, goes in", common(m, plug) < 1e-6)
    cable = zcyl(usbc, 2.25, v("pocket_h") - 1, TOP + 10)
    report("a 4.5 mm cable passes the cap", common(m, cable) < 1e-6)
    # the cap must stop the plug body backing out: test 0.7 mm in from each end
    # of a 12.4 mm body, at its middle and 2.5 mm either side
    for dx in (-5.5, 5.5):
        zs = []
        for dy in (-2.5, 0, 2.5):
            hits, _, _ = m.ray.intersects_location([[usbc[0] + dx, usbc[1] + dy, 1.0]], [[0, 0, 1]])
            zs.append(min((h[2] for h in hits), default=None))
        report(f"cap over the plug body's end at x {usbc[0] + dx:.2f}",
               all(z is not None and abs(z - v("pocket_h")) < 0.02 for z in zs),
               f"(first solid at z = {', '.join('none' if z is None else f'{z:.2f}' for z in zs)})")

    # the widest moulding that, centred on the port, still clears the case's own side
    hdmi = v("hdmi")
    mw = 2 * (CASE[0] / 2 + hdmi[0]) - 0.2
    moulding = rounded_box(hdmi, mw, 14.2, 2.0, -1, 45)
    vol = common(m, moulding)
    report(f"a {mw:.1f} x 14.2 mm HDMI plug moulding reaches the port", vol < 1e-6,
           f"({vol:.4f} mm3 in the way)")

    sz, slot = v("screw_z"), v("slot")
    for side in (-1, 1):
        for dz in (-slot, 0, slot):
            vol = common(m, screw(side, sz + dz))
            report(f"M3 flat head seats flush, {'left' if side < 0 else 'right'} arm, z {sz + dz:.1f}",
                   vol < 1e-3, f"({vol:.4f} mm3 in the way)")
        # the arm round the screw: something to clamp
        ring = trimesh.boolean.difference(
            [box(XA - 0.01, XO, -4.5, 4.5, sz - slot - 4.5, sz + slot + 4.5) if side > 0
             else box(-XO, -XA + 0.01, -4.5, 4.5, sz - slot - 4.5, sz + slot + 4.5),
             box(-50, 50, -3.3, 3.3, sz - slot - 3.3, sz + slot + 3.3)], engine="manifold")
        report(f"{'left' if side < 0 else 'right'} arm is solid round its slot",
               abs(common(m, ring) - ring.volume) < 1e-2 * ring.volume)

    sections_png(m)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, axs = plt.subplots(3, 1, figsize=(9, 13))
    usbc, hdmi, led = v("usbc"), v("hdmi"), v("led")

    def draw(ax, origin, normal, project):
        s = m.section(plane_origin=origin, plane_normal=normal)
        for e in s.entities:
            p = project(s.vertices[e.points])
            ax.plot(p[:, 0], p[:, 1], "-", color="#0e2942", lw=1.2)

    for ax, z in zip(axs[:2], (1.0, 10.0)):
        draw(ax, [0, 0, z], [0, 0, 1], lambda p: p[:, :2])
        ax.add_patch(Rectangle((-CASE[0] / 2, YB), CASE[0], CASE[1], fill=False, ls=":", color="grey"))
        ax.add_patch(Rectangle((usbc[0] - 6.75, usbc[1] - 3.75), 13.5, 7.5, fill=False, color="#c0392b"))
        mw = 2 * (CASE[0] / 2 + hdmi[0]) - 0.2
        ax.add_patch(Rectangle((hdmi[0] - mw / 2, hdmi[1] - 7.1), mw, 14.2, fill=False, color="#7a7a7a"))
        ax.add_patch(Circle(led, v("led_d") / 2, color="#e6a700"))
        ax.set_title(f"z = {z} mm off the case's front edge (dotted: the case; red: plug body; "
                     f"grey: HDMI moulding; amber: LED)", fontsize=8)
    draw(axs[2], [0, 0, 0], [0, 1, 0], lambda p: p[:, [2, 0]])
    axs[2].add_patch(Rectangle((-62, -CASE[0] / 2), 62, CASE[0], fill=False, ls=":", color="grey"))
    sz = v("screw_z")
    for s in (-1, 1):
        axs[2].plot([sz, sz], [s * (CASE[0] / 2 - 3), s * (XO + 0.5)], "-", color="#c0392b", lw=2)
    axs[2].set_title("y = 0: through the screws (red), the case dotted", fontsize=8)
    for ax in axs:
        ax.set_aspect("equal")
        ax.grid(True, lw=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
