# Better Item 1.6.0

A live Transform panel with declared Blender 5.0+ compatibility. Runtime validation for this release used Blender 5.2.3 LTS on Windows; Blender 5.0 and 5.2.4 were not executed. GPL-3.0-or-later. Author: Gabriel Webber do Nascimento.

## Installation

Download the Better Item extension ZIP from the repository's `addons` directory. In Blender use **Edit > Preferences > Add-ons > Install from Disk**, choose that ZIP and enable Better Item. Open **N > Better Item** in Object Mode. If Blender still has an older module loaded after an update, restart it. The repository ZIP is not the extension package.

## One live Transform panel

The panel keeps Blender's familiar **Location**, **Rotation**, **Scale** and **Dimensions** names and compact stacked XYZ fields. There are no separate native/incremental panels and no Apply buttons for object transformations. Drag a number or enter a value: the active object updates immediately.

- **Reference > Individual > Orientation** lists Global, Frame, Object, Normal, Gimbal, View, 3D Cursor and Custom Orientation. Default entries use Blender's familiar icons. Custom Orientation... explicitly opens a named source field; enter the existing custom orientation name. There is no capture-from-viewport control.
- **Reference > Individual > Location** lists Global, Frame, Object, Bounding Box Center, 3D Cursor, Individual Origins, Median Point and Active Element. All pivot choices appear directly, with native icons; no nested Pivot selector or Viewport Pivot alias.
- **Location** is the object's world origin expressed in the chosen axes, relative to the chosen origin.
- **Rotation** is the object's orientation relative to the chosen axes. The display supports the six Euler orders, independently of the object's underlying rotation storage mode.
- **Dimensions** is the physical distance between extreme evaluated vertices projected onto each chosen unit direction. It is not the projection of the object's local bounding box. Modifiers are included in the measurement.
- **Scale** (labeled **Scale (Default)** in Reference mode) always shows the object's native Scale. It is read-only when external/reference axes or a non-global origin are selected. In Global axes with Global origin, it remains editable.

Changing axes or origin only changes the readings. It never moves, rotates or resizes the object. Changing only the origin changes Location, without changing Rotation or Dimensions. Dimensions is shown as Unavailable on object types without convertible surface geometry, including Empty, Camera, Light, Armature, Lattice and Grease Pencil; their other transform fields remain usable.

Rotation edits preserve signed native Scale and Delta transforms, and preserve the object origin by default. Enable **Rotate Around Reference Location** to rotate around the selected reference origin instead. A reference that follows the object or selection is intentionally live. Numeric Location and Rotation edits must read back as requested within the operation budget. If the reference follows the edit and prevents that result, Better Item rolls back with BI-T009. Apply the relevant component to an independent Frame first; no source is silently frozen. This also covers self-following Gimbal Rotation.

### Linked components and locks

Each group has independent XYZ chain toggles and a group toggle. Linked edits multiply participating components by the same ratio: (100, 200, 600) becomes (300, 600, 1800) when X is changed to 300. An unlinked axis changes alone. Native locks and drivers are checked; a rejected edit leaves the object unchanged and reports the reason in the panel.

For proportional Rotation, 360 degrees is used only as the denominator when the edited axis starts at exact zero. Other linked axes keep their real values: zero stays zero. Editing Z from 40 to 10 degrees in (0, 0, 40) produces (0, 0, 10), not (90, 90, 10). Entering zero scales other linked angles to zero. The edited angle is retained, including explicit turns. Near-zero angles may still produce large ratios. A zero Location, Scale or Dimension does not define a proportional ratio: unlink that axis first. A geometrically zero dimension cannot be enlarged by scaling. Dimensions rejects collapsing a positive width to zero (BI-T010), which would make subsequent dimension edits singular; deliberate collapse remains possible through native Scale.

### Non-destructive Dimensions

