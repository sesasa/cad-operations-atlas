# CAD Operations Atlas

An interactive 3D guide to the modeling operations behind real parts, from extrude and loft to zebra stripes and mold splits. Each operation builds itself in front of you: watch it play, scrub the timeline, and drag to rotate.

**[▶ Open the live demo](https://sesasa.github.io/cad-operations-atlas/)**

[![CAD Operations Atlas: the shortboard worked example at the zebra check step](docs/screenshot.png)](https://sesasa.github.io/cad-operations-atlas/)

## What's inside

- **44 operations** in two tiers, Basics and Advanced, grouped like a CAD feature tree.
- **Two worked examples**, each built in ten steps from operations in the atlas:
  - a 6'0" × 19.7" × 2.5" shortboard (28.5 L), from the outline sketch to a zebra-stripe surface check;
  - a 13¼" × 17" three-blade outboard propeller, backed by a real CAD model you can download as a [STEP file](models/propeller.step).
- **Deep links** for every operation, so you can share one directly, for example [`#loft`](https://sesasa.github.io/cad-operations-atlas/#loft) or [`#zebra-stripes`](https://sesasa.github.io/cad-operations-atlas/#zebra-stripes).
- Works on phones and follows your system's light or dark mode.

### Basics

| Group | Operations |
| --- | --- |
| Solid features | Extrude, Revolve, Sweep, Loft, Shell, Fillet, Chamfer, Draft, Rib, Cut and hole |
| Curves | 3D spline, Projected curve, Helix, Split line |
| Surfaces | Boundary surface, Fill surface, Offset surface, Ruled surface, Extend surface, Trim surface, Knit surface, Thicken |
| Bodies and patterns | Mirror, Linear pattern, Circular pattern, Combine, Split body, Wrap, Flex |

### Advanced

| Group | Operations |
| --- | --- |
| Advanced features | Variable-radius fillet, Twisted sweep, Loft with guide curves, Modeled thread, Dome, Cut with surface, Curve-driven pattern |
| Freeform and analysis | Subdivision cage, Zebra stripes, Curvature map, Draft analysis, Scan to surface |
| Industry tools | Sheet metal bend, Weldment frame, Core and cavity |

## Worked example 1: a 6'0" shortboard

The Examples tab holds complete parts built only from operations in the atlas. Each step has "Uses" chips that jump to the operations it relies on.

| Step | What happens | Uses |
| --- | --- | --- |
| 1. Outline sketch | Half the plan shape as one spline on the top plane | 3D spline |
| 2. Rocker and deck line | Bottom rocker and deck curve on the side plane | 3D spline |
| 3. Rail curve | Project the outline onto the rocker to get the 3D rail | Projected curve |
| 4. Cross-sections | Five half-sections on reference planes | Loft with guide curves |
| 5. Loft the half body | Loft through the sections, guided by rocker, deck, and rail | Loft with guide curves, Boundary surface |
| 6. Mirror and knit | Mirror across the stringer plane and knit into one solid | Mirror, Knit surface |
| 7. Swallow tail cut | Extruded cut from a V-shaped sketch | Cut and hole |
| 8. Thruster fins | Fins extruded, filleted, and mirrored with toe and cant | Extrude, Fillet, Mirror |
| 9. Leash plug | Revolved cut on the deck | Revolve, Cut and hole |
| 10. Zebra check | Stripes confirm the surfaces are fair | Zebra stripes, Curvature map |

![Thruster fins step in dark mode](docs/screenshot-fins.png)

## Worked example 2: an outboard propeller

A 13¼" diameter, 17" pitch, three-blade aluminium propeller with a through-hub exhaust and a 15-tooth spline bore. It comes as a real parametric model: [`models/propeller.py`](models/propeller.py) builds it with [CadQuery](https://cadquery.readthedocs.io/) on OpenCascade (the geometry kernel FreeCAD uses) and exports [`models/propeller.step`](models/propeller.step), which opens in FreeCAD, SOLIDWORKS, Fusion, Onshape and other CAD tools. The page draws the same blade from the same formulas.

| | |
| --- | --- |
| Diameter × pitch | 337.6 mm × 432 mm (13¼" × 17") |
| Blades | 3, raked 15° aft, 28° tip skew |
| Sections | 12 flat-face airfoil sections, pitch angle 67° at the root to 22° at the tip |
| Hub | Barrel Ø74 to Ø66 mm × 100 mm, exhaust passage, sleeve, 3 ribs, 15-tooth spline |
| Volume and mass | 510 cm³, 1.38 kg in aluminium (2.70 g/cm³) |

| Step | What happens | Uses |
| --- | --- | --- |
| 1. Hub barrel | Revolve a tapered profile into the barrel | Revolve |
| 2. Pitch helices | Helices at three radii set the 17" pitch | Helix |
| 3. Blade sections | Twelve airfoil sections, each turned to its pitch angle, raked and skewed | 3D spline |
| 4. Loft the blade | Smooth loft through the sections, guided by leading and trailing edges | Loft with guide curves |
| 5. Flared root | Root sections grow wider and thicker, blending into the hub | Variable-radius fillet |
| 6. Pattern the blades | Copy the blade twice around the shaft axis | Circular pattern |
| 7. Combine and bore | Join blades and barrel, then cut the exhaust passage | Combine, Cut and hole |
| 8. Sleeve and ribs | Inner sleeve tied to the barrel by three ribs | Revolve, Rib, Circular pattern |
| 9. Spline bore | 15-tooth spline cut through the sleeve | Cut and hole, Circular pattern |
| 10. Zebra check | Stripes run smoothly across each blade | Zebra stripes, Curvature map |

[![Propeller zebra check step](docs/screenshot-propeller.png)](https://sesasa.github.io/cad-operations-atlas/#propeller-10)

To rebuild the STEP file after changing a dimension:

```sh
pip install cadquery
python models/propeller.py
# valid: True  diameter: 337.6 mm  length: 112.1 mm  volume: 510.1 cm3  mass (Al 2.70 g/cm3): 1.38 kg
```

A note on the root: a true variable-radius fillet between the lofted blade and the conical barrel fails in OpenCascade, a common problem with this kind of intersection. The model uses the usual propeller-design alternative instead: the root sections flare wider (+20 mm chord) and thicker (+9 mm), so the loft itself blends into the hub with a radius that varies along the chord.

## Color key

| Color | Meaning |
| --- | --- |
| Red | Input sketch, tool, or scan |
| Orange | Live preview |
| Blue | Finished feature |
| Gray | Existing geometry |
| Green | Added patch |
| Purple | Control cage |

## Run it locally

It is a single HTML file with no build step. Open `index.html` in any modern browser, or serve the folder:

```sh
python3 -m http.server 8000
# then visit http://localhost:8000
```

An internet connection is needed for [three.js r128](https://threejs.org/) (loaded from cdnjs) and the Google Fonts.

## Notes

The previews are simplified schematics for learning, not CAD kernels; the propeller is the exception, with a real solid model in `models/`. Operation names follow SOLIDWORKS terms; most CAD tools (Fusion, Onshape, CATIA, NX, Rhino) have the same operations under similar names.

## License

[MIT](LICENSE)
