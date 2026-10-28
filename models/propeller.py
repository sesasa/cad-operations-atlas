"""Parametric three-blade outboard propeller, built with CadQuery (OpenCascade).

13 1/4" diameter x 17" pitch, aluminium, through-hub exhaust, 15-tooth spline bore.
Units are millimetres; the propeller axis is +Z, with the front face at z = 0.

    pip install cadquery
    python models/propeller.py            # writes models/propeller.step

The atlas page (index.html) redraws the same part from the same formulas in
JavaScript (the PROP_ block there), so keep the two in step when changing a number.
"""
import math
import pathlib

import cadquery as cq
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

OUT = pathlib.Path(__file__).resolve().parent

# Main dimensions
R = 168.0                     # tip radius (13.25" diameter)
PITCH = 432.0                 # 17" pitch
BLADES = 3
RAKE = math.radians(15)       # blades lean aft
SKEW = math.radians(28)       # tip skew, growing with the square of the span

# Hub: barrel (outer tube), inner sleeve, three ribs, splined bore
HUB_L = 100.0
HUB_R0, HUB_R1 = 37.0, 33.0   # barrel outer radius, front and rear
WALL = 5.0
SLEEVE_R = 17.0
RIB_T = 5.0
SPLINE_TEETH, SPLINE_MAJOR, SPLINE_MINOR = 15, 11.5, 10.0

# Blade sections, as fractions of the tip radius
STATIONS = [0.17, 0.21, 0.25, 0.30, 0.38, 0.47, 0.56, 0.65, 0.75, 0.85, 0.93, 1.0]
X0 = STATIONS[0]              # root section sits inside the barrel wall
C_MAX = 140.0
Z_MID = 50.0


def flare(x):
    """Root flare: 0 out on the blade, 1 at the root section."""
    return max(0.0, 1 - (x * R - X0 * R) / 25) ** 2


def chord(x):
    return C_MAX * math.sqrt(max(0.0, 1 - ((x - 0.55) / 0.48) ** 2)) + 6.0 + 20 * flare(x)


def thickness(x):
    return 14.0 - 12.0 * (x - X0) / (1 - X0) + 9 * flare(x)


def pitch_angle(x):
    return math.atan(PITCH / (2 * math.pi * x * R))


def section_points(x, n=24):
    """Closed flat-face ogival section at r = x*R, as 3D points."""
    r = x * R
    c, t, phi = chord(x), thickness(x), pitch_angle(x)
    skew = SKEW * ((x - X0) / (1 - X0)) ** 2
    z0 = Z_MID + (r - X0 * R) * math.tan(RAKE)
    pts = []
    for k in range(n):                                # back: circular-arc camber
        s = -c / 2 + c * k / n
        u = 2 * s / c
        pts.append((s, max(0.6, t * (1 - u * u))))
    for k in range(n):                                # face: nearly flat
        s = c / 2 - c * k / n
        u = 2 * s / c
        pts.append((s, -0.6 - 0.04 * t * (1 - u * u)))
    cx, cz = math.cos(phi), math.sin(phi)             # chord follows the pitch helix
    cs, sn = math.cos(skew), math.sin(skew)
    out = []
    for s, h in pts:                                  # flat section on the plane tangent to r,
        u = s * cx - h * cz                           # turned about the axis by the skew angle
        out.append(cq.Vector(u * cs + r * sn, -u * sn + r * cs, z0 + s * cz + h * cx))
    return out


def blade():
    """Smooth loft through the sections. The sections are built point-for-point alike,
    so OpenCascade's compatibility pass (which fails on this twist) is switched off."""
    loft = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    loft.CheckCompatibility(False)
    for x in STATIONS:
        loft.AddWire(cq.Wire.assembleEdges([cq.Edge.makeSpline(section_points(x), periodic=True)]).wrapped)
    loft.Build()
    return cq.Solid(loft.Shape())


def ring(r_front, r_rear, z0=0.0, z1=HUB_L):
    """Solid of revolution under a straight (conical) profile."""
    return (cq.Workplane("XZ")
            .polyline([(0, z0), (r_front, z0), (r_rear, z1), (0, z1)]).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)))


def spline_pts():
    pts, w = [], math.pi / SPLINE_TEETH * 0.5
    for k in range(SPLINE_TEETH):
        a = 2 * math.pi * k / SPLINE_TEETH
        for da, rr in ((-w, SPLINE_MINOR), (-w * 0.6, SPLINE_MAJOR), (w * 0.6, SPLINE_MAJOR), (w, SPLINE_MINOR)):
            pts.append((rr * math.cos(a + da), rr * math.sin(a + da)))
    return pts


def build():
    body = ring(HUB_R0, HUB_R1)                                       # revolve the barrel
    b = blade()                                                       # sections, flared root, loft
    for i in range(BLADES):                                           # circular pattern + combine
        body = body.union(cq.Workplane().add(b.rotate(cq.Vector(), cq.Vector(0, 0, 1), 360 * i / BLADES)))
    cavity = ring(HUB_R0 - WALL, HUB_R1 - WALL, -1, HUB_L + 1)
    body = body.cut(cavity)                                           # exhaust passage
    rib = (cq.Workplane("XY").box(HUB_R0, RIB_T, HUB_L - 16, centered=(False, True, False))
           .translate((SLEEVE_R - 2, 0, 8)))
    ribs = rib
    for i in range(1, BLADES):
        ribs = ribs.union(rib.rotate((0, 0, 0), (0, 0, 1), 360 * i / BLADES))
    ribs = ribs.rotate((0, 0, 0), (0, 0, 1), 180 / BLADES).intersect(cavity)
    body = body.union(ring(SLEEVE_R, SLEEVE_R)).union(ribs)           # sleeve and ribs
    bore = cq.Workplane("XY").polyline(spline_pts()).close().extrude(HUB_L + 2).translate((0, 0, -1))
    return body.cut(bore)                                             # splined bore


if __name__ == "__main__":
    part = build()
    solid = part.val()
    bb = solid.BoundingBox()
    vol = solid.Volume() / 1000
    print(f"valid: {solid.isValid()}  diameter: {2 * max(bb.xmax, bb.ymax, -bb.xmin, -bb.ymin):.1f} mm  "
          f"length: {bb.zlen:.1f} mm  volume: {vol:.1f} cm3  mass (Al 2.70 g/cm3): {vol * 2.70 / 1000:.2f} kg")
    cq.exporters.export(part, str(OUT / "propeller.step"))
