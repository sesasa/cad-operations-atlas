"""Finite-element check of one snap hook from models/snap_enclosure.py.

3D linear elastic analysis, displacement controlled: the hook head's contact face
is pushed 1.0 mm inward, which is what the base wall does while the lid closes.
A patch of the lid around the hook is included and clamped where it joins the rest
of the lid, so the root fillet and the lid's own flexibility are part of the model.

    CAD (CadQuery)  ->  mesh (gmsh, tetrahedra)  ->  solve (scikit-fem, quadratic P2 elements)

    pip install cadquery gmsh scikit-fem pypardiso
    python models/snap_fea.py          # prints the results, writes snap_fea.json and snap_fea.js

snap_fea.js holds the deformed surface mesh and strain field that the atlas page draws.
"""
import json
import math
import pathlib
import sys
import tempfile
import time

import cadquery as cq
import gmsh
import numpy as np
from skfem import (Basis, ElementTetP1, ElementTetP2, ElementVector, FacetBasis, Functional, LinearForm, MeshTet,
                   asm, condense)
from skfem.models.elasticity import lame_parameters, linear_elasticity
import pypardiso

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import snap_enclosure as se  # noqa: E402

NU = 0.35                      # Poisson's ratio, ABS
DEFLECTION = se.UNDERCUT - se.CLEAR
PATCH_X, PATCH_Y0 = 8.0, 13.0  # lid patch: |x| <= 8 mm, y from 13 mm to the lid edge
Y_OUT, Y_IN, Z_RET = se.Y_OUT, se.Y_IN, se.Z_RET


def geometry(root_r, t_tip):
    lid = (cq.Workplane("XY").box(2 * PATCH_X, se.W / 2 - PATCH_Y0, se.LID_T, centered=False)
           .translate((-PATCH_X, PATCH_Y0, se.H)))
    return se.add_hook(lid, 0.0, 1, root_r, t_tip)


def mesh(root_r, t_tip, h_root, h_beam=0.3, h_far=0.8):
    """Tetrahedra: h_root on the root fillet (or sharp root edge), h_beam along the hook, h_far in the lid."""
    with tempfile.TemporaryDirectory() as tmp:
        step = str(pathlib.Path(tmp) / "hook.step")
        cq.exporters.export(geometry(root_r, t_tip), step)
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("hook")
        gmsh.model.occ.importShapes(step)
        gmsh.model.occ.synchronize()
    root = [c for _, c in gmsh.model.getEntities(1)
            if (lambda b: b[2] > se.H - root_r - 1e-3 and b[5] < se.H + 1e-3 and b[1] > Y_IN - root_r - 1e-3
                and b[4] < Y_OUT + root_r + 1e-3 and b[0] > -se.HOOK_W / 2 - root_r - 1e-3
                and b[3] < se.HOOK_W / 2 + root_r + 1e-3)
            (gmsh.model.getBoundingBox(1, c))]
    f = gmsh.model.mesh.field
    d = f.add("Distance")
    f.setNumbers(d, "CurvesList", root)
    f.setNumber(d, "Sampling", 200)
    th = f.add("Threshold")
    for k, v in (("InField", d), ("SizeMin", h_root), ("SizeMax", h_far), ("DistMin", 0.25), ("DistMax", 1.5)):
        f.setNumber(th, k, v)
    bx = f.add("Box")
    for k, v in (("VIn", h_beam), ("VOut", h_far), ("XMin", -se.HOOK_W / 2 - 0.5), ("XMax", se.HOOK_W / 2 + 0.5),
                 ("YMin", Y_IN - 0.8), ("YMax", Y_OUT + se.UNDERCUT + 0.3), ("ZMin", 6.0), ("ZMax", se.H + 0.6),
                 ("Thickness", 1.0)):
        f.setNumber(bx, k, v)
    m = f.add("Min")
    f.setNumbers(m, "FieldsList", [th, bx])
    f.setAsBackgroundMesh(m)
    for k in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
        gmsh.option.setNumber(k, 0)
    gmsh.model.mesh.generate(3)

    tags, xyz, _ = gmsh.model.mesh.getNodes()
    index = {t: i for i, t in enumerate(tags)}
    _, _, conn = gmsh.model.mesh.getElements(3)
    tets = np.vectorize(index.get)(np.array(conn[0]).reshape(-1, 4))
    groups = {"fixed": set(), "contact": set()}
    for _, s in gmsh.model.getEntities(2):
        x0, y0, z0, x1, y1, z1 = gmsh.model.getBoundingBox(2, s)
        if abs(abs(x0) - PATCH_X) < 1e-3 and abs(x1 - x0) < 1e-3 or abs(y0 - PATCH_Y0) < 1e-3 and abs(y1 - y0) < 1e-3:
            name = "fixed"                                   # where the patch joins the rest of the lid
        elif abs(y0 - (Y_OUT + se.UNDERCUT)) < 1e-3 and abs(y1 - y0) < 1e-3:
            name = "contact"                                 # head face that slides on the wall
        else:
            continue
        groups[name] |= {index[t] for t in gmsh.model.mesh.getNodes(2, s, includeBoundary=True)[0]}
    gmsh.finalize()
    return MeshTet(xyz.reshape(-1, 3).T, tets.T), groups


