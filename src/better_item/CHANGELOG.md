# Better Item — changelog

## 1.7.11

Keep spatial operations bound to the correct object when local and linked objects share a name.
- Preserve untouched axes, fixed anchors and atomic refusals across Align and Distribute.
- Keep Live targets, order and New Frame assignment attached to their captured objects.
- Preserve saved references, migration and legacy Python distribution behavior.

## 1.7.10

### Fixed
- Keep observer error/recovery redraws inside the Window RNA guard and skip removed windows before creating a native context override.
- Show the actual spacing-inspection refusal, including invalid Volume geometry, instead of requesting already valid references. Keep the (status, value) tuple contract and cache only display text, never exceptions or RNA wrappers.
- Match native Transform display precision: Location, Rotation and Dimensions use 5; Scale remains 3. Stored values and unit conversion are unchanged.
- Title BI-F006 as Orientation sync paused, preserving its severity, retry policy and other diagnostic titles.

### Validation
- No new feature, saved schema, mathematical tolerance or supported minimum change. Validation results and limitations are recorded in the release report.

## 1.7.9

### Fixed
- Keep native orientation synchronization registered after unexpected failures. Isolate failed Frames/scenes, expose paused export health and retry with bounded backoff without confusing failed reads with deliberate native deletion.
- Clear transient synchronization health on Undo/load/unregister; preserve the existing suspension/recovery behavior for invalid sources.
- Correct the repository homepage version and current report/snapshot links.
- Linked Location, Rotation, Scale and Dimensions edits no longer accumulate float32 read-back error across a drag (a 400-tick Location drag lost about 6e-6 of the ratio), and no longer collapse every linked axis when the dragged value reaches zero, which previously made every later tick fail with BI-T008. While the channels are exactly as the previous linked edit left them, the vector from before the gesture remains the ratio source; any outside change, link change, change of the resolved reference (Frame, orientation, pivot, rotation order) or cache reset discards it.
- Changing Default Euler order or toggling links invalidates the remembered ratio, including a toggle back to the previous link configuration.

### Performance
- Find objects that emit unrealized instances once per evaluated state instead of scanning every instance for each measured object. First Geometry Bounds / Volume inspections were quadratic in selection size.
- In Edit Mode with a Normal source, reuse the per-element selection fingerprint until a depsgraph event, an object-set change or a 2 s safety interval; idle timer ticks no longer walk every vertex, edge and face in Python.

### Documentation
- Clarify that `position_roundoff` returns one object's budget and that a gap sums both endpoints.
- No saved schema, mathematical contract, UI layout or supported minimum changed.

### Maintenance
- Verify installer hash, version, Python fingerprint and exact source inventory during matrix preparation and before each test process. Reject contaminated workspaces without deleting results or profiles.
- Add a release consistency check for metadata, documentation and package/source parity. Version LF checkout rules for the Better Item package.

## 1.7.8

### Performance
- Preserve spacing-inspection entries after transform-only updates to unrelated objects. Entries track numeric target/anchor identities; geometry and unknown updates still invalidate conservatively. Application never reuses display-cache validation.
- Skip the scene-wide selection-normal source scan in Object Mode, preserving native Frame export and selection Normal refresh in Edit Mode.
- Limit node-tree matching to GeometryNodeTree and skip object traversal when vertex/projection caches are empty, while still advancing the geometry revision used by Placement and Live.
- Add a reproducible opt-in cache benchmark and dependency-freshness regressions. No mathematical contracts, persistent schema, UI workflow or supported minimum changed.

## 1.7.7

### Fixed
- Direct Python Endpoint calls honor the requested Placement in either keyword order. Declare Method before its dependent RNA Placement proxy, preserving saved enum IDs, per-method choices, migration and the native invoke/F9 flow.
- Invalid Endpoint Geometry Bounds arguments reject without moving objects instead of silently executing Origins.
- Restore the missing 1.7.4 history and place the changelog title before the version entries.

## 1.7.6

- Lower the manifest minimum to Blender 4.2.0 after testing current Object Mode capabilities on the initial and final 4.2 patches and intermediate release lines.
- No runtime Python or mathematical algorithm changes. Native installer checks cover the lower minimum; historical 1.7.5 evidence remains versioned separately.
- Adapt native-animation cache fixtures to public pre/post Action-slot APIs. This is test maintenance and adds no animation feature.
- Record an independent BMesh feasibility study for a future Edit Mode 2.0. No Edit Mode target UI or mesh editing runtime is added here.

## 1.7.5

- Remove direct Custom Orientation references and the scene-list discovery workaround. No exception-text parsing or search-name cache remains.
- Existing custom-reference selections are explicitly marked removed and require choosing Object or Frame. No target or unrelated native orientation is modified.
- Keep Frame export to native orientations through public Blender operators and native deletion detection.
- Start a portable-build compatibility matrix; exact executed builds and limitations are reported separately.

## 1.7.4

### Changed
- Add a searchable scene Custom Orientation source picker to Transform, Align and Distribute and the Frame editor, preserving existing source names.
- Refresh the disposable index after native creation, renaming and deletion, with informational guidance for missing sources.
- This release used a fragile exception-text discovery workaround. Direct Custom Orientation sources and discovery were removed in 1.7.5; Frame export to native orientations remains supported. See the historical 1.7.4 release report for its finite validation and limitations.

## 1.7.3

### Changed
- Endpoint offers Origins, Bounds Center and Center of Mass (Surface / Volume), distributing points without a geometric-fit requirement. Geometry Bounds is available only for Offset; the retired Endpoint interval solver was removed.
- Each method remembers its own Placement, including F9. Old Endpoint / Geometry files migrate to Origins with a visible notice, preserving Geometry Bounds for Offset.
- Use the native Blender labels Center of Mass (Surface) and Center of Mass (Volume).
- Live observes cursor, object and Frame references during an explicitly enabled editing session. Target selection and Active Object identity are captured; users may select and move reference objects without retargeting distribution. Endpoint order is retained after its first successful update.
- Live updates stop when disabled, on Undo/Redo/load, before frame changes or rendering, and when the add-on is disabled. No animation or permanent constraint is created. Direct target edits pause updates instead of being overwritten.
- Display the captured object count and active identity. Transform references remain stored per object.

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
