# Better Item — delivery records

## 1.6.0

Add projected Geometry Bounds distribution with signed Spacing (zero allows touching projected bounds); add Match Reference/Set Rotation selection alignment, preserving selected world positions. Reuse the existing evaluated geometry cache and native rotation solver. Add collapsed Solver Settings, typed pending-input diagnostics, warning-level domain refusals and optional technical Details. Origins behavior/data remain compatible. No animation runtime or new viewport manipulators.

## 1.5.7

Feedback-driven numerical validation and affine-stage integrity. See README and the repository audit report for current execution evidence.

## Previous delivery validation records

The following are historical delivery records, not a claim that every combination was rerun in the latest release.

## Validation and source

Version 1.5.5 verifies that renamed final Dimensions modifiers are reused; downstream, duplicate and disabled owned stacks reject without changing geometry, transforms, group matrices or stack order; frame Apply resolves its requested components atomically; compatibility enum serials remain stable; old authoring data/drivers remain untouched; and the current runtime contains no calls that add/remove drivers or insert/delete keyframes. Runtime tests and a real Blender panel check cover the maintenance changes. The maintenance audit and deferred scope are recorded in `docs/better_item/maintenance-1.5.5.md` in the repository.


Version 1.5.4 tests physical widths and dimension edits under inherited nonuniform Gimbal bases, invariance under axis rescaling/reversal, unchanged coordinate bases and base meshes, invalid directions, per-group unavailable states, and Default-mode independence. Cache tests include nested GN, external native keyframes/drivers, shape keys, frame/subframe changes, backward seeks, key edits, modifier toggles, undo/redo and same-frame translation reuse. A real UI test verifies the previously stale 6-to-10 reading and the independently unavailable groups.


The 1.5.3 tests cover read/write rejection without mutation for Quaternion/Axis-Angle, the functioning native storage fields, Euler edits, unsupported Dimensions types, the separate zero-Dimension diagnostic, missing-frame and missing-orientation readouts, valid zero vectors, wrong-scene detection and actual UI rendering. Existing precision, reference, arrangement and undo/redo tests also pass.


Version 1.5.2 tests 1,200 Parent Inverse cancellation cases, 842 movements across -210..210 mm in two unit conventions, real-error rejection, Default / Local channels, native Dimensions, removal of animation runtime, and real timer-driven redraw following native-menu deletion. Earlier compatibility tests covered 1.5.1 authoring files; the current version leaves that data untouched without managing it. The existing precision, layout, frame and arrangement regressions remain covered.

Development tests are in the [GitHub repository](https://github.com/Borbofruto/Blender-Plugins/tree/main/tests/better_item), not inside the installable add-on ZIP. The ZIP contains runtime source, its manifest, license and this manual.

The 1.4.1 regression suite covers linked zero angles, 128 signed-scale rotation combinations, parent inverses, delta transforms, locked-parent roundoff, unavailable geometry, deleted frame choices and conditional UI. A real Blender window test also verifies timer-driven orientation updates, invalid-source removal, recovery and rename.

Version 1.4.2 additionally tests 66 Individual orientation/location combinations for parity between the two panels, all native pivots, World frame origins, external native deletion, surviving enum serials after an intermediate removal, conditional Normal sampling, and 1,500 locked-parent positioning cases. A real two-main-window Blender test verifies separate scene orientation exports, timer updates, native-menu deletion and identical reference controls.

Automated Blender tests also cover vectorized precision, cache reuse, shared geometry and modifier invalidation, memory limits and 2,000 frame renames. They cover live field updates, reference switching without object movement, true vertex extrema, non-destructive oblique Dimensions, shared data isolation, Euler orders, angle turns, proportional links, locks, drivers, alignment/distribution, parenting, saved/live frames, source deletion, renaming, persistence, undo/redo and registration. The actual viewport and panel were also opened and visually inspected. Arrangement regression tests exercise 630 combinations across axis masks, selected/key/reference origins, signed spacing, rotated reference axes, and rotated/scaled parents. They also cover coded validation, reference lines, independent frame components and persistence. Native integration tests execute G/R, compare all Euler/quaternion/axis-angle Gimbal directions with Blender (48 operations), check edit-mode Normal, component/native cycles, invalid-source recovery, old-file migration and new-process persistence.

`arrange.py` plans reference-space arrangements and validates spacing/order; `__init__.py` defines the UI and properties; `transform_view.py` implements live readings and edits; `frames.py` owns independent saved frame components and viewport indicators; `native_refs.py` resolves native pivots/orientations and synchronizes native custom orientations; `engine.py` implements native Scale edits and transactional world positioning; `math_core.py` holds Blender-independent rules; `trace.py` provides read-only affine accounting; `orientation.py` provides orientation utilities; `references.py` defines the common reference options, resolution rules and UI for both consumers.

