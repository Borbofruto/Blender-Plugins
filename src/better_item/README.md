# Better Item 1.7.11

A live Transform panel with declared Blender 4.2+ compatibility. Executed builds, test coverage and remaining limits are recorded in the [compatibility report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/compatibility-1.7.6.md). GPL-3.0-or-later. Author: Gabriel Webber do Nascimento.

1.7.7 fixes direct Python Endpoint Placement arguments and repairs the changelog. Current execution results, including the new operator regression, are recorded separately in the [1.7.7 maintenance report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.7.md). The compatibility report above preserves the provenance of the earlier 1.7.6 matrix.

1.7.8 retains spacing inspection results across unrelated transform-only object updates, avoids Object Mode selection-normal source scans, and narrows geometry-tree invalidation work. Geometry updates and unclassified events still invalidate conservatively; applying an operation always plans and validates independently. Measured before/after results and remaining costs are recorded in the [cache maintenance report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.8.md).

1.7.9 keeps the native orientation observer alive after unexpected failures, isolates failed Frames and retries with bounded backoff. A paused export shows BI-F006 instead of appearing healthy while its axes are outdated. Explicit native deletion is still respected; transient health is cleared on Undo/load/unregister. Release and runner integrity checks are documented in the [1.7.9 maintenance report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.9.md).
1.7.9 keeps linked Location, Rotation, Scale and Dimensions edits exact across a continuous drag, including through zero; removes a quadratic scan from the first (cold) spacing inspection; and stops re-walking every selected element in Edit Mode on each Normal-orientation refresh. No mathematical contract, saved schema, UI workflow or supported minimum changed. Measurements and limits are in the [1.7.9 report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.9.md).

## Installation

Download the Better Item extension ZIP from the repository's `addons` directory. In Blender use **Edit > Preferences > Add-ons > Install from Disk**, choose that ZIP and enable Better Item. Open **N > Better Item** in Object Mode. If Blender still has an older module loaded after an update, restart it. The repository ZIP is not the extension package.

## One live Transform panel

The panel keeps Blender's familiar **Location**, **Rotation**, **Scale** and **Dimensions** names and compact stacked XYZ fields. There are no separate native/incremental panels and no Apply buttons for object transformations. Drag a number or enter a value: the active object updates immediately.

- **Reference > Individual > Orientation** lists Global, Frame, Object, Normal, Gimbal, View and 3D Cursor. Default entries use Blender icons. Direct native Custom Orientation references were removed in 1.7.5: no scene-list discovery or exception-text parsing remains. Named Frames and Object sources provide reusable orientations.
- **Reference > Individual > Location** offers Global, Frame, Object and 3D Cursor. Selection-based Location choices in Transform are explicit Capture actions: they create an independent saved Frame. Alignment/distribution can capture selection context at operation start. Individual Origins is no longer offered as a single reference point.
- **Location** is the object's world origin expressed in the chosen axes, relative to the chosen origin.
- **Rotation** is the object's orientation relative to the chosen axes. The display supports the six Euler orders, independently of the object's underlying rotation storage mode.
- **Dimensions** is the physical distance between extreme evaluated vertices projected onto each chosen unit direction. It is not the projection of the object's local bounding box. Modifiers are included in the measurement.
- **Scale** (labeled **Scale (Default)** in Reference mode) always shows the object's native Scale. It is read-only when external/reference axes or a non-global origin are selected. In Global axes with Global origin, it remains editable.

Choosing a normal linked/manual source changes only the readings. A Capture choice stores its current result independently. Changing axes or origin only changes the readings. It never moves, rotates or resizes the object. Changing only the origin changes Location, without changing Rotation or Dimensions. Dimensions is shown as Unavailable on object types without convertible surface geometry, including Empty, Camera, Light, Armature, Lattice and Grease Pencil; their other transform fields remain usable.

