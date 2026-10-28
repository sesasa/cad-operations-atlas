"""Two-part ABS enclosure held together by four cantilever snap hooks, built with CadQuery.

80 x 50 x 24 mm closed. The lid's hooks pass down inside the base walls and their
heads catch in windows cut through the long walls. Units are millimetres; the
base sits on z = 0 and the lid closes at z = 22.

    pip install cadquery
    python models/snap_enclosure.py       # writes models/snap_enclosure.step

The atlas page (index.html) draws and animates the same part from the same
numbers (the SNAP_ block there), so keep the two in step when changing one.
"""
import math
import pathlib

import cadquery as cq

OUT = pathlib.Path(__file__).resolve().parent

# Base
L, W, H = 80.0, 50.0, 22.0
R_CORNER, WALL, R_BOTTOM = 4.0, 2.0, 1.5

# Lid
LID_T = 2.0
RIB_T, RIB_H, CLEAR = 1.2, 3.0, 0.2

# Cantilever hooks: beam along -z from the lid underside, head pointing out through the wall
HOOK_X = 20.0          # hooks at x = +-20 on both long sides
HOOK_W = 6.0           # beam width (b)
HOOK_T = 1.6           # beam thickness (h)
HOOK_L = 12.0          # root to retaining face (l)
UNDERCUT = 1.2         # head protrusion beyond the beam
LEAD = math.radians(30)   # lead-in ramp angle, from the insertion direction
HEAD_FLAT = 0.5

# Windows the heads catch in
WIN_W, WIN_Z0 = 7.0, 7.0
WIN_Z1 = H - HOOK_L + 0.1   # retaining edge 0.1 mm above the hook's retaining face

# ABS, from the Bayer/Covestro snap-fit design guide
E_ABS = 2300.0          # MPa, secant modulus
EPS_ALLOWED = 0.025     # one-time assembly strain limit
MU = 0.5                # ABS on ABS
DENSITY = 1.05          # g/cm3


def hook_numbers():
    """Deflection, strain and forces for one hook (rectangular, constant section)."""
    y = UNDERCUT - CLEAR                                  # deflection while the head passes the wall
    eps = 1.5 * y * HOOK_T / HOOK_L ** 2                  # = y*h / (0.67 * l^2)
    p = HOOK_W * HOOK_T ** 2 * E_ABS * eps / (6 * HOOK_L)  # deflection force, N
    w = p * (MU + math.tan(LEAD)) / (1 - MU * math.tan(LEAD))  # mating force, N
    return y, eps, p, w


def rounded_box(lx, ly, lz, r, z0=0.0):
    return (cq.Workplane("XY").box(lx, ly, lz, centered=(True, True, False))
            .edges("|Z").fillet(r).translate((0, 0, z0)))


def base():
    b = rounded_box(L, W, H, R_CORNER).edges("<Z").fillet(R_BOTTOM).faces(">Z").shell(-WALL)
    for x in (-HOOK_X, HOOK_X):
        for s in (-1, 1):
            win = (cq.Workplane("XY").box(WIN_W, 3 * WALL, WIN_Z1 - WIN_Z0, centered=(True, True, False))
                   .translate((x, s * (W / 2 - WALL / 2), WIN_Z0)))
            b = b.cut(win)
    return b


def hook_profile():
    """Hook cross-section in the (y, z) plane for the +y wall."""
    y_out = W / 2 - WALL - CLEAR           # beam face next to the wall
    y_in = y_out - HOOK_T
    z_ret = H - HOOK_L                     # retaining face (90 degrees: does not pull apart)
    z_ramp = z_ret - HEAD_FLAT             # top of the lead-in ramp
    z_tip = z_ramp - UNDERCUT / math.tan(LEAD)
    return [(y_in, H), (y_out, H), (y_out, z_ret), (y_out + UNDERCUT, z_ret),
            (y_out + UNDERCUT, z_ramp), (y_out, z_tip), (y_out, z_tip - 0.4), (y_in, z_tip - 0.4)]


def lid():
    part = rounded_box(L, W, LID_T, R_CORNER, H)
    hook = (cq.Workplane("YZ").polyline(hook_profile()).close()
            .extrude(HOOK_W / 2, both=True))
    for x in (-HOOK_X, HOOK_X):
        for s in (1, -1):
            h = hook.translate((x, 0, 0))
            part = part.union(h if s > 0 else h.mirror("XZ"))
    # Locating ribs just inside the base walls, interrupted around the hooks
    yo, xo = W / 2 - WALL - CLEAR, L / 2 - WALL - CLEAR
    ribs = [(-15, 15), (25, 35), (-35, -25)]
    for x0, x1 in ribs:
        for s in (1, -1):
            part = part.union(cq.Workplane("XY").box(x1 - x0, RIB_T, RIB_H, centered=(True, True, False))
                              .translate(((x0 + x1) / 2, s * (yo - RIB_T / 2), H - RIB_H)))
    for s in (1, -1):
        part = part.union(cq.Workplane("XY").box(RIB_T, 30, RIB_H, centered=(True, True, False))
                          .translate((s * (xo - RIB_T / 2), 0, H - RIB_H)))
    return part


if __name__ == "__main__":
    b, lt = base(), lid()
    for name, p in (("base", b), ("lid", lt)):
        s = p.val()
        print(f"{name}: valid {s.isValid()}  volume {s.Volume() / 1000:.1f} cm3  "
              f"mass {s.Volume() / 1000 * DENSITY:.1f} g (ABS)")
    clash = b.intersect(lt).val().Volume()
    print(f"closed-position overlap between base and lid: {clash:.3f} mm3")
    y, eps, p, w = hook_numbers()
    print(f"hook: deflection {y:.2f} mm  strain {eps * 100:.2f} % (limit {EPS_ALLOWED * 100:.1f} %)  "
          f"deflection force {p:.1f} N  mating force {w:.1f} N per hook, {4 * w:.0f} N for the lid")
    asm = cq.Assembly().add(b, name="base", color=cq.Color(0.70, 0.70, 0.66)).add(
        lt, name="lid", color=cq.Color(0.22, 0.54, 0.87))
    asm.export(str(OUT / "snap_enclosure.step"))