When a requested dimension change is representable by native local Scale, Better Item uses it, and the Scale readout updates accordingly. An oblique, nonuniform dimension edit may require a shear that native Scale cannot represent. For Mesh objects the add-on then creates or updates a **Better Item Dimensions** Geometry Nodes modifier containing an affine transform that stores the cumulative geometric correction.

The modifier preserves the base mesh, shared mesh users and shape keys. It does not read the source object or frame, so moving the reference later does not modify the already-edited geometry. Repeated edits update the same final modifier, even if renamed. Before any Reference Dimensions edit, the owned modifier must be unique, enabled and last in the stack. Multiple owned modifiers reject with BI-M001; an owned modifier followed by another rejects with BI-M002. The addon does not reorder, delete, apply or duplicate them automatically. Reading evaluated Dimensions remains available for those stacks. Default / Local edits continue to use the native channels. A copied modifier group is made single-user before editing. In this case native Scale can remain unchanged, which is what the Scale readout correctly shows.

Oblique dimension editing currently requires a Mesh object. A disabled Better Item Dimensions modifier must be enabled before further edits. Parent transforms that cannot represent a rigid requested Rotation are rejected and rolled back. Reflected or singular parent-inverse/bone matrices without an unambiguous channel rotation are rejected rather than guessing their scale signs. Dimensions are scaled about the object's origin.

## Scope: spatial precision

The active extension has no relative-animation schema, keyframe/bake operators, playback controller, legacy-animation warning or automatic migration/removal of animation data and drivers. It does not manage clips from the archived prototype. Existing authoring data is left untouched. The complete 1.5.1 prototype remains separately preserved at `archive/better_item-animation-1.5.1`; evaluating or recovering those files is a separate, manual workflow.

The frame/subframe callback invalidates measurement caches only. Reading current evaluated geometry, including geometry affected by Blender's native systems, is part of accurate measurement; it does not write object poses or animation. The driver guard only inspects native driven channels to prevent overwriting them.

## Default / Local and Reference

**Default / Local** shows Blender's actual Item Location, Rotation, Scale and Dimensions channels. Parent and Parent Inverse are not stripped from a world measurement: the readout accesses the stored channels directly. Moving the parent leaves the child's stored Location/Rotation unchanged. Delta transforms remain separate. Euler rotation uses proportional XYZ links; Quaternion and Axis-Angle expose Blender's native component storage. Default Dimensions edits adjust native Scale and preserve its locks. Code calling `transform_view.values` or `edit_component` for Default Rotation must use an Euler storage mode; Quaternion/Axis-Angle consumers should access the corresponding Blender native property directly.

**Reference** shows and edits the pose using the chosen reference Location and Orientation. Switching between the two changes the readout, not the object's pose. Existing files open in Reference unless the user selects Default / Local. Align/Distribute always uses its shared reference system; raw per-object channels are not a common alignment space.

The old Parent reference shortcut is no longer offered: Object covers explicit parent-object references. Older Parent shortcuts migrate to that actual Object (or Global when no parent exists), without being reinterpreted as Default / Local.

## Transform Information


Failed reference readings are labeled **Unavailable**, with their reason, instead of displaying a fabricated zero vector. Location and Orientation-dependent readings are checked independently; unaffected world/default information remains available.

The read-only section includes reference source paths (including source-object ancestors), World Location, reference origin, actual reference-space Location, Default / Local Location, Delta Location, the effective Parent/Inverse origin, local contribution transformed into world space, evaluation residual, World/default Rotation, parent Scale and optional full matrices.

For local translation `l` including Delta and effective parent matrix `P` (parent world times Parent Inverse), it displays the exact affine accounting:

`world_origin = P.translation + P.linear @ l + evaluation_residual`

The residual exposes changes from constraints or evaluation outside that native parent chain. Rotation and Scale are matrices/quaternions in this accounting, not component-wise sums of Euler angles. With a simple translated parent, the display reduces to the familiar example: parent at Y = 40 plus local Y = 10 gives world Y = 50. With rotation or scale, the transformed local contribution explains the difference.