Reference choices appear in Location, then Orientation order, including in the Frame editor. Location uses the origin icon and Orientation uses the Gimbal icon beside its label. A required Object, Frame or custom-orientation Name is shown one level below its parent choice, with an indented branch marker. Those child labels have no category icon; source icons remain inside their selector widgets. This hierarchy is shared by Transform, Align and Distribute and the Frame editor.

Rotation edits preserve signed native Scale and Delta transforms, and preserve the object origin by default. Enable **Rotate Around Reference Location** to rotate around the selected reference origin instead. A reference that follows the object or selection is intentionally live. Numeric Location and Rotation edits must read back as requested within the operation budget. If the reference follows the edit and prevents that result, Better Item rolls back with BI-T009. Apply the relevant component to an independent Frame first; no source is silently frozen.

In Object Mode, Normal follows the active object's axes; when that object is also the target, a nonzero relative Rotation generally cannot remain the absolute value entered. Euler Gimbal can also follow the edit, but some components remain editable. An unparented quaternion object's Gimbal basis is stationary world axes, and Rotation edits remain supported. The panel therefore does not disable every Normal/Gimbal field based only on its name. It keeps the readback/rollback guard. To edit against a stable snapshot, create a Frame with the required Orientation source and use Apply Orientation to make that component Manual before selecting it as the reference. These fields set absolute relative angles, not incremental rotation commands. Gimbal does not remove Gimbal lock; singular bases remain unavailable.

### Linked components and locks

Each group has independent XYZ chain toggles and a group toggle. Linked edits multiply participating components by the same ratio: (100, 200, 600) becomes (300, 600, 1800) when X is changed to 300. An unlinked axis changes alone. Native locks and drivers are checked; a rejected edit leaves the object unchanged and reports the reason in the panel.

For proportional Rotation, 360 degrees is used only as the denominator when the edited axis starts at exact zero. Other linked axes keep their real values: zero stays zero. Editing Z from 40 to 10 degrees in (0, 0, 40) produces (0, 0, 10), not (90, 90, 10). Entering zero scales other linked angles to zero. The edited angle is retained, including explicit turns. Near-zero angles may still produce large ratios. A zero Location, Scale or Dimension does not define a proportional ratio: unlink that axis first. A geometrically zero dimension cannot be enlarged by scaling. Dimensions rejects collapsing a positive width to zero (BI-T010), which would make subsequent dimension edits singular; deliberate collapse remains possible through native Scale.

### Non-destructive Dimensions

When a requested dimension change is representable by native local Scale, Better Item uses it, and the Scale readout updates accordingly. An oblique, nonuniform dimension edit may require a shear that native Scale cannot represent. For Mesh objects the add-on then creates or updates a **Better Item Dimensions** Geometry Nodes modifier containing an affine transform that stores the cumulative geometric correction.

The modifier preserves the base mesh, shared mesh users and shape keys. It does not read the source object or frame, so moving the reference later does not modify the already-edited geometry. Repeated edits update the same final modifier, even if renamed. Before any Reference Dimensions edit, the owned modifier must be unique, enabled and last in the stack. Multiple owned modifiers reject with BI-M001; an owned modifier followed by another rejects with BI-M002. The addon does not reorder, delete, apply or duplicate them automatically. Reading evaluated Dimensions remains available for those stacks. Default / Local edits continue to use the native channels. A copied modifier group is made single-user before editing. In this case native Scale can remain unchanged, which is what the Scale readout correctly shows.

Oblique dimension editing currently requires a Mesh object. A disabled Better Item Dimensions modifier must be enabled before further edits. Parent transforms that cannot represent a rigid requested Rotation are rejected and rolled back. Reflected or singular parent-inverse/bone matrices without an unambiguous channel rotation are rejected rather than guessing their scale signs. Dimensions are scaled about the object's origin.

## Scope: spatial precision

The active extension has no relative-animation schema, keyframe/bake operators, playback controller, legacy-animation warning or automatic migration/removal of animation data and drivers. It does not manage clips from the archived prototype. Existing authoring data is left untouched. The complete 1.5.1 prototype remains separately preserved at `archive/better_item-animation-1.5.1`; evaluating or recovering those files is a separate, manual workflow.

