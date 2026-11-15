# Better Item 1.7.2 — Geometry precision and sidebar inspection

## Findings confirmed
The 1.7.1 checker used width/gap-relative float32 tolerance but omitted the rounding of large stored world translations. The planner was correct in the reproduced scenes; verification rejected 14 of 21 valid scenarios. The sidebar also recomputed inspection on each draw and again in the Live getter. The unused native_refs import was present.

## Corrections
- Add the projected `engine._world_roundoff` budget to geometric boundary verification in Offset and Endpoint. Both adjacent object budgets contribute to gap verification. This accounts for native translations, parents, parent-inverse products and deltas; it is not an arbitrary scene-unit epsilon.
- Preserve atomic rejection of collapsed positive gaps and collapsed positive advances of occupied slots. Coordinate allowance is separate from geometry-invariance checks, including symmetric Endpoint shape changes whose centers remain unchanged.
- Compare measured nonzero geometric gaps with their storage budget, so valid large-scene results are not immediately reported as Mixed. Collapsed and nonzero intervals are not labelled one uniform nonzero gap.
- Cache scalar inspection results for at most four signatures, shared by drawing and the Live getter. Selection, active object, scene/view-layer, resolved reference values, method and measurement parameters are in the signature. Evaluated-scene updates, frame changes, arrangement edits and load/Undo/Redo invalidate results. Distribution application never uses this cache to skip planning or validation.
- Remove the unused import. No UI layout, feature, constraint policy or animation runtime is added.

## Executed evidence
Blender 5.2.3 LTS / Windows only.

### Large scenes and long chains
- 21 deterministic cases: Offset chains of 200 two-unit cubes at an initial/reference offset of 100, gaps 0.05 / 0.2 / 1.0, three seeds; Endpoint cases with 12 pieces at 300 / 1000 and four pieces at 5000, four seeds.
- **Before: 7 accepted / 14 rejected. After: 21 accepted / 0 rejected.** Independent float64 world-vertex projected-bound oracle verifies gaps, not just a reuse of the planner.
- Maximum actual gap error in these cases: 0.00040064 Blender units, at the 5000 offset. This remains a finite float32 representation; no claim of exact real-number geometry is made.
- Each accepted result reports uniform spacing within the storage budget.
- At 1e9: unresolved positive/zero Offset occupied chains, an Endpoint chain with collapsed gaps, and coincident quantized endpoints reject and restore poses. Symmetric position-driven shape changes also reject independently of the widened position budget.

### Inspection performance and freshness
One measured run, seconds per call (mean of five warm calls):

| Objects | Basis | First inspection | Cached inspection |
|---|---|---:|---:|
| 600 | Origins | 0.00606 | 0.000387 |
| 600 | Geometry Bounds | 0.260 | 0.000341 |
| 600 | Volume Centroid | 0.364 | 0.000348 |
| 1500 | Origins | 0.0126 | 0.000744 |
| 1500 | Geometry Bounds | 0.660 | 0.000749 |
| 1500 | Volume Centroid | 0.884 | 0.000774 |

This improves unchanged redraws; the first inspection after a relevant change still costs a full measurement. The cache deliberately invalidates conservatively on evaluated scene changes, including unrelated updates.

- Call-count instrumentation confirms draw and getter share one underlying pass.
- Freshness checks: Location, Rotation, Scale, spacing sign, axes, placement basis, shape keys, modifier creation/state, mesh changes, frame evaluation, saved/manual Frame values, Endpoint values/cursor, active object, external Geometry Nodes dependency and unselected reference geometry. Cached results are compared with uncached reads.
- Undo/Redo clears cached inspection. Cache remains bounded; unregister removes callbacks and cached data.
- Real Blender sidebar with 600 objects: five stable redraw/timer cycles reuse **one** full inspection. No draw traceback in the log.
- Existing real-sidebar six-phase live/Endpoint test passes; it edits RNA controls and does not claim mouse-gesture automation.

### Existing regressions repeated
320 Endpoint + 140 Offset batches across all bases, parents, mirrors, unit scales and masks; 168 older geometric combinations and 72 orientation batches; contracts/persistence, 1.7.1 axis/sign/checkbox checks, preview operator Undo/Redo, geometry dependency rollback and cache regressions. The cache154 suite also passes for nested external GN dependencies and frame/subframe changes. These are this run's checks, not a claim to have repeated all externally reported thousands of cases.

Installer validation, syntax parsing, archive integrity and the three new headless suites against extracted ZIP contents are checked before publication. New scripts/results are in `tests/better_item/` and `tests/better_item/results/1.7.2/`. The baseline JSON intentionally describes the older version's rejected cases.

## Scope
This release fixes existing precision and performance behavior. Feature development remains outside this correction. Geometry below native storage resolution, constraints requiring a different solving policy, Normal-selection optimization and new interactions are not redefined here. Blender versions other than 5.2.3 were not runtime-tested.