## Reference Frames

Each scene stores named frames with independent world Location and Orientation. Frame identity survives renaming, saving and undo/redo.

The panel order is **Reference Frames > Transform > Align and Distribute**.

**New Frame** asks only for a name. Configure its two components afterward with exactly the same reference dropdowns as Transform and Align and Distribute, plus Manual for stored frame values:

- **Location:** Manual world coordinates, an Object origin, the default pivots, the Location of another Frame, or Global (the world origin).
- **Orientation:** Manual world rotation, an Object's axes, a default transform orientation, or another Frame.

Each Object choice has its own searchable object picker. To get both components from the same object, choose that object twice. A frame may instead follow Object A's position and Object B's rotation, or use a manual component with a linked component. Existing one-source frames are migrated into separate pointers while preserving their links.

**Apply Location / Apply Orientation** copies the current component and makes it Manual. Applying one component leaves the other link intact. Editing manual values changes the frame, never the source object. Select Manual directly to return to the stored manual values; use Apply to keep the currently resolved values.

### Choosing a reference

Both Transform and Align and Distribute have a **Reference** section:

- **Frame:** select one saved frame to use its Location and Orientation together.
- **Individual:** choose Location and Orientation separately, including a different saved frame for each component. Previously selected individual choices are preserved when switching tabs.

The **+** creates a named frame and selects it in that field. **Use Frame for Active Object** selects both components for Transform and enables Rotate Around Reference Location. Switching references only changes readings and future edits; it never moves the object.

Earlier Match Axes origin choices are resolved during migration into an explicit, independent Location choice. Existing frame serials and saved selections are retained.

Frames, names, manual values, separate object pointers, component chains and consumer selections are saved in the scene inside the .blend. Identity survives renaming and undo/redo. Save/reopen is tested in a fresh Blender process.

### Default pivots and custom orientations

Location lists the five native pivots directly. These follow the current selection. A single frame has one location: **Individual Origins uses the active object's origin**, because several independent origins cannot be represented by one frame. In Mesh Edit Mode, median/bounds/active pivots use selected elements.

Orientation lists native axes directly, except Local, which is intentionally excluded from this reference readout. A Custom Orientation... choice accepts a native custom orientation name by explicit name. Changing the viewport's dropdown later does not change that stored source. In Object Mode, Normal follows the native object's axes, matching Blender. Edit-mode Normal is sampled only when its relevant inputs change. View requires an open 3D Viewport.

Old Local and Viewport orientation shortcuts are migrated to a fixed saved frame at load. Old Viewport Pivot choices become the concrete native pivot selected at migration time. Legacy RNA IDs remain readable for .blend/script compatibility, but these retired shortcuts are not presented in the addon UI.

Click **Use Orientation in Viewport** to create/select a native custom orientation named `BI: <frame name>`. It appears in Blender's regular orientation dropdown and works with native **G**, **R** and axis constraints. Its matrix follows the frame while Better Item is enabled, with a 0.2-second refresh. Frame renaming updates its exported orientation and dependent frames. **Remove Exported Orientation** ends synchronization and deletes that exported entry. Deleting it from Blender's native orientation menu also ends the export at the next refresh: the add-on clears its native name/status and does not recreate it. The scene frame and its Location/Orientation sources remain available; click Use Orientation in Viewport again to export it explicitly.

Another frame can use that exported native orientation as its own source, or link directly through the Frame tab. Removing a frame clears dependent frame choices to Choose a Frame, including other frames that used its components. Only the requested component must be valid. A missing Location source does not prevent exporting a valid Orientation. Circular component chains, including cycles through exported native orientations, are rejected. If an exported orientation becomes invalid, it is removed at the next refresh and restored when repaired; an active removed orientation falls back to Global.

Exported custom orientations contain rotation/directions only. Exporting one does not change Blender's native pivot setting. Better Item's own reference origin and **Rotate Around Reference Location** remain separate controls.