def direct_solve(A, b):
    """Sparse direct solve (Intel MKL PARDISO); multigrid converges poorly on this thin, end-held part."""
    x = pypardiso.spsolve(A.tocsr(), b)
    assert np.linalg.norm(A @ x - b) < 1e-8 * np.linalg.norm(b), "solve failed"
    return x


def facets_in(m, nodes):
    bf = m.boundary_facets()
    keep = np.all(np.isin(m.facets[:, bf], np.fromiter(nodes, int)), axis=0)
    return bf[keep]


def analyse(root_r, t_tip, h_root, keep_field=False, h_beam=0.3, h_far=0.8):
    t0 = time.time()
    m, groups = mesh(root_r, t_tip, h_root, h_beam, h_far)
    basis = Basis(m, ElementVector(ElementTetP2()))
    lam, mu = lame_parameters(se.E_ABS, NU)
    K = asm(linear_elasticity(lam, mu), basis)
    fixed = basis.get_dofs(facets_in(m, groups["fixed"])).all()
    # 1 N spread evenly over the head's contact face, pointing inward; the head is free to tilt
    fb = FacetBasis(m, basis.elem, facets=facets_in(m, groups["contact"]))
    area = asm(Functional(lambda w: 1.0 + 0 * w.x[0]), fb)
    f = asm(LinearForm(lambda v, w: -v[1] / area), fb)
    u = np.zeros(K.shape[0])
    A, b, _, I = condense(K, f, D=fixed)
    u[I] = direct_solve(A, b)
    mean_uy = asm(Functional(lambda w: w["u"][1]), fb, u=fb.interpolate(u)) / area
    scale = DEFLECTION / -mean_uy                            # linear: scale to a 1.0 mm deflection
    u *= scale
    force = scale                                            # N, the push the wall must supply

    g = basis.interpolate(u).grad                             # (3, 3, elements, points)
    eps = 0.5 * (g + g.transpose(1, 0, 2, 3))
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    sig = 2 * mu * eps + lam * tr * np.eye(3)[:, :, None, None]
    e1 = np.linalg.eigvalsh(eps.transpose(2, 3, 0, 1))[..., -1]           # max principal strain
    vm = np.sqrt(0.5 * ((sig[0, 0] - sig[1, 1]) ** 2 + (sig[1, 1] - sig[2, 2]) ** 2 + (sig[2, 2] - sig[0, 0]) ** 2)
                 + 3 * (sig[0, 1] ** 2 + sig[1, 2] ** 2 + sig[0, 2] ** 2))
    xq = basis.global_coordinates().value
    region = xq[2] > Z_RET + 1.0          # beam, root and lid; leaves out the loaded head face
    e1r = np.where(region, e1, -np.inf)
    k = np.unravel_index(np.argmax(e1r), e1.shape)
    # nominal strain on the beam's outer face, 3 mm below the root (away from the fillet)
    on_face = (np.abs(xq[1] - Y_OUT) < 0.25) & (np.abs(xq[2] - (se.H - 3.0)) < 0.4) & (np.abs(xq[0]) < 2.0)
    res = {"root_r": root_r, "t_tip": t_tip, "h_root": h_root, "nodes": int(m.nvertices), "elements": int(m.nelements),
           "dofs": int(K.shape[0]), "force_N": float(force), "peak_strain": float(e1[k]),
           "peak_at_mm": [round(float(xq[i][k]), 2) for i in range(3)], "peak_von_mises_MPa": float(vm[region].max()),
           "strain_3mm_below_root": float(e1[on_face].max()) if on_face.any() else None,
           "seconds": round(time.time() - t0, 1)}
    if keep_field:
        b1 = basis.with_element(ElementTetP1())
        nodal = np.array([[b1.project(eps[i, j]) for j in range(3)] for i in range(3)])  # (3, 3, vertices)
        res["field"] = (m, u[basis.nodal_dofs], np.linalg.eigvalsh(nodal.transpose(2, 0, 1))[:, -1])
    return res