Measurement frame/subframe callbacks invalidate caches. A separate guard ends a transient Live session before frame changes or rendering; it does not apply distribution during playback. Reading current evaluated geometry, including geometry affected by Blender's native systems, is part of accurate measurement; it does not write object poses or animation. The driver guard only inspects native driven channels to prevent overwriting them.

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

Frame Location offers stable Manual, Global, Object, Frame and 3D Cursor sources. Selection-dependent Median Point, Bounding Box Center and Active Element are Capture actions that store a Manual point. In Mesh Edit Mode those actions capture selected elements. Individual Origins is not offered as a single frame Location; legacy sources can be applied manually.

Transform/Arrangement Orientation lists native axes directly, except Local, which is intentionally excluded from this reference readout. In the Frame editor, Normal/Gimbal/View choices are Capture actions rather than continuing context links. In Object Mode, Normal follows the native object's axes, matching Blender. Edit-mode Normal is sampled only when its relevant inputs change. View requires an open 3D Viewport.

Old Local and Viewport orientation shortcuts are migrated to a fixed saved frame at load. Old Viewport Pivot choices become the concrete native pivot selected at migration time. Legacy RNA IDs remain readable for .blend/script compatibility, but these retired shortcuts are not presented in the addon UI.

Click **Use Orientation in Viewport** to create/select a native custom orientation named `BI: <frame name>`. It appears in Blender's regular orientation dropdown and works with native **G**, **R** and axis constraints. Its matrix follows the frame while Better Item is enabled, with a 0.2-second refresh. Frame renaming updates its exported orientation and dependent frames. **Remove Exported Orientation** ends synchronization and deletes that exported entry. Deleting it from Blender's native orientation menu also ends the export at the next refresh: the add-on clears its native name/status and does not recreate it. The scene frame and its Location/Orientation sources remain available; click Use Orientation in Viewport again to export it explicitly.

Another frame can use that exported native orientation as its own source, or link directly through the Frame tab. Removing a frame clears dependent frame choices to Choose a Frame, including other frames that used its components. Only the requested component must be valid. A missing Location source does not prevent exporting a valid Orientation. Circular component chains, including cycles through exported native orientations, are rejected. If an exported orientation becomes invalid, it is removed at the next refresh and restored when repaired; an active removed orientation falls back to Global.

Exported custom orientations contain rotation/directions only. Exporting one does not change Blender's native pivot setting. Better Item's own reference origin and **Rotate Around Reference Location** remain separate controls.

Gimbal axes can be nonorthogonal. Their full basis is retained for native transforms, reference coordinates and projected Dimensions. Euler Rotation fields display/edit the rotational component of that basis. Dimensions normalizes each direction before projection, so a scaled Gimbal direction cannot scale the reported length; Location continues to use coordinates in the original full basis. Applying a nonorthogonal basis stores it without loss; manual Rotation then applies a world-space rotation offset to that stored basis (`offset @ stored_basis`). Singular bases, including Gimbal lock, are rejected with BI-F005.

Object Orientation resolves a proper orthonormal rotational basis, with signed-scale handling; it does not expose inherited shear or axis lengths as reference coordinates. Gimbal instead reproduces the native storage-dependent axis construction and can retain oblique axes under nonuniform parent transforms. These sources are not interchangeable in a sheared hierarchy. Manual Frames can also retain a full stored basis. Location uses that basis, Dimensions projects onto its unit directions, and Rotation uses its rotational component as described above.

Transform and Align/Distribute operations have no continuing transform link on targets: moving a source changes readings and future operations, never an already-applied pose. They do not add parenting or Child Of constraints.

Multiple RGB frame indicators can be shown in the viewport. The active frame is larger; visibility is controlled per frame and globally. These arrows are indicators; manual editing uses panel fields.