Gimbal axes can be nonorthogonal. Their full basis is retained for native transforms, reference coordinates and projected Dimensions. Euler Rotation fields display/edit the rotational component of that basis. Dimensions normalizes each direction before projection, so a scaled Gimbal direction cannot scale the reported length; Location continues to use coordinates in the original full basis. Applying a nonorthogonal basis stores it without loss; manual Rotation then applies a world-space rotation offset to that stored basis (`offset @ stored_basis`). Singular bases, including Gimbal lock, are rejected with BI-F005.

Transform and Align/Distribute operations have no continuing transform link on targets: moving a source changes readings and future operations, never an already-applied pose. They do not add parenting or Child Of constraints.

Multiple RGB frame indicators can be shown in the viewport. The active frame is larger; visibility is controlled per frame and globally. These arrows are indicators; manual editing uses panel fields.

## Align and Distribute

The panel uses the same independent Location/Orientation or saved Frame reference controls as Transform. Move Axes selects positional axes for alignment/distribution. Rotation components are selected separately inside Set Rotation.

### Position alignment

Alignment > Position retains origin alignment. Bounding Box Center (including through Frames) exposes Min/Center/Max of selected origin coordinates. Other Location references align origins to the reference point. A selected object supplying that point stays fixed.

### Orientation alignment

Alignment > Orientation operates on the selection and preserves each selected world origin and signed native Scale:

- Match Reference matches the full rotational component of the reference axes.
- Set Rotation changes only the enabled reference-space Euler components, in the explicitly chosen Euler order. Disabled components are planned from each object's original rotation before the batch starts.

The known object providing the Orientation reference stays fixed in world orientation/position when selected with the targets. Location does not need to be configured for orientation alignment. Per-object Transform reference settings and numeric hints are not overwritten.

Axes are captured once before a batch; no continuing relationship is created. Selected parents are processed before children and the whole selection rolls back if any required edit fails. Unselected children follow their parents normally. Nonuniform parent transforms may prevent a rigid rotation and cause a diagnostic rejection. Oblique/reflected reference axes use their rotational component, with a contextual note in the panel. This release does not implement angular minimum/maximum/mean or single-vector direction matching.

### Distribution: Origins or Geometry Bounds

Origins preserves the existing signed Spacing behavior. Bounding Box Center distributes origins at equal intervals between fixed origin extremes. Other point/object/frame references use signed steps, keeping the selected Location source fixed. Existing files default to Origins and retain their signed spacing.

Geometry Bounds measures extreme evaluated vertices along the chosen unit reference directions. It uses actual projected minimum/maximum offsets relative to each origin, not just Dimensions divided by two or the object's local box corners. Modifiers and displaced origins are included. Shared meshes, native Scale/Rotation and modifier stacks are left untouched.

- Spacing is signed in both modes. Positive values pack towards positive selected axes; negative values pack towards negative selected axes. In Geometry Bounds, its magnitude is the physical gap. Zero permits touching projected boundaries and always packs towards positive axes. There is no separate Direction control.
- An Object Location reference with supported geometry anchors the first target after that object's corresponding outer boundary plus the spacing magnitude. If selected, the reference remains fixed.
- A point reference (Global, manual Frame, cursor or Empty) anchors the first boundary at that point plus the spacing magnitude.
- Bounding Box Center packs from the original outer selection boundary in the chosen direction. The opposite endpoint is free to move; Geometry Bounds is not the fixed-extremes Origins algorithm.
- Ordering uses original origin projections. Relative to a point/key, objects on the opposite side come first, nearest to farthest, then objects on the direction side, nearest to farthest. Each selected axis is ordered independently.
- On Reference Axis, when exactly one axis is enabled and a point/key reference is used, places origins on that reference line. Otherwise unselected positional information is preserved; for oblique geometry axes, physical projection components are preserved.

