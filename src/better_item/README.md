# Better Item 1.4.0

A live Transform panel for Blender 5.0+, tested in Blender 5.2.3 LTS. GPL-3.0-or-later. Author: Gabriel Webber do Nascimento.

## Installation

Download `addons/better_item-1.4.0.zip` from the repository. In Blender use **Edit > Preferences > Add-ons > Install from Disk**, choose that ZIP, enable Better Item, and restart Blender after an update. Open **N > Better Item** in Object Mode. The repository ZIP is not the extension package.

## One live Transform panel

The panel keeps Blender's familiar **Location**, **Rotation**, **Scale** and **Dimensions** names and compact stacked XYZ fields. There are no separate native/incremental panels and no Apply buttons for object transformations. Drag a number or enter a value: the active object updates immediately.

- **Reference > Individual > Orientation** chooses Global, Local, another Object, the current Viewport orientation, or a Saved Frame.
- **Reference > Individual > Location** chooses the world origin, the Viewport Pivot, a Saved Frame origin, another Object origin, or the 3D Cursor.
- **Location** is the object's world origin expressed in the chosen axes, relative to the chosen origin.
- **Rotation** is the object's orientation relative to the chosen axes. The display supports the six Euler orders, independently of the object's underlying rotation storage mode.
- **Dimensions** is the distance between extreme evaluated vertices along each chosen axis. It is not the projection of the object's local bounding box. Modifiers are included in the measurement.
- **Scale** always shows the object's native Scale. It is read-only when external/reference axes or a non-global origin are selected. In Global/Local axes with Global origin, it remains editable.

Changing axes or origin only changes the readings. It never moves, rotates or resizes the object. Changing only the origin changes Location, without changing Rotation or Dimensions.

Rotation edits preserve the object origin by default. Enable **Use Reference Pivot** to rotate around the selected reference origin instead. A reference that follows the object or selection is intentionally live: its readings may stay at zero while the object moves. No reference is silently frozen.

### Linked components and locks

Each group has independent XYZ chain toggles and a group toggle. Linked edits multiply participating components by the same ratio: (100, 200, 600) becomes (300, 600, 1800) when X is changed to 300. An unlinked axis changes alone. Native locks and drivers are checked; a rejected edit leaves the object unchanged and reports the reason in the panel.

For proportional Rotation, exact 0 degrees is treated as 360 degrees. The edited angle is retained, including explicit turns. Near-zero angles may still produce large ratios. A zero Location, Scale or Dimension does not define a proportional ratio: unlink that axis first. A geometrically zero dimension cannot be enlarged by scaling.

### Non-destructive Dimensions

When a requested dimension change is representable by native local Scale, Better Item uses it, and the Scale readout updates accordingly. An oblique, nonuniform dimension edit may require a shear that native Scale cannot represent. For Mesh objects the add-on then creates or updates a **Better Item Dimensions** Geometry Nodes modifier containing a constant affine transform.

The modifier preserves the base mesh, shared mesh users and shape keys. It does not read the source object or frame, so moving the reference later does not modify the already-edited geometry. Repeated edits update the same final modifier. A copied modifier group is made single-user before editing. In this case native Scale can remain unchanged, which is what the Scale readout correctly shows.

Oblique dimension editing currently requires a Mesh object. A disabled Better Item Dimensions modifier must be enabled before further edits. Parent transforms that cannot represent a requested Rotation are rejected and rolled back. Dimensions are scaled about the object's origin.

## Reference Frames

Each scene stores named frames with independent world Location and Orientation. Frame identity survives renaming, saving and undo/redo.

The panel order is **Reference Frames → Transform → Align and Distribute**.

**New Frame** asks only for a name. Configure its two components afterward with compact source tabs:

- **Location:** Manual world coordinates, an Object origin, a native Pivot, or the Location of another Frame.
- **Orientation:** Manual world rotation, an Object's axes, a Native transform orientation, or the Orientation of another Frame.

Each Object tab has its own searchable object picker. To get both components from the same object, choose that object twice. A frame may instead follow Object A's position and Object B's rotation, or use a manual component with a linked component. Existing one-source frames are migrated into separate pointers while preserving their links.