## Align and Distribute

The panel retains Location before Orientation, with indented source fields. Alignment and Offset use the shared references. Endpoint / Between Points uses the inherited Location only as Start, or an explicitly overridden Start; it does not consume the shared Orientation or Move axes.

### Position and orientation alignment

Position alignment uses origins. Selection-derived Bounds exposes Min/Center/Max; other references align to their point and keep a selected known source fixed. Match Reference / Set Rotation retains the six Euler orders, selected component masks, signed native Scale and selected world positions. Parents are processed first and unsupported rigid rotations reject atomically. Distribution changes neither per-object Transform reference settings nor source mesh data.

### Distribution method

- **Offset:** signed Spacing in the shared reference axes. Positive goes positive; negative goes negative. No Direction selector. Choose one axis or multiple independent axes. Unselected reference coordinates are preserved. Offset does not also align objects onto a reference line; the old On Reference Axis setting is ignored by this method. In Geometry Bounds, zero retains the last nonzero spacing direction (positive only if no direction has been entered yet). This direction is saved with the scene.
- **Endpoint / Between Points:** Start and End define a 3D segment and its direction. No external Orientation is required. Start uses shared Location by default; Override Start gives it a separate Location source.
- **Endpoint / Reference Axis:** projects End onto exactly one Move axis through Start. This explicitly uses the shared Orientation. An endpoint object can be off that line; its position is used as an axial limit, and it is not moved.

Start/End accept world XYZ Manual coordinates, Global, a chosen Object, saved Frame Location, 3D Cursor or the operation's Active Object. A Frame's unused Orientation may be missing without blocking its valid Location. End does not acquire an Orientation of its own.

### Placement basis

| Basis | Contract |
|---|---|
| Origins | Use the existing native origin point. |
| Bounds Center | Use the center of evaluated world-axis-aligned geometric bounds; do not change the native origin. |
| Center of Mass (Surface) | Area-weighted center of the evaluated triangulated surface, including world deformation. Loose vertices have no surface weight. |
| Center of Mass (Volume) | Uniform-density signed-volume centroid. Requires a nonzero closed volume with consistent triangle orientation. The check rejects open/nonmanifold edge incidence and inconsistent winding, but does not certify absence of self-intersections or physical validity of nested shells. |
| Geometry Bounds | Use evaluated occupied intervals projected along the distribution direction(s), so physical gaps are equal rather than point intervals. Loose vertices count. |

Offset supports all five bases. Endpoint supports only the four point bases: Origins, Bounds Center and Center of Mass (Surface / Volume). It places the first and last points at the effective limits and spaces the other points evenly. Pieces may overlap; there is no geometric-fit requirement and nothing is resized or rotated. Geometry Bounds is available only for Offset, measuring physical gaps instead of point intervals. Each method remembers its own Placement choice, including in F9.

Example: five two-unit cubes can be distributed by Origins inside a half-unit segment. Their origin points are evenly spaced from 0 to 0.5; their geometry overlaps and retains its native size. Geometry Bounds cannot be chosen for Endpoint. An older saved Endpoint / Geometry selection migrates to Origins with a setup notice, while its Geometry Bounds choice is retained for Offset. Choosing Placement explicitly clears the notice.

### Endpoint anchors and ordering

A known endpoint source object selected with the targets is fixed and occupies its first/last point slot. With a geometric point basis, that selected anchor's corresponding geometric point becomes the effective segment endpoint. The distributor does not move anchor objects; users may move them as live spatial inputs. Offset origins and native anchor transforms are preserved.

Empty/Camera and other non-geometric source objects remain valid fixed point anchors. A selected non-anchor without the geometry required by the chosen basis is rejected. At least two placement slots are required; selecting only two fixed endpoint objects leaves no target to arrange.

