# Better Item 1.2.0

A live Transform panel for Blender 5.0+, tested in Blender 5.2.3 LTS. GPL-3.0-or-later. Author: Gabriel Webber do Nascimento.

## Installation

Download `addons/better_item-1.2.0.zip` from the repository. In Blender use **Edit > Preferences > Add-ons > Install from Disk**, choose that ZIP, enable Better Item, and restart Blender after an update. Open **N > Better Item** in Object Mode. The repository ZIP is not the extension package.

## One live Transform panel

The panel keeps Blender's familiar **Location**, **Rotation**, **Scale** and **Dimensions** names and compact stacked XYZ fields. There are no separate native/incremental panels and no Apply buttons for object transformations. Drag a number or enter a value: the active object updates immediately.

- **Axes** chooses Global, Local, another Object, the current Viewport orientation, or a Saved Frame.
- **Origin** chooses the world origin, the Viewport Pivot, a Saved Frame origin, another Object origin, or the 3D Cursor.
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

- **Create from Viewport** captures the current transform orientation and pivot. Median and bounds pivots use the full selection; Individual Origins captures the active object's origin.
- **Create from Object (Applied)** copies the active object's world position and orientation without a persistent link.
- **Create Linked to Object** uses its transform as a live source. Location and Orientation links are independent.
- **Create Manual** starts a frame at the world origin with zero rotation.

Edit **Source Object** to select a source. Selecting a source without enabling links does not copy it. **Apply Location**, **Apply Orientation**, or **Apply Reference** stores the current component values and ends the respective links. Unlinking also preserves the current values. Applied components can be edited manually. After both components are applied, the source pointer is released and the original object can be deleted safely.

**Use for Active Object** selects the frame's axes and origin for the target and enables its reference pivot. Axes and origin can subsequently be selected independently.

The only live link is between a source and a frame. There is no parenting, Child Of, constraint or continuing transform link on the target. Moving the source changes the readout, but never moves the target again. A missing source is reported rather than silently substituted.

Multiple RGB frame indicators can be displayed in the viewport. The active frame is larger. Visibility is controlled per frame and globally. These arrows are indicators; manual frame editing uses the panel fields.

Viewport capture supports Global, Local, Normal in Object Mode, Parent, Cursor, View and custom orthogonal orientations. View requires a 3D viewport. Gimbal is rejected because its axes may be nonorthogonal.

## Align and Distribute

All alignment and distribution is based on object origins along global XYZ axes.

- **Selection Bounds (Origins):** align to Min, Center or Max; distribute at equal intervals between fixed extremes (at least three objects).
- **Key Object (Active):** align to its fixed origin, or distribute with signed Spacing from it. At least two objects are required.

Key distribution prioritizes objects on the side opposite the spacing direction, nearest to farthest, followed by objects on the same side, nearest to farthest. Name breaks ties. Each selected axis is sorted independently.

Example: key X=-600 mm, other objects at -800, -650 and -590 mm, spacing +30 mm. Order: -650, -800, -590; final positions: -570, -540, -510 mm. Negative spacing reverses direction and side priority. Zero spacing places all origins on the key along the selected axes.

Parenting is resolved in world coordinates. Failed operations roll back preceding moves. Unselected children follow their parents normally.

## Validation and source

Automated Blender tests cover live field updates, reference switching without object movement, true vertex extrema, non-destructive oblique Dimensions, shared data isolation, Euler orders, angle turns, proportional links, locks, drivers, alignment/distribution, parenting, saved/live frames, source deletion, renaming, persistence, undo/redo and registration. The actual viewport and panel were also opened and visually inspected.

`__init__.py` defines the UI and properties; `transform_view.py` implements live readings and edits; `frames.py` owns saved frames and viewport indicators; `engine.py` implements native field edits and transactional world positioning; `math_core.py` holds Blender-independent rules; `orientation.py` provides orientation utilities.
