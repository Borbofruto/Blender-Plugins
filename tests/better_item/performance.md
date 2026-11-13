# Dimensions benchmark: 1.2.0 versus 1.2.1

Blender 5.2.3 LTS, same machine and synthetic mesh: 250,000 vertices with seeded random coordinates, no faces or modifiers. Nontrivial projection axes. Timed with `time.perf_counter` around `transform_view.dimensions`, after updating the dependency graph.

The old implementation is the version at commit `55e9daa6dd190cf2f9c0f09ac0d997a859d93327`.

| Scenario | 1.2.0 | 1.2.1 |
| --- | --- | --- |
| First read following translation | 272.12 ms | 10.98 ms |
| Subsequent translation read 1 | 268.64 ms | 0.030 ms |
| Subsequent translation read 2 | 257.77 ms | 0.012 ms |
| Reprojection after native Scale changes | Not separately measured | 2.32 / 2.45 / 2.45 ms |

Both versions returned the same extents for the translation test: `(3.0378150939941406, 2.3937989473342896, 3.0556617975234985)`.

These are Dimensions calculation times, not full interaction or viewport timings. Dependency-graph evaluation, modifiers, drawing and scene complexity add their own costs. Results vary by machine and mesh.

Run the current benchmark from the repository root in a separate Blender process:

```powershell
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tests/better_item/benchmark_dimensions.py
```

`test_better_item_cache.py` checks projection accuracy, translation/rotation reuse, unrelated edits, shared mesh changes, an externally driven Mirror modifier, cache memory bounds, and 2,000 frame renames. Existing live-edit, frame, undo/redo and registration tests also pass.
