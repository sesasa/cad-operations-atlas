# CAD Operations Atlas

An interactive 3D guide to the modeling operations behind real parts, from extrude and loft to zebra stripes and mold splits. Each operation builds itself in front of you: watch it play, scrub the timeline, and drag to rotate.

**[▶ Open the live demo](https://sesasa.github.io/cad-operations-atlas/)**

[![CAD Operations Atlas: the shortboard worked example at the zebra check step](docs/screenshot.png)](https://sesasa.github.io/cad-operations-atlas/)

## What's inside

- **44 operations** in two tiers, Basics and Advanced, grouped like a CAD feature tree.
- **A worked example**: a 6'0" × 19.7" × 2.5" shortboard (28.5 L) modeled in ten steps, from the outline sketch to a zebra-stripe surface check.
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

## Worked example: a 6'0" shortboard

The page opens on a complete part built only from operations in the atlas. Each step has "Uses" chips that jump to the operations it relies on.

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

The previews are simplified schematics for learning, not CAD kernels. Operation names follow SOLIDWORKS terms; most CAD tools (Fusion, Onshape, CATIA, NX, Rhino) have the same operations under similar names.

## License

[MIT](LICENSE)