**Apply Location / Apply Orientation** copies the current component and makes it Manual. Applying one component leaves the other link intact. Editing manual values changes the frame, never the source object. Select Manual directly to return to the stored manual values; use Apply to keep the currently resolved values.

### Choosing a reference

Both Transform and Align and Distribute have a **Reference** section:

- **Frame:** select one saved frame to use its Location and Orientation together.
- **Individual:** choose Location and Orientation separately, including a different saved frame for each component. Previously selected individual choices are preserved when switching tabs.

The **+** creates a named frame and selects it in that field. **Use Frame for Active Object** selects both components for Transform and enables Use Reference Pivot. Switching references only changes readings and future edits; it never moves the object.

Frames, names, manual values, separate object pointers, component chains and consumer selections are saved in the scene inside the .blend. Identity survives renaming and undo/redo. Save/reopen is tested in a fresh Blender process.

### Native pivots and orientations

Location's **Pivot** tab offers Bounding Box Center, 3D Cursor, Individual Origins, Median Point and Active Element. These follow the current viewport selection. A single frame has one location: **Individual Origins uses the active object's origin**, because several independent origins cannot be represented by one frame. In Mesh Edit Mode, median/bounds/active pivots use selected elements.

Orientation's **Native** tab can follow Global, Local, Normal, Gimbal, View, Cursor, Parent, or a custom orientation. Choose from the native **Viewport** orientation dropdown, then click **Use Viewport Choice** to link that named orientation to this frame. Changing the viewport's dropdown afterward does not change the stored source selection. Native sources that depend on an object use the current active object. View requires an open 3D Viewport. Normal in Edit Mode requires a selection from which Blender can create an orientation.

Click **Use Orientation in Viewport** to create/select a native custom orientation named `BI: <frame name>`. It appears in Blender's regular orientation dropdown and works with native **G**, **R** and axis constraints. Its matrix follows the frame while Better Item is enabled, with a 0.2-second refresh. Frame renaming updates its exported orientation and dependent frames. **Remove Native Orientation** ends synchronization and deletes that exported entry.

Another frame can use that exported native orientation as its own source, or link directly through the Frame tab. Only the requested component must be valid. A missing Location source does not prevent exporting a valid Orientation. Circular component chains, including cycles through exported native orientations, are rejected. If an exported orientation becomes invalid, it is removed at the next refresh and restored when repaired; an active removed orientation falls back to Global.

Native orientations contain rotation/directions only. Exporting one does not change Blender's native pivot setting. Better Item's own reference origin and **Use Reference Pivot** remain separate controls.

Gimbal axes can be nonorthogonal. Their full basis is retained for native transforms, reference coordinates and projected Dimensions. Euler Rotation fields display/edit the rotational component of that basis. Applying a nonorthogonal basis stores it without loss; manual Rotation then edits a rotation offset on those stored axes. Singular bases, including Gimbal lock, are rejected with BI-F005.

The only live dependency is from sources to frames. There is no parenting, Child Of, constraint or continuing transform link on targets. Moving a source changes readings and future transformations, never the target's previously applied transformation.

Multiple RGB frame indicators can be shown in the viewport. The active frame is larger; visibility is controlled per frame and globally. These arrows are indicators; manual editing uses panel fields.

## Align and Distribute

Alignment and distribution operate on object origins, using one Frame or independent component references:

- **Global**, **Active Local**, a chosen **Object**, a **Saved Frame**, or the current **Viewport** orientation.
- Saved Frame pickers include the same **+** creation shortcut as Transform.
- **Selection Bounds (Origins):** align to Min, Center or Max; distribute between fixed extremes (at least three objects).
- **Key Object (Active):** align to its fixed origin, or distribute at signed Spacing from it. At least two selected objects are required, including the active key.
- **Reference Origin:** align to or distribute from the chosen reference origin. At least one target object is required. The origin can match the orientation object/frame or be selected independently: Global, 3D Cursor, another Object, another Saved Frame, or the Viewport Pivot.

