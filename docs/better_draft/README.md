# Better Draft 0.1.1 (provisional name)

Exports the outline of a flat mesh to DXF with real LINE, ARC and CIRCLE entities, in millimetres at 1:1. Bevelled corners and round holes are recognised from the mesh; each run gets a confidence, and you can force a run to be an arc or straight lines.

Blender 4.2 or newer. Install `addons/better_draft.zip` with **Edit > Preferences > Get Extensions > Install from Disk**. No internet connection is needed: ezdxf and its dependencies ship inside the ZIP.

## Export

Select one or more mesh objects in Object Mode and choose **File > Export > Technical Profile (.dxf)**.

- **Which faces:** a flat mesh uses all its faces. A mesh with thickness uses the faces coplanar with the active face (set it in Edit Mode) or, without one, with the largest face. The drawing is seen from the object's +Z.
- **Layers:** `OUTER` for the outer outline, `INNER` for holes. Units are declared as millimetres.
- **Modifiers** are applied on a temporary copy. The scene is not changed.
- **Report:** a `.txt` next to each DXF lists every entity with radius, centre, segment count, maximum deviation, confidence and whether it was marked by hand.

| Option | Default | Meaning |
| --- | --- | --- |
| Confidence Threshold | 0.7 | Arc candidates at or above this become arcs |
| Min Segments | 4 | Fewer segments never become an arc automatically |
| Circle Min Segments | 8 | A whole loop becomes a circle only from this many segments |
| Straight Tolerance | 0.1° | Smaller turns are subdivisions of a straight line |
| Fit Tolerance | 0.01 mm | Largest vertex distance to its arc or line; also the flatness tolerance |
| Plane | Local Part | Or World XY (region must be parallel to it) |
| Files | One per Object | Or Single File, pieces side by side |
| Spacing | 10 mm | Gap between pieces side by side |
| Loose Parts | Stop | Or Largest (one copy if the largest parts are identical) or All |
| Min Part Area | 1 % | Parts smaller than this share of the largest are ignored |

If any selected object cannot be exported, nothing is written and the message says why and what to do.

## Marking runs

In Edit Mode select outline edges and use the right-click menu or **Edge** menu:

- **Mark as Arc:** the run becomes one arc if it fits within Fit Tolerance; otherwise the export stops and says so.
- **Mark as Lines:** the run stays straight segments.
- **Mark as Automatic:** recognition decides again.

If a run has edges with different marks, Lines wins over Arc, and Arc wins over Automatic. Marks are stored in the edge attribute `better_draft_arc_mode` (0 automatic, 1 arc, 2 lines). It is the only data the add-on writes to the mesh, and only when you mark edges.

## Limits

- Blender's Bevel produces true circular arcs only on 90° corners. On other corner angles the profile is not circular and exports as lines.
- A regular polygon and a circle with the same number of vertices are identical meshes. Use Circle Min Segments or Mark as Lines to keep polygons.
- Accuracy depends on the distance between the mesh and its own object origin (float32): about 0.003 mm at 100 m and about 0.06 mm at 1 km. Where the object sits in the world does not matter.
- Marks are read from the evaluated mesh; modifiers that create new edges may not carry them.
- Ellipses, splines and variable radius export as lines.

Reports: [v0 report](relatorio-v0.md) · [calibration](calibracao-v0.md) · [decisions](decisoes-v0.md) · [specification](especificacao-v0.md)