For three cubes of side 2, choosing the first cube as the Object Location reference and Spacing = 0 places their origins at 0, 2 and 4 along that axis. Rotated or irregular objects are valid: the guarantee is a gap between projected bounds, not visual contact between arbitrary surfaces or collision-free nesting. Loose vertices count. No mesh cleanup or orientation correction is performed automatically.

Starting origins still need to define an order. Coincident/indistinguishable starts name the objects and axes to separate. Zero spacing does not mean ambiguous initial ordering is accepted. Objects without supported evaluated vertices should use Origins. Unrealized GN instances must be realized first. Geometry or native transforms that change as a function of Location may invalidate a fixed-bound plan; the operation diagnoses and rolls back instead of solving a feedback dependency.

Very large coordinates can make even a mathematically valid gap unrepresentable in Blender float32. Final evaluated boundaries and gaps are verified. An unresolved positive gap, unintended overlap or changed geometry rejects and restores all target locations. Verification tolerances are relative to physical extents; exact real-number contact is not promised.

### Solver Settings and diagnostics

Solver Settings starts collapsed. Minimum Separation (mm), default 0.00001 mm, identifies distinguishable starting coordinates and remains the minimum signed interval in Origins mode. It does not prohibit Geometry Bounds Spacing = 0. It is converted using Scene Unit Scale.

- Setup needed is neutral information: choose an object/frame, select mesh elements, or complete another missing input. Only dependent controls/readouts become unavailable.
- A refused operation is a warning with a reason and a user action, rather than a critical programming error.
- Unexpected API/runtime failures are marked as failures; the technical exception belongs in Details for support.

Support codes and technical details are collapsed by default. The usual message should explain what to do, without requiring Python knowledge. Empty object pointers do not distinguish a never-selected source from a deleted source; both ask for a valid selection rather than inventing a cause.

Python operator callers must check returned CANCELLED status: user-correctable warnings/INFO need not raise RuntimeError. For background EXEC_DEFAULT distribution, pass mode/axes/spacing explicitly; the real UI INVOKE captures panel settings. Orientation operators retain their copied numeric arguments for redo while references are resolved from the current Scene at each execution.

### Support codes (Details)

| Code | Support meaning |
|---|---|
| BI-F001 | Circular frame dependency |
| BI-F002 | Missing component source, active object or required selection |
| BI-F003 | Missing native custom orientation |
| BI-F004 | Missing viewport context or failed native orientation operation |
| BI-F005 | Singular or ill-conditioned reference axes / Gimbal lock |
| BI-A001 | No arrangement axis selected |
| BI-A002 | Missing or invalid orientation/origin reference |
| BI-A003 | Too few selected target objects |
| BI-A004 | Invalid alignment reference or missing selected active key |
| BI-A005 | Orientation reference follows a selected target |
| BI-A006 | Batch orientation or position verification failed |
| BI-D001 | Zero, too-small or invalid spacing/minimum |
| BI-D002 | Ambiguous starting coordinates; objects and axes are listed |
| BI-D003 | Native precision collapsed the resulting spacing; the operation is rolled back |
| BI-G001 | Geometry Bounds requires supported evaluated geometry |
| BI-G002 | The physical gap cannot be retained at native coordinate precision |
| BI-G003 | Evaluated geometry changes during movement |
| BI-G004 | Location reference moves with a distributed target |
| BI-G005 | A native Rotation/Scale depends on Location |
| BI-M001 | Multiple owned Dimensions modifiers; resolve the stack explicitly |
| BI-M002 | Owned Dimensions modifier is not last; reorder it explicitly |
| BI-M003 | Missing ownership data or incompatible affine node graph |
| BI-M004 | Owned Dimensions modifier is disabled |
| BI-M005 | Unrealized Geometry Nodes instances cannot be measured completely |
| BI-T001 | Object is not editable |
| BI-T002 | An active driver controls the field |
| BI-T003 | A required local Location axis is locked |
| BI-T004 | An active constraint controls the object |
| BI-T005 | Singular parent transform |
| BI-T006 | Evaluated position did not retain the target; residual is reported |
| BI-T007 | Coordinate exceeds the numeric range |
| BI-T008 | Proportional denominator is zero or unresolved within Location rounding uncertainty |
| BI-T009 | A moving reference prevents the requested numeric readback |
| BI-T010 | Singular zero/negative Dimensions edit |
| BI-T011 | Rotation unexpectedly changes evaluated Scale |
| BI-T012 | Evaluated Dimensions fails the relative precision check |
| BI-V001 | Other invalid input or unsupported operation; read the accompanying explanation |
| BI-V002 | Blender API rejected a field edit |