**Reference Origin + On Reference Axis**, with exactly one XYZ axis selected, places all target origins on that reference line, at the entered signed Spacing. For example, choose a rotated object as Axes, Origin = Match Axes, select X, and enable On Reference Axis. Targets are arranged along its rotated X axis. With multiple axes, each axis is distributed independently and the line option is disabled. Without the line option, unselected coordinates are preserved.

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
| BI-T001 | Object is not editable |
| BI-T002 | An active driver controls the field |
| BI-T003 | A required local Location axis is locked |
| BI-T004 | An active constraint controls the object |
| BI-T005 | Singular parent transform |
| BI-T006 | Evaluated position did not retain the target; residual is reported |
| BI-T007 | Coordinate exceeds the numeric range |

The position solver assigns absolute local targets, instead of adding a rounded world displacement to the previous position. This fixes cancellation errors that previously rejected ordinary unparented objects near small coordinates. Parenting uses a double-precision solve and float32-aware verification. Native transforms, unit precision and locks still apply; failed operations restore prior positions. Unselected children follow their parents normally.

## Independent frame components

A frame remains one named item in the list, containing two independent components: Location and Orientation. The same frame may be used only as an origin/pivot, only as axes, or for both. Different frames can supply axes and origin. Set manual or linked sources independently in the frame editor after creating a named frame. Only the component actually used is required and validated: a missing linked Location source does not block a manual Orientation used as axes, and a missing linked Orientation source does not block a manual Location used as a pivot. Arrangement reference choices and mixed frame data persist in the .blend.

## Performance and maintenance

Dimensions reads evaluated vertex coordinates in bulk with Blender's `foreach_get` and projects them with NumPy. The evaluated local geometry and its projected extents have separate bounded caches. Geometry data is discarded only when the dependency graph reports a relevant geometry update. Translation alone reuses the previous extents; rotation and scale reuse local vertices and recompute the projection. Modifiers and shared mesh edits still invalidate affected geometry.

The geometry cache is limited to eight entries and 64 MiB. Larger meshes are measured without retaining their coordinate array. Projected extents retain at most 32 entries, one current projection per object/context. Load, undo, redo and unregister clear both caches. Frame enum items retain one current list per existing scene, instead of retaining every rename history.

A synthetic benchmark on 250,000 vertices measured the old Python loop at 258â€“272 ms after each translation. The optimized implementation measured about 12 ms for the first read and 0.03 ms for subsequent translation-only reads. These numbers time Dimensions itself, excluding dependency-graph updates, UI drawing and other scene costs; they are not a whole-viewport performance guarantee. Run `tests/better_item/benchmark_dimensions.py` to measure on another machine.

Version and extension description live only in `blender_manifest.toml`; this is a manifest-based Blender extension, without duplicate legacy `bl_info` metadata. Legacy transformation branches and obsolete staged-edit properties have been removed. Native Scale edits, reference-space Location and reference-space Rotation each have one active implementation.

## Validation and source

Automated Blender tests also cover vectorized precision, cache reuse, shared geometry and modifier invalidation, memory limits and 2,000 frame renames. They cover live field updates, reference switching without object movement, true vertex extrema, non-destructive oblique Dimensions, shared data isolation, Euler orders, angle turns, proportional links, locks, drivers, alignment/distribution, parenting, saved/live frames, source deletion, renaming, persistence, undo/redo and registration. The actual viewport and panel were also opened and visually inspected. Arrangement regression tests exercise 630 combinations across axis masks, selected/key/reference origins, signed spacing, rotated reference axes, and rotated/scaled parents. They also cover coded validation, reference lines, independent frame components and persistence. Native integration tests execute G/R, compare all Euler/quaternion/axis-angle Gimbal directions with Blender (48 operations), check edit-mode Normal, component/native cycles, invalid-source recovery, old-file migration and new-process persistence.

`arrange.py` plans reference-space arrangements and validates spacing/order; `__init__.py` defines the UI and properties; `transform_view.py` implements live readings and edits; `frames.py` owns independent saved frame components and viewport indicators; `native_refs.py` resolves native pivots/orientations and synchronizes native custom orientations; `engine.py` implements native Scale edits and transactional world positioning; `math_core.py` holds Blender-independent rules; `orientation.py` provides orientation utilities.