Offset preserves the requested ordering rule: opposite half-space first, then nearest to farthest within each half-space. Endpoint has no pre-existing axis and orders by the opposite half-space of Start→End, then **spatial distance from Start**. This permits objects initially lying in a plane perpendicular to a new segment. Indistinguishable distances within a half-space name the conflicting objects and require separation; names are not silently used to invent a meaningful order.

### Current spacing and Live Preview

Offset inspection includes the anchor-to-first interval, the selected axes and the selected placement basis. A uniform selection displays its measured spacing. Mixed spacing is a normal state and is never represented as a fabricated zero or average. With Live off, Spacing is an explicit requested value and Distribute applies it. With Live on, the editable Spacing field reads back the current uniform result. Current is measured automatically in both modes; enabling Live does not overwrite the requested spacing. Endpoint point intervals are derived from its references and are read-only. There is no independent distance slider; its spatial sources are the controls.

The **Live** checkbox captures the selected input objects and the identity of the active object without moving them. The first control/reference edit applies a distribution. Later edits replan from the initial native locations; Endpoint retains the object order established by its first successful update for that method/basis/path/axis configuration. Switching a configuration can establish its own order. Live remembers these object identities even when they are renamed.

While enabled, a lightweight 0.1-second editing observer detects changes to cursor, Manual coordinates, object references, Frame components and relevant orientation/geometry. Select an Empty and move it normally: the original captured targets continue to update, without changing Blender's actual selection. Active Object / Active Element references use the object captured at enable time, rather than whichever object was most recently selected. Selected endpoint objects are editable sources too; distribution does not restore them to their old locations.

The sidebar shows the captured object count and active name. Its spacing inspection uses those captured objects even if none of them remain selected. Alignment continues to operate on the actual current selection. Changing the target set requires disabling Live, selecting new inputs, and enabling it again. Direct external changes to a moving target's Location/Rotation/Scale pause updates with an informational message instead of overwriting the user's edit. Missing/invalid sources retain the last valid poses and can recover after the source is fixed. Unrelated geometry updates do not normalize a previously untouched selection.

Unchecking Live keeps current poses and stops the observer. There are no Confirm/Cancel buttons in the sidebar. Disabling the add-on also keeps the result. Undo/Redo or loading another file ends the session; changing frame or starting a render stops it before any evaluated animation can be followed. Live is an editing session, not a saved linkage or animation system: it creates no parenting, constraints, drivers, keyframes or geometry modifiers. Reopening a saved file retains ordinary object poses and references, not an ongoing Live session. Only one scene/view-layer session may be active; switching scenes/view-layers suspends polling until the captured context is active again.

Selection-dependent Median/Bounding Box starts must first be captured into an independent Frame for Live; a one-shot operation can still use their initial context. Legacy selection-dependent Frame sources should likewise be applied to independent components before use.

The one-shot operator remains REGISTER/UNDO and supports Blender's Adjust Last Operation (F9) for copied method, path, basis, axes and spacing parameters. Source choices are scene settings. Existing Python preview BEGIN/CONFIRM/CANCEL actions remain supported for compatibility, while the sidebar uses the Live checkbox.

### Reference context and compatibility

Individual Origins is removed from visible single-point selectors; legacy stored IDs remain readable. Frame selection-dependent Location choices and Normal/Gimbal/View Orientation choices are labelled **Capture** and store independent Manual values. Explicit Object/Frame links remain live pointers. Old files may retain a legacy contextual Frame source, marked in the editor with Apply available to capture it; no arbitrary replacement source is invented.

Bounding Box Center in Object Mode now matches Blender's origin-based pivot. It differs from Bounds Center placement, which measures each object's evaluated geometry. Context-derived selection points in new Transform choices are captures into independent Frames; they are not continuous self-following editing references.

New Offset operations never switch solvers just because Location is Bounding Box Center. Saved pre-1.7 selection-range configurations retain a marked compatibility path for the old Distribute operation; switch Method to choose the new explicit behavior. Live Preview is unavailable for that legacy range until switched. An explicit shared-source choice also exits that legacy range. The old Python operator SELECTION/KEY/REFERENCE paths remain supported.

