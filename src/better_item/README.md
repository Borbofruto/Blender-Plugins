# Better Item 1.5.5

A live Transform panel for Blender 5.0+, tested in Blender 5.2.3 LTS. GPL-3.0-or-later. Author: Gabriel Webber do Nascimento.

## Installation

Download `addons/better_item-1.5.5.zip` from the repository. In Blender use **Edit > Preferences > Add-ons > Install from Disk**, choose that ZIP, enable Better Item, and restart Blender after an update. Open **N > Better Item** in Object Mode. The repository ZIP is not the extension package.

## One live Transform panel

The panel keeps Blender's familiar **Location**, **Rotation**, **Scale** and **Dimensions** names and compact stacked XYZ fields. There are no separate native/incremental panels and no Apply buttons for object transformations. Drag a number or enter a value: the active object updates immediately.

- **Reference > Individual > Orientation** lists Global, Frame, Object, Normal, Gimbal, View, 3D Cursor and Custom Orientation. Default entries use Blender's familiar icons. Custom Orientation... explicitly opens a named source field; enter the existing custom orientation name. There is no capture-from-viewport control.
- **Reference > Individual > Location** lists Global, Frame, Object, Bounding Box Center, 3D Cursor, Individual Origins, Median Point and Active Element. All pivot choices appear directly, with native icons; no nested Pivot selector or Viewport Pivot alias.
- **Location** is the object's world origin expressed in the chosen axes, relative to the chosen origin.
- **Rotation** is the object's orientation relative to the chosen axes. The display supports the six Euler orders, independently of the object's underlying rotation storage mode.
- **Dimensions** is the physical distance between extreme evaluated vertices projected onto each chosen unit direction. It is not the projection of the object's local bounding box. Modifiers are included in the measurement.
- **Scale** (labeled **Scale (Default)** in Reference mode) always shows the object's native Scale. It is read-only when external/reference axes or a non-global origin are selected. In Global axes with Global origin, it remains editable.

Changing axes or origin only changes the readings. It never moves, rotates or resizes the object. Changing only the origin changes Location, without changing Rotation or Dimensions. Dimensions is shown as Unavailable on object types without convertible surface geometry, including Empty, Camera, Light, Armature, Lattice and Grease Pencil; their other transform fields remain usable.

Rotation edits preserve signed native Scale and Delta transforms, and preserve the object origin by default. Enable **Rotate Around Reference Location** to rotate around the selected reference origin instead. A reference that follows the object or selection is intentionally live: its readings may stay at zero while the object moves. No reference is silently frozen.

### Linked components and locks

Each group has independent XYZ chain toggles and a group toggle. Linked edits multiply participating components by the same ratio: (100, 200, 600) becomes (300, 600, 1800) when X is changed to 300. An unlinked axis changes alone. Native locks and drivers are checked; a rejected edit leaves the object unchanged and reports the reason in the panel.

For proportional Rotation, 360 degrees is used only as the denominator when the edited axis starts at exact zero. Other linked axes keep their real values: zero stays zero. Editing Z from 40 to 10 degrees in (0, 0, 40) produces (0, 0, 10), not (90, 90, 10). Entering zero scales other linked angles to zero. The edited angle is retained, including explicit turns. Near-zero angles may still produce large ratios. A zero Location, Scale or Dimension does not define a proportional ratio: unlink that axis first. A geometrically zero dimension cannot be enlarged by scaling.

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

Alignment and distribution use object origins and the same Reference section as Transform. There is no separate Align To dropdown.

- **Location = Bounding Box Center** (including through a frame) exposes Min/Center/Max alignment of selected origins and equal-interval distribution between their fixed extremes. This arrangement mode measures origin bounds in the chosen axes; the ordinary Transform readout still uses Blender's geometry-based bounding-box pivot.
- **Other Location choices** align origins to that reference point, or distribute at signed Spacing from it. A selected source object is kept fixed; Active Element reproduces the former key-object anchor. Use Object to select an explicit key object, independent of the active target.
- The same behavior applies when the Location component comes through one or more frames.

**On Reference Axis**, with exactly one XYZ axis selected and a point reference, places target origins on that reference line. Choose a rotated Object for Orientation and the same Object for Location, or select one Frame for both components.
Targets are arranged along its rotated X axis. With multiple axes, each axis is distributed independently and the line option is disabled. Without the line option, unselected coordinates are preserved.

This is a straight reference-axis arrangement, not a curved-path constraint. It creates no parenting, constraints or ongoing relationship. Moving the reference later does not move the targets. A selected object that supplies the reference origin stays fixed.

Key/reference distribution prioritizes objects on the side opposite the spacing direction, nearest to farthest, followed by objects on the same side, nearest to farthest. Each selected axis is sorted independently. Objects with coincident or insufficiently separated starting coordinates are rejected rather than ordered arbitrarily by name.

Example: key X=-600 mm, other objects at -800, -650 and -590 mm, spacing +30 mm. Order: -650, -800, -590; final positions: -570, -540, -510 mm. Negative spacing reverses direction and side priority.

### Minimum distance and diagnostics

**Minimum Distance (mm)** defaults to **0.00001 mm** and is converted using Scene Unit Scale. Zero spacing and smaller absolute spacing are rejected. Before moving anything, the add-on also checks starting coordinates on every selected reference axis. If two or more objects are coincident or closer than the minimum, the message names the objects and axes and asks for a sufficient offset. Same coordinates on an unselected axis are allowed. The resulting coordinates are checked too: if native float32 precision collapses the spacing, the operation is rolled back with BI-D003, naming the affected objects and axes.

Errors remain visible in the panel with a code and actionable details. Changing settings, a successful operation, or Dismiss clears the message. Typical codes:

| Code | Meaning |
| --- | --- |
| BI-F001 | Circular frame dependency |
| BI-F002 | Missing component source, active object or required selection |
| BI-F003 | Missing native custom orientation |
| BI-F004 | Missing viewport context or failed native orientation operation |
| BI-F005 | Singular reference axes / Gimbal lock |
| BI-A001 | No arrangement axis selected |
| BI-A002 | Missing or invalid orientation/origin reference |
| BI-A003 | Too few selected target objects |
| BI-A004 | Invalid alignment reference or missing selected active key |
| BI-D001 | Zero, too-small or invalid spacing/minimum |
| BI-D002 | Ambiguous starting coordinates; objects and axes are listed |
| BI-D003 | Native precision collapsed the resulting spacing; the operation is rolled back |
| BI-M001 | Multiple owned Dimensions modifiers; resolve the stack explicitly |
| BI-M002 | Owned Dimensions modifier is not last; reorder it explicitly |
| BI-T001 | Object is not editable |
| BI-T002 | An active driver controls the field |
| BI-T003 | A required local Location axis is locked |
| BI-T004 | An active constraint controls the object |
| BI-T005 | Singular parent transform |
| BI-T006 | Evaluated position did not retain the target; residual is reported |
| BI-T007 | Coordinate exceeds the numeric range |

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