def hand_calc():
    y, eps, p, w = se.hook_numbers()
    return {"deflection_mm": y, "strain": eps, "force_N": p, "mating_force_N": w}


def export_field(m, disp, e1):
    """Boundary surface with per-vertex displacement and max principal strain, as integers
    (position x100, displacement x1e4, strain x1e5) to keep the page's data file small."""
    bf = m.boundary_facets()
    tri = m.facets[:, bf].copy()
    a, b, c = (m.p[:, tri[i]] for i in range(3))
    inside = m.p[:, m.t[:, m.f2t[0, bf]]].mean(axis=1)               # centroid of the owning tetrahedron
    flip = np.einsum("ij,ij->j", np.cross(b - a, c - a, axis=0), inside - a) > 0
    tri[1, flip], tri[2, flip] = tri[2, flip], tri[1, flip].copy()   # outward-facing triangles
    used, inv = np.unique(tri, return_inverse=True)
    q = lambda a, k: np.rint(a * k).astype(int).tolist()
    return {"p": q(m.p[:, used].T.ravel(), 100), "u": q(disp[:, used].T.ravel(), 1e4),
            "e": q(np.clip(e1[used], 0, None), 1e5), "t": inv.reshape(3, -1).T.ravel().tolist()}


STUDY = (("straight hook, R0.6 root fillets", 0.6, 1.6, (0.24, 0.12, 0.08)),
         ("tapered hook, 1.6 to 1.0 mm, R0.6 root fillets", 0.6, 1.0, (0.24, 0.12, 0.08)),
         ("straight hook, sharp root", 0.0, 1.6, (0.24, 0.12, 0.08)))

if __name__ == "__main__":
    out = HERE / "snap_fea.json"
    if "--display-only" in sys.argv and out.exists():
        runs = json.loads(out.read_text())["runs"]            # reuse the mesh study, redraw the page data
    else:
        runs = []
        for design, root_r, t_tip, sizes in STUDY:
            for h in sizes:
                _, eps, p, _ = se.hook_numbers(t_tip)
                r = {"design": design, **analyse(root_r, t_tip, h), "hand_force_N": p, "hand_strain": eps}
                runs.append(r)
                print(f"{design:48s} h {h:.2f} mm {r['dofs']:7d} dofs  force {r['force_N']:.2f} N  "
                      f"peak strain {r['peak_strain'] * 100:.2f} %  at {r['peak_at_mm']}  {r['seconds']} s", flush=True)
    chosen = [r for r in runs if r["root_r"] == se.ROOT_R and r["t_tip"] == se.HOOK_T_TIP]
    best = min(chosen, key=lambda r: r["h_root"])           # finest mesh of the adopted design
    hc = hand_calc()
    print(f"adopted design: FEA force {best['force_N']:.2f} N, peak strain {best['peak_strain'] * 100:.2f} %; "
          f"hand calculation {hc['force_N']:.2f} N, {hc['strain'] * 100:.2f} %")
    show = analyse(se.ROOT_R, se.HOOK_T_TIP, 0.24, keep_field=True, h_beam=0.45, h_far=1.2)   # coarser mesh for drawing
    m, disp, e1 = show.pop("field")
    field = export_field(m, disp, e1)
    summary = {"material": {"E_MPa": se.E_ABS, "nu": NU, "strain_limit": se.EPS_ALLOWED},
               "load": {"deflection_mm": DEFLECTION, "where": "even pressure on the head's contact face, scaled to 1.0 mm"},
               "hand_calc": hc, "runs": runs, "result": best}
    out.write_text(json.dumps(summary, indent=1))
    (HERE / "snap_fea.js").write_text("// Generated by models/snap_fea.py: FEA surface mesh and results for the atlas page.\n"
                                      "window.SNAP_FEA=" + json.dumps({"summary": {k: summary[k] for k in ("hand_calc", "result", "load")},
                                                                       **field}, separators=(",", ":")) + ";\n")
    print(f"display mesh: {len(field['t']) // 3} triangles, {len(field['e'])} vertices")
