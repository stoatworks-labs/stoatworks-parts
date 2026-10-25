"""Checks for mini_converter_power_guard_v0.1.stl.

    python -I check.py
    python -I check.py -D bnc_holes=true -D model='"sync"' -D bnc_y=12.6

Reads the numbers the checks need from the .scad, so the two stay in step. With
-D options it renders that variant into a scratch folder first and checks it.

The STL is in its print pose; the checks turn it back into the converter's frame
(origin at the case's corner by the power jack, on its underside: X across the
end, Y up, Z out of the end) and test it against a stand-in converter: the case
and its recessed end panel, the jack and a 12 V plug, every BNC on both models
with a BNC plug in it, the Sync Generator's USB port with a plug in it, the side
screws, and a cable tie. The BNCs' height is the least certain number, so they
are checked at three heights. Draws three sections into check_sections.png.
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
SCAD_PATH = HERE / "mini_converter_power_guard.scad"
SCAD = SCAD_PATH.read_text()
OVERRIDES = dict(a.split("=", 1) for a in sys.argv[2::2]) if sys.argv[1::2] and set(sys.argv[1::2]) == {"-D"} else {}
STLS = {p: HERE / f"mini_converter_power_guard_v0.1{'' if p == 'guard' else '-' + p}.stl" for p in ("guard", "body", "logo")}
if OVERRIDES:
    SCRATCH = Path(tempfile.mkdtemp())
    for p in STLS:
        STLS[p] = SCRATCH / STLS[p].name
        args = sum((["-D", f"{k}={x}"] for k, x in OVERRIDES.items()), [])
        subprocess.run(["openscad", "-o", str(STLS[p]), "-D", f'part="{p}"', *args, str(SCAD_PATH)],
                       check=True, capture_output=True)
STL = STLS["guard"]


def v(name):
    if name in OVERRIDES:
        s = OVERRIDES[name]
    else:
        m = re.search(rf"^{name}\s*=\s*([^;]+);", SCAD, re.M)
        s = m.group(1).split("//")[0].strip()
    return eval(s.replace("[", "(").replace("]", ")").replace("true", "True").replace("false", "False"))


H, W, LEN, RECESS = v("case_h"), v("case_w"), v("case_l"), v("recess")
JACK, PLUG_R = v("jack"), v("plug_r")
GAP, ARM_T = v("side_gap"), v("arm_t")
XO, FO = -GAP - ARM_T, W + GAP + ARM_T
TOWER_H, TIE, TIE_Y, TOP_CH = v("tower_h"), v("tie"), v("tie_y"), v("top_ch")
TZ = TOWER_H - TOP_CH - TIE[1] - 0.8

# From Blackmagic's top views (README). Their height is less certain: the open window
# is checked at three heights, holes at the measured one.
BNCS = {"Sync Generator": (24.15, 38.74, 53.34), "SDI Distribution (and 4K)": (29.29, 44.25, 58.48, 72.99)}
HOLES = v("bnc_holes")
if HOLES:
    BNCS = {k: x for k, x in BNCS.items() if ("Sync" in k) == (v("model") == "sync")}
BNC_YS = (v("bnc_y"),) if HOLES else (10.9, 12.4, 13.9)
USB = (79.4, 8.8)  # the Sync Generator's mini-B, with a plug moulding 12 x 8 mm
# A BNC plug: coupling sleeve 14.3 mm (7.45 with room) out to 32 mm, body and boot
# 10 mm to 55 mm, then 8 mm coax. A 1/2 in nut is 14.7 mm across its corners.
SLEEVE_R, SLEEVE_Z, BOOT_R, BOOT_Z, COAX_R, NUT_R = 7.45, 32, 5.0, 55, 4.0, 7.35


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


def union(ms):
    return trimesh.boolean.union(ms, engine="manifold")


def common(a, b):
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.0 if r.is_empty else float(r.volume)


def bnc_plug(c, grow=0.0):
    return union([zcyl(c, NUT_R + grow, -RECESS, 1.5), zcyl(c, SLEEVE_R + grow, -RECESS, SLEEVE_Z),
                  zcyl(c, BOOT_R + grow, SLEEVE_Z - 1, BOOT_Z), zcyl(c, COAX_R + grow, BOOT_Z - 1, 120)])


def spare(m, make):
    """How far an envelope can grow before it touches the guard."""
    g = 0.0
    for t in np.arange(0.1, 6.0, 0.1):
        if common(m, make(t)) > 1e-6:
            break
        g = t
    return g


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
    case = box(-GAP + 0.01, W + GAP - 0.01, 0, H, -LEN, 0)
    report(f"nothing inside the case, both arms {GAP} mm off its sides", common(m, case) < 1e-6)
    rim = trimesh.boolean.difference([box(0, W, 0, H, -0.05, 0.05), box(0.9, W - 0.9, -1, H - 0.9, -1, 1)],
                                     engine="manifold")
    on_rim = common(m, rim)
    report("it bears on the case's front edge", on_rim > 0, f"({on_rim / 0.05:.0f} mm2 on the edge)")

    plug = zcyl(JACK, PLUG_R - 0.01, -RECESS, TOWER_H + 5)
    vol = common(m, plug)
    report(f"a plug moulding up to {2 * PLUG_R:.0f} mm across goes in from the front, any length",
           vol < 1e-6, f"({vol:.4f} mm3 in the way)")

    for model, xs in BNCS.items():
        for y in BNC_YS:
            vols = [common(m, bnc_plug((x, y))) for x in xs]
            g = min(spare(m, lambda t, x=x: bnc_plug((x, y), t)) for x in xs)
            report(f"{model}: every BNC with a plug in it is clear, BNCs {y} mm up", max(vols) < 1e-6,
                   f"(at least {g:.1f} mm to spare)")
    if "Sync Generator" in BNCS:
        usb = box(USB[0] - 6, USB[0] + 6, USB[1] - 4, USB[1] + 4, -RECESS, 35)
        report("Sync Generator: a USB plug fits its mini-B port", common(m, usb) < 1e-6)
    for p in ((18.8, 8.1), (84.6, 7.8)):
        report(f"the small hole at x {p[0]} is not covered", common(m, zcyl(p, 1.5, -RECESS, 10)) < 1e-6)

    # the tie: both tunnels clear from the outer face into the pocket, and its
    # loop round a boot up to 9 mm stays inside the tower's footprint
    for name, y in (("upper", JACK[1] + TIE_Y), ("lower", JACK[1] - TIE_Y)):
        vol = common(m, box(XO - 1, JACK[0] - PLUG_R + 1.5, y - TIE[0] / 2 + 0.2, y + TIE[0] / 2 - 0.2,
                            TZ + 0.3, TZ + TIE[1] - 0.3))
        report(f"{name} tie tunnel is clear into the pocket (1.4 x 4.8 mm)", vol < 1e-6)
    for d in (3.5, 5.0, 7.0, 9.0):
        cx = JACK[0] - PLUG_R + d / 2
        loop = cx + d / 2 + 1.5
        report(f"a {d} mm boot or cable tied against the pocket: loop to x {loop:.1f}", loop < v("window")[0],
               f"(its centre {cx - JACK[0]:+.1f} mm off the jack's axis)")

    hole, csd = v("hole_d"), v("csink_d")
    sz, sl_, sy, yy = v("screw_z"), v("slot"), v("slot_y"), v("screw_y")
    for side, x_out, sgn in (("near", XO, -1), ("far", FO, 1)):
        for u in (-sl_, 0, sl_):
            for w in (-sy, sy):
                head = trimesh.creation.cone(radius=csd / 2 - 0.2, height=csd / 2 - 0.2, sections=96)
                # wide end just inside the outer face, narrowing into the hole
                head.apply_transform(trimesh.transformations.rotation_matrix(-sgn * np.pi / 2, [0, 1, 0]))
                head.apply_translation([x_out - sgn * 0.15, yy + w, -sz + u])
                lim = sorted([x_out - sgn * (csd - hole) / 2, x_out + sgn * 1])
                head = trimesh.boolean.intersection([head, box(lim[0], lim[1], -99, 99, -999, 999)], engine="manifold")
                vol = common(m, head)
                if vol > 1e-3:
                    report(f"{side} arm: M3 flat head seats at {u:+.1f}, {w:+.1f}", False, f"({vol:.4f} mm3)")
        report(f"{side} arm: an M3 flat head seats anywhere in the slot", True)
        x0, x1 = sorted([x_out + sgn * 0.01, x_out + sgn * 60])
        report(f"{side} arm: a screwdriver reaches the screw", common(m, xcyl(yy, -sz, csd / 2, x0, x1)) < 1e-6)

    for f in STLS.values():
        report(f"{f.name} re-imports into OpenSCAD", reimports(f))

    sections_png(m)
    print("all passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


def sections_png(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))

    def draw(ax, origin, normal, project):
        s = m.section(plane_origin=origin, plane_normal=normal)
        for e in s.entities:
            p = project(s.vertices[e.points])
            ax.plot(p[:, 0], p[:, 1], "-", color="#0e2942", lw=1.2)

    for ax, z in zip(axs[:2], (1.0, TZ + TIE[1] / 2)):
        draw(ax, [0, 0, z], [0, 0, 1], lambda p: p[:, :2])
        ax.add_patch(Rectangle((0, 0), W, H, fill=False, ls=":", color="grey"))
        for model, xs in BNCS.items():
            for x in xs:
                ax.add_patch(Circle((x, BNC_YS[len(BNC_YS) // 2]), SLEEVE_R if z < SLEEVE_Z else BOOT_R, fill=False,
                                    color="#7a7a7a", ls="-" if "Sync" in model else "--"))
        ax.add_patch(Rectangle((USB[0] - 6, USB[1] - 4), 12, 8, fill=False, color="#7a7a7a"))
        ax.add_patch(Circle(JACK, PLUG_R, fill=False, color="#c0392b"))
        ax.set_xlim(-6, W + 6)
        ax.set_title(f"z = {z} mm out from the case's front edge (dotted: the case's end; grey: BNC plugs on the "
                     f"Sync Generator, dashed: on the DA, and the USB plug; red: biggest 12 V plug)", fontsize=8)
    draw(axs[2], [0, JACK[1], 0], [0, 1, 0], lambda p: p[:, [0, 2]])
    axs[2].add_patch(Rectangle((0, -LEN), W, LEN, fill=False, ls=":", color="grey"))
    axs[2].add_patch(Rectangle((JACK[0] - PLUG_R, -RECESS), 2 * PLUG_R, TOWER_H + RECESS, fill=False, color="#c0392b"))
    axs[2].set_ylim(-40, 40)
    axs[2].set_title("y = the jack's height, from above: the plate, both arms, and the tower round the plug (red)",
                     fontsize=8)
    for ax in axs:
        ax.set_aspect("equal")
        ax.grid(True, lw=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "check_sections.png", dpi=90)


if __name__ == "__main__":
    sys.exit(main())