### Solver and diagnostics

Solver Settings remains collapsed. Minimum Separation (mm) distinguishes starting positions/distances and valid endpoint lengths, and remains the minimum nonzero Offset point interval. Geometry Bounds allows a zero Offset gap. Units use Scene Unit Scale. Native coordinates remain float32; inverse solves and geometry integration use double precision. Position checks propagate the existing parent/native rounding budget, including cancellation around offset origins. Endpoint point placement uses the native world-position rounding budget. Offset interval checks also use relative float32 tolerances without a fixed arbitrary scene-unit floor. Positive gaps that collapse to zero and Offset point intervals that cannot retain the requested spacing are rejected.

Unsupported geometry, moving endpoint dependencies, native locks/drivers/constraints and unrepresentable fits reject atomically. Setup needed is neutral, a refused operation is a warning, and unexpected failures have technical Details. These are finite precision guarantees, not a collision solver or a proof that arbitrary meshes are valid solids.

### Support codes (Details)

| Code | Support meaning |
|---|---|
| BI-F001 | Circular frame dependency |
| BI-F002 | Missing component source, active object or required selection |
| BI-F003 | Retired custom-orientation reference: choose Object or Frame |
| BI-F004 | Missing viewport context or failed native orientation operation |
| BI-F005 | Singular or ill-conditioned reference axes / Gimbal lock |
| BI-F006 | Native orientation synchronization paused after an unexpected failure; automatic retry pending |
| BI-A001 | No arrangement axis selected |
| BI-A002 | Missing or invalid orientation/origin reference |
| BI-A003 | Too few selected target objects |
| BI-A004 | Invalid alignment reference or missing selected active key |
| BI-A005 | Orientation reference follows a selected target |
| BI-A006 | Batch orientation or position verification failed |
| BI-D001 | Zero, too-small or invalid spacing/minimum |
| BI-D002 | Ambiguous starting coordinates; objects and axes are listed |
| BI-D003 | Native precision collapsed the resulting spacing; the operation is rolled back |
| BI-E001 | Missing, coincident, reversed or invalid endpoint limits/path |
| BI-E002 | Geometry Bounds is only available for Offset; choose a point basis for Endpoint |
| BI-E003 | Endpoint point placement failed native precision verification or distinct points collapsed |
| BI-P001 | Placement basis requires supported geometry |
| BI-P002 | Unresolved/zero surface area or centroid |
| BI-P003 | Invalid/open/inconsistently oriented or zero volume |
| BI-L001 | Live needs capture/restart, a captured target changed/was removed, or the session ended |
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
| BI-T008 | Proportional denominator is zero or unresolved within Location rounding uncertainty. A linked edit that continues the previous edit of the same channels keeps its original ratio and is not refused when it passes through zero |
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

Version 1.7.0 adds 320 Endpoint batches and 140 Offset batches across placement bases, endpoint paths, fixed anchors, mirrors, parents and unit scales; contract, dependency, centroid cache, source removal, persistence and native preview undo tests; and a real-sidebar preview test. See [the 1.7.0 report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.0.md) for execution results and limits. Historical tests below are separately identified.

The [1.6.1 review](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/review-1.6.1.md) separates confirmed maintenance issues from deliberate behavior and unverified claims. Historical validation paragraphs removed from CHANGELOG are preserved in the repository's documentation history. The installer remains `addons/better_item.zip`; its filename is stable across updates.

The 1.6.0 feature contract, release notes and execution evidence are in [the release report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.6.0.md). New feature tests cover 168 geometric combinations, 72 orientation batches (288 targets), hierarchy/dependency/precision rollback, persistence, Undo/Redo and real sidebar/invoke behavior. Earlier numerical regression grids continue below; these are finite matrices, not every possible scene.


The three audits of 1.5.5 are reviewed in [the 1.5.7 report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/feedback-1.5.7.md), with confirmed defects, deliberate policies, unconfirmed claims and the 11-group test matrix.

