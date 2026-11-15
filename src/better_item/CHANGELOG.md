# Better Item — changelog

## 1.7.2

### Fixed
- Offset and Endpoint Geometry Bounds verification includes the projected native world-position roundoff budget, including parent/inverse/delta evaluation. Gap checks include both adjacent position budgets.
- Positive collapsed gaps and collapsed occupied-slot advances still reject atomically. Geometry-dependency checks remain independent of the coordinate budget, including symmetric Endpoint bounds changes.
- Geometric spacing inspection accounts for native coordinate roundoff when comparing nonzero gaps, avoiding Mixed immediately after a valid large-scene distribution.

### Performance
- Bounded scalar spacing-inspection cache shared by panel drawing and the live getter. Evaluation updates, load/undo/redo, frame changes and arrangement edits invalidate it; current resolved references, selection, active object, axes and method parameters are in the signature. No cached validation is used when applying distribution.
- Remove the unused native_refs import from distribution.py.

## 1.7.1

### Fixed
- Modern Offset preserves unselected coordinates even in saved scenes with On Reference Axis enabled. That transverse alignment option is no longer displayed.
- Zero Geometry Bounds spacing retains the last entered nonzero direction, persisted in the scene; no Direction selector is added.

### Changed
- Live is a checkbox: enable without moving or overwriting requested spacing; edit controls to update immediately; disable to keep the result. Distribute appears when Live is off.
- Actual spacing inspection remains independent and automatic; the live field reads the measured uniform result without seeding the one-shot requested value.
- Sidebar no longer requires Confirm/Cancel. Existing Python preview operators remain compatible.

## 1.7.0

### Added
- Explicit Offset / Endpoint methods, inherited or overridden Start and independent End sources.
- Between Points segments and Reference Axis projection, with selected endpoint objects preserved.
- Bounds Center, Surface Centroid and Volume Centroid placement alongside Origins and Geometry Bounds.
- Actual spacing inspection and nonpersistent Live Preview with Confirm/Cancel and initial-state replanning.

### Changed
- Context-dependent Frame sources are capture actions; Transform selection-based Location choices capture independent Frames.
- Remove Individual Origins from the visible single-reference choices; retain legacy stored values.
- Make Offset independent of the Location source type. Saved legacy selection-range configurations retain a compatibility path.
- Match native Object Mode Bounding Box Center to selected origins. Reset deleted Frame choices in endpoint references too.
- Keep the stable installer filename and the existing animation-free scope.

## 1.6.3

### Changed
- Show Location before Orientation in shared reference controls and the Frame editor.
- Use the Gimbal icon beside the Orientation label.

## 1.6.2

### Changed
- Add category icons to Orientation and Location labels, with an indented branch for their required Object, Frame or custom-orientation Name.
- Use the same reference hierarchy in Transform, Align and Distribute and the Frame editor; keep child-label icons absent and selector icons native.
- Preserve reference data, transform calculations and the stable installer filename.

## 1.6.1

### Fixed
- Classify arrangement input failures with existing specific support codes; retain the common BI-V001 fallback.
- Document self-following Normal/Gimbal Rotation, Object/Gimbal basis differences and signed distribution ordering with examples.

### Changed
- Remove an unused import and move historical validation narratives out of this changelog into repository documentation.
- Keep the stable `addons/better_item.zip` installer filename. Transform mathematics and panel layout are unchanged.

## 1.6.0

### Added
- Geometry Bounds distribution with signed Spacing and zero-gap packing.
- Match Reference and per-component Set Rotation for the selection.
- Collapsed Solver Settings and separate pending-input, warning and failure diagnostics.

## 1.5.7

### Fixed
- Improve numeric readback, zero-dimension guards, parent diagnostics and transactional affine-stage validation.
- Reject edits whose moving reference prevents the requested absolute relative readout (BI-T009).

Earlier delivery notes and test narratives: [documentation history](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/delivery-history-through-1.6.0.md).