### Relative Location zeros and proportional links

Reference Location conversions and the native position solve use double precision before writing Blender's float32 channels. An explicitly requested zero is displayed as exactly zero only after a successful position edit, and only while the evaluated object matrix, resolved origin, resolved axes and native position channels match the verified state. Its raw residual must remain within a magnitude-dependent rounding budget. This records the meaning of an accepted zero; it does not make Blender's stored matrices exact or snap arbitrary small coordinates to zero.

A proportional Location edit rejects a denominator whose magnitude is indistinguishable from zero within that conversion budget, instead of multiplying other axes by an enormous ratio. Unlink the edited axis, set a resolvable nonzero coordinate, then link again. Genuine small coordinates remain measurable and editable when the scene can resolve them. Changing a source, moving the target externally, or switching resolved references invalidates the zero readout hint. Nonzero readouts remain measured, rather than replaced by requested values. No constraints, drivers or animation runtime are created.

When a locked local axis is preserved within the inverse-solve roundoff budget, that accepted error is propagated through the parent linear matrix and included in final world verification. The locked channel remains exactly unchanged; real locked-axis movement and unexpected positioning errors are still rejected.

The position solver assigns absolute local targets, instead of adding a rounded world displacement to the previous position. This fixes cancellation errors that previously rejected ordinary unparented objects near small coordinates. Parenting uses a double-precision solve and float32-aware verification. Its rounding budget retains the separate parent and Parent Inverse terms before cancellation, preventing false BI-T006 errors near zero. Native transforms, unit precision and locks still apply; failed operations restore prior positions. Unselected children follow their parents normally.

## Independent frame components

A frame remains one named item in the list, containing two independent components: Location and Orientation. The same frame may be used only as an origin/pivot, only as axes, or for both. Different frames can supply axes and origin. Set manual or linked sources independently in the frame editor after creating a named frame. Only the component actually used is required and validated: a missing linked Location source does not block a manual Orientation used as axes, and a missing linked Orientation source does not block a manual Location used as a pivot. Arrangement reference choices and mixed frame data persist in the .blend.

## Performance and maintenance

Dimensions reads evaluated vertex coordinates in bulk with Blender's `foreach_get` and projects them with NumPy. The evaluated local geometry and its projected extents have separate bounded caches. Geometry data is discarded when the dependency graph reports a relevant geometry update and on every frame/subframe evaluation. This conservative frame invalidation also covers external animation dependencies that do not emit geometry-update flags. Translation alone reuses the previous extents; rotation and scale reuse local vertices and recompute the projection. Modifiers and shared mesh edits still invalidate affected geometry.

Frame evaluation clears both caches, including past-frame entries, rather than reusing historical geometry after a key edit. This also invalidates static geometry on a frame change; same-frame translations still reuse it.

The geometry cache is limited to eight entries and 64 MiB. Larger meshes are measured without retaining their coordinate array. Projected extents retain at most 32 entries, one current projection per object/context. Load, undo, redo and unregister clear both caches. Frame enum items retain one current list per existing scene, instead of retaining every rename history.