Executed on Blender 5.2.3 LTS / Windows:

- 9,216 read/edit combinations: 6,240 successful round trips and 2,976 verified atomic rejections for moving references or unsupported parent rotations.
- 192 comparisons with actual native Rotation operators; 54 single-axis Gimbal direction comparisons.
- Object/bone/vertex parenting, collapsed children, negative scales, deep hierarchies, small/large dimensions, 1,000 chained proportional edits and chains up to 100 Frames.
- Same-frame driven shape-key/GN changes, cache freshness, malformed affine groups, fault-injected rollback, unrealized instances, modifier identity, copy-on-write, Undo/Redo and .blend persistence.
- Real UI panel/dialog draws, timer synchronization, native-menu deletion, invalid-source recovery and rename. These are automation/smoke tests, not an exhaustive manual interaction audit.

Existing suites include 1,500 locked-parent cases, 1,200 Parent Inverse cancellations, 842 mm sweep moves, arrangements, reference parity/migration, cache, signed-scale rotation and preservation of retired authoring data.

Tests and machine-readable results are in [the repository](https://github.com/Borbofruto/Blender-Plugins/tree/main/tests/better_item), outside the installable ZIP. Historical delivery records are in CHANGELOG.md. The declared Blender 4.2 minimum does not imply support for every scene or future Blender release. Consult the compatibility report for exact builds and executed coverage.

1.7.1 corrects transverse Offset movement and zero-spacing direction, and replaces the sidebar preview transaction buttons with a Live checkbox. See the [1.7.1 correction report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.1.md).

### 1.7.2 precision and inspection corrections

Geometry Bounds verification includes the native world-position roundoff budget projected onto the measured direction. Adjacent gap checks include both positions. This permits normal float32 rounding in long chains and translated deployment scenes; it does not promise exact real-number contact or recover geometry/spacing below storage resolution. A requested positive gap that collapses, or a positive occupied-slot advance that collapses, still rejects and restores poses. Position-dependent geometry is checked separately; coordinate tolerance does not permit shape changes.

Current spacing uses a bounded scalar-result cache shared by the panel and Live getter. Changed selection/active object, resolved references, method parameters and evaluated scene updates invalidate or change the signature. Loading, Undo/Redo and frame changes clear it. The first measurement after invalidation still evaluates geometry; redraws reuse the result. Application always plans and validates independently of this display cache.

See the [1.7.2 correction report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.2.md) for before/after cases, large-selection timings and runtime evidence. No features or animation support were added.

The [1.7.3 report](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.3.md) records the current point-only Endpoint contract, independent Placement choices, reference-driven Live behavior, migration and finite validation. Earlier reports describe historical behavior; the retired Endpoint geometric-fit solver is no longer offered. Transform settings remain per object, while arrangement settings and Frames belong to the scene.

## Removed custom-orientation references

The 1.7.4 scene-discovery workaround and the Custom Orientation input were removed in 1.7.5. Existing files retain their saved source without modifying targets, but show Custom Orientation (Removed) and INFO setup guidance until the user selects Object, Frame or a supported default orientation. The retired choice is never offered for new references. Frame export to a native Blender orientation remains available for G/R through public operators, including native deletion detection. No exception message is parsed and no native orientation is deleted merely because a saved reference was retired. Historical release reports and the 1.7.3 handoff document describe their respective versions.

## Blender 4.2 baseline and future Edit Mode

The 1.7.6 minimum is Blender 4.2.0. The extension runtime Python is unchanged from 1.7.5; support expansion is backed by actual portable-build tests, native ZIP installation and an upward 4.2.0-to-5.3 file migration fixture. See the compatibility report for exact builds, artifacts and limitations. The separate [Edit Mode feasibility study](https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/edit-mode-2.0-feasibility.md) establishes public BMesh foundations for a future 2.0; Edit Mode targets are not implemented in this installer.
