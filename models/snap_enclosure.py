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
import numpy as np

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
HOOK_T = 1.6           # beam thickness at the root (h)
HOOK_T_TIP = 1.0       # beam thickness at the head: tapered, which FEA showed cuts peak strain 25 %
HOOK_L = 12.0          # root to retaining face (l)
UNDERCUT = 1.2         # head protrusion beyond the beam
LEAD = math.radians(30)   # lead-in ramp angle, from the insertion direction
HEAD_FLAT = 0.5
ROOT_R = 0.6           # root fillet, both sides of the beam (about h/3; avoids a sharp corner)
RIM_CHAMFER = 1.0      # lead-in chamfer on the base's inner rim; also clears the root fillet

# Windows the heads catch in
WIN_W, WIN_Z0 = 7.0, 7.0
WIN_Z1 = H - HOOK_L + 0.1   # retaining edge 0.1 mm above the hook's retaining face

# ABS, from the Bayer/Covestro snap-fit design guide
E_ABS = 2300.0          # MPa, secant modulus
EPS_ALLOWED = 0.025     # one-time assembly strain limit
MU = 0.5                # ABS on ABS
DENSITY = 1.05          # g/cm3


def hook_numbers(t_tip=None):
    """Deflection, peak strain and forces for one hook from cantilever beam theory.

    Thickness may taper linearly from HOOK_T at the root to t_tip at the head, so the
    deflection is integrated numerically; for a constant section this reduces to the
    guide's eps = 1.5*y*h/l^2 and P = b*h^2*E*eps/(6*l)."""
    t_tip = HOOK_T_TIP if t_tip is None else t_tip
    y = UNDERCUT - CLEAR                                  # deflection while the head passes the wall
    n = 2000
    s = (np.arange(n) + 0.5) * HOOK_L / n                 # distance from the root
    h = HOOK_T + (t_tip - HOOK_T) * s / HOOK_L
    inertia = HOOK_W * h ** 3 / 12
    p = y / np.sum((HOOK_L - s) ** 2 / (E_ABS * inertia)) / (HOOK_L / n)   # tip load for deflection y, N
    eps = float(np.max(6 * p * (HOOK_L - s) / (E_ABS * HOOK_W * h ** 2)))
    w = p * (MU + math.tan(LEAD)) / (1 - MU * math.tan(LEAD))  # mating force, N
    return y, eps, float(p), float(w)


def rounded_box(lx, ly, lz, r, z0=0.0):
    return (cq.Workplane("XY").box(lx, ly, lz, centered=(True, True, False))
            .edges("|Z").fillet(r).translate((0, 0, z0)))


def base():
    b = rounded_box(L, W, H, R_CORNER).edges("<Z").fillet(R_BOTTOM).faces(">Z").shell(-WALL)
    inner_rim = cq.selectors.BoxSelector((-L / 2 + WALL - 0.5, -W / 2 + WALL - 0.5, H - 0.1),
                                         (L / 2 - WALL + 0.5, W / 2 - WALL + 0.5, H + 0.1))
    b = b.edges(inner_rim).chamfer(RIM_CHAMFER)
    for x in (-HOOK_X, HOOK_X):
        for s in (-1, 1):
            win = (cq.Workplane("XY").box(WIN_W, 3 * WALL, WIN_Z1 - WIN_Z0, centered=(True, True, False))
                   .translate((x, s * (W / 2 - WALL / 2), WIN_Z0)))
            b = b.cut(win)
    return b


Y_OUT = W / 2 - WALL - CLEAR         # beam face next to the wall
Y_IN = Y_OUT - HOOK_T
Z_RET = H - HOOK_L                   # retaining face (90 degrees: does not pull apart)
Z_RAMP = Z_RET - HEAD_FLAT           # top of the lead-in ramp
Z_TIP = Z_RAMP - UNDERCUT / math.tan(LEAD)


def hook_sketch(t_tip=None):
    """Closed hook cross-section in the (y, z) plane for the +y wall."""
    y_in_tip = Y_OUT - (HOOK_T_TIP if t_tip is None else t_tip)
    return (cq.Workplane("YZ").polyline([(Y_IN, H), (Y_OUT, H), (Y_OUT, Z_RET), (Y_OUT + UNDERCUT, Z_RET),
                                         (Y_OUT + UNDERCUT, Z_RAMP), (Y_OUT, Z_TIP), (Y_OUT, Z_TIP - 0.4),
                                         (y_in_tip, Z_TIP - 0.4), (y_in_tip, Z_RET)]).close())


def add_hook(part, x, side, root_r=ROOT_R, t_tip=None):
    """Union one hook under the lid at (x, +-y) and fillet all four of its root edges."""
    hook = hook_sketch(t_tip).extrude(HOOK_W / 2, both=True).translate((x, 0, 0))
    part = part.union(hook if side > 0 else hook.mirror("XZ"))
    if root_r > 0:
        y0, y1 = sorted((side * Y_IN, side * Y_OUT))
        root = cq.selectors.BoxSelector((x - HOOK_W / 2 - 0.05, y0 - 0.05, H - 0.05),
                                        (x + HOOK_W / 2 + 0.05, y1 + 0.05, H + 0.05))
        part = part.edges(root).fillet(root_r)
    return part


def lid():
    part = rounded_box(L, W, LID_T, R_CORNER, H)
    for x in (-HOOK_X, HOOK_X):
        for side in (1, -1):
            part = add_hook(part, x, side)
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