A synthetic benchmark on 250,000 vertices measured the old Python loop at 258-272 ms after each translation. The optimized implementation measured about 12 ms for the first read and 0.03 ms for subsequent translation-only reads. These numbers time Dimensions itself, excluding dependency-graph updates, UI drawing and other scene costs; they are not a whole-viewport performance guarantee. The [repository tests](https://github.com/Borbofruto/Blender-Plugins/tree/main/tests/better_item) include `benchmark_dimensions.py` to measure on another machine.

Version and extension description live only in `blender_manifest.toml`; this is a manifest-based Blender extension, without duplicate legacy `bl_info` metadata. Legacy transformation branches and obsolete staged-edit properties have been removed. Native Scale edits, reference-space Location and reference-space Rotation each have one active implementation.

## Numerical and affine-stage validation

Evaluated vertex storage remains Blender float32; projection and reference affine calculations use float64 to avoid additional cancellation. This cannot recover detail already absent from stored vertices. Dimensions verification has no fixed absolute floor: a positive result must stay within 32 float32 epsilons relative to the requested width. An unrepresentable result rejects and rolls back instead of accepting a large relative loss. World-position verification uses its parent/delta/inverse rounding budget without a blanket absolute tolerance. Native channel writes verify the actual requested float32 representation.

Reference matrices are checked by singular-value ratio, not absolute determinant. Uniform unit rescaling alone cannot invalidate a basis. A reciprocal condition number at or below eight float32 epsilons is rejected (BI-F005).

The affine stage validates node types, operations, required links, selection/offset defaults and matrix metadata before any mutation. Its modifier persistent UID is retained independently of the node-group marker. Missing/corrupted data rejects with BI-M003; it is not rebuilt or silently reordered. Creation, copy-on-write and evaluation failures are transactional. Unrelated user Geometry Nodes groups remain untouched. Unrealized instances reject with BI-M005; add Realize Instances upstream for a complete measurement.

Native Scale and Default/Local edits distinguish driven components: an unrelated driver need not block an independent channel, while edited or unexpectedly changed driven components remain protected. Active constraints are still handled conservatively. The add-on does not add/remove drivers, write keyframes or control playback.

## Validation and source

The 1.6.0 feature contract, release notes and execution evidence are in [the release report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.6.0.md). New feature tests cover 168 geometric combinations, 72 orientation batches (288 targets), hierarchy/dependency/precision rollback, persistence, Undo/Redo and real sidebar/invoke behavior. Earlier numerical regression grids continue below; these are finite matrices, not every possible scene.


The three audits of 1.5.5 are reviewed in [the 1.5.7 report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/feedback-1.5.7.md), with confirmed defects, deliberate policies, unconfirmed claims and the 11-group test matrix.

Executed on Blender 5.2.3 LTS / Windows:

- 9,216 read/edit combinations: 6,240 successful round trips and 2,976 verified atomic rejections for moving references or unsupported parent rotations.
- 192 comparisons with actual native Rotation operators; 54 single-axis Gimbal direction comparisons.
- Object/bone/vertex parenting, collapsed children, negative scales, deep hierarchies, small/large dimensions, 1,000 chained proportional edits and chains up to 100 Frames.
- Same-frame driven shape-key/GN changes, cache freshness, malformed affine groups, fault-injected rollback, unrealized instances, modifier identity, copy-on-write, Undo/Redo and .blend persistence.
- Real UI panel/dialog draws, timer synchronization, native-menu deletion, invalid-source recovery and rename. These are automation/smoke tests, not an exhaustive manual interaction audit.

Existing suites include 1,500 locked-parent cases, 1,200 Parent Inverse cancellations, 842 mm sweep moves, arrangements, reference parity/migration, cache, signed-scale rotation and preservation of retired authoring data.

Tests and machine-readable results are in [the repository](https://github.com/Borbofruto/Blender-Plugins/tree/main/tests/better_item), outside the installable ZIP. Historical delivery records are in CHANGELOG.md. The declared Blender 5.0 minimum is not a runtime-tested compatibility guarantee for every version; only 5.2.3 was available for this delivery.
