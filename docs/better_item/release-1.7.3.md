# Better Item 1.7.3 — Endpoint point placement and reference-driven Live

## Endpoint and Placement
- Offset offers all five bases. Endpoint offers only Origins, Bounds Center, Center of Mass (Surface) and Center of Mass (Volume). Point placement may overlap geometry; it does not resize, rotate or change mesh data to make pieces fit.
- The old Endpoint occupied-interval fit solver was removed. Geometry Bounds is an Offset operation. Direct retired API requests return a setup diagnostic (BI-E002), not an insufficient-space claim.
- Each method remembers its own Placement choice, including F9. Explicit enum IDs retain saved values. Old Endpoint / Geometry data migrates to Origins with a visible notice; Geometry Bounds remains the remembered Offset choice. The notice clears when Placement is explicitly chosen.
- Labels use Blender's Center of Mass (Surface / Volume) wording. New point verification rejects distinct placement points that collapse at native coordinate resolution; this is separate from geometries overlapping normally.

## Live semantics
- Enabling Live captures target identities and the active object, without moving or normalizing anything. Changing Blender selection does not retarget the session. Active Object / Active Element references use the captured identity.
- An observer is registered only for the enabled session, checking spatial inputs at 0.1-second intervals. It follows cursor, object, Manual and Frame Location sources, and applicable orientation/geometry changes. Computation can take longer for large selections; this is not a fixed-FPS promise.
- Endpoint order is kept after the first successful solve for each method/basis/path/axis configuration. Selected source anchors can be moved normally by the user and are not restored to initial poses by distribution.
- Readout uses captured targets even when deselected. The sidebar reports captured count and active name. Alignment still operates on the actual selection.
- Manual transforms of moving targets pause Live with actionable guidance. Invalid/missing sources retain the last valid poses and can recover when fixed. New unrelated geometry does not normalize an untouched capture.
- Disable Live to keep results and stop observing. Undo/Redo/load ends the session. Frame changes and rendering stop it before playback/evaluation can be followed. Unregister also keeps results and removes the observer/guards. It creates no parenting, constraints, drivers, keyframes, modifiers or saved distribution linkage.
- Transform settings remain per object. Arrangement settings and named Frames remain scene data. That storage policy was not changed in this release.

## Executed validation
Blender 5.2.3 LTS / Windows.
- Current one-shot grid: **256 Endpoint batches + 140 Offset batches**, all supported bases, both Endpoint paths, selected anchors, unit scales, parents and mirrors.
- Live grid: **96 batches / 192 reference updates**, four point bases, both paths, three anchor configurations, signs, parents and mirrors. An independent transformed-cube-center oracle checks positions, stable order and native data preservation.
- Functional checks: short segments containing overlapping full-size pieces, separate method choices, native labels, selected/unselected Empty sources, cursor changes after selecting a different active object, editable selected anchors, independent linked Frame Location with invalid unused Orientation, manual controls, invalid-source recovery, target edit guard, transverse Offset preservation, unrelated geometry, frame/render stop, persistence and unregister lifecycle.
- A real **1.7.2** source tree produced a Geometry Endpoint file. A fresh 1.7.3 process opened it, showed the migration notice, retained the Offset choice and distributed points in a short segment.
- Real Blender UI: the actual timer followed cursor changes and an Empty moved with Blender's native transform operator while targets were deselected. Native invoke, separate F9 choices and Undo/Redo passed. Panel drawing had no exceptions; screenshots were inspected. This is an automated UI smoke test, not a physical mouse-drag audit.
- Previous checks repeated for 200-piece Offset chains, finite precision/collapse rollback, 21 large-scene scenarios (Geometry Offset and point Endpoint), placement/centroid dependencies, 168 geometric and 72 orientation batches, geometry/spacing caches, 1.7.1 zero-direction/axis/checkbox behavior, and .blend persistence. Current results are in `tests/better_item/results/1.7.3/`.
- Updated existing test entry points to the current contract: retired Geometry Endpoint fit expectations and selection-change cancellation expectations no longer remain as failing requirements. Old version result folders remain historical evidence.

Installer syntax, archive and extension validation, and the functional/Live grid tests against extracted ZIP contents are checked before publication. No installer filenames or versioned ZIP copies were added to addons/.

## Limits
Only Blender 5.2.3 was runtime-tested. Live is one transient scene/view-layer editing session, not animation or a saved relationship. It suspends while the user switches away from the captured scene/view-layer or leaves Object Mode. Independent selection-derived Frames are still required for Live contextual Median/Bounding Box sources. Native float32 precision, constraints and unsupported parent/geometry conditions retain explicit validation. Center of Mass (Volume) still requires the supported nonzero closed-volume conditions; the new names do not introduce physical density/material simulation.
