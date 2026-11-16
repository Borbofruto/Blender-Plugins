# Better Item 1.7.4 - Custom Orientation scene picker

## Problem and change
Custom Orientation previously opened an exact-name text field. It did not enumerate scene orientations. The shared child field is now a searchable source picker in Transform, Align and Distribute and the Frame editor. The existing 0.2-second observer refreshes the index after native creation, renaming and deletion and requests sidebar redraw. An empty scene shows informational setup instructions. A deleted or renamed referenced name is not silently replaced; the existing INFO setup diagnostic explains that a new source must be chosen.

Existing source strings and the 1.7.3 alignment contract are unchanged. A Frame exported as a native orientation is also discoverable. This does not add a current-viewport reference mode, animation, or object relationships.

## Compatibility limitation
Blender 5.2 has no public collection of scene custom orientations; static RNA enum items include only defaults. A small adapter reads the dynamic identifiers from a rejected empty orientation-slot assignment. It copies raw names without executing text and checks each candidate against the scene. Temporary slot access restores the prior active orientation, and no native orientation wrapper survives callbacks. Unrecognized exception formats or ambiguous names fall back to the original exact-name input with an informational message. This is a compatibility workaround, not a guaranteed enumeration API. The scene search collection is disposable (may be serialized by Blender), cleared on load/Undo/Redo and rebuilt from native scene data. Saved name strings remain the source of truth. No dynamically growing enum-signature cache is introduced.

Blender API background: [TransformOrientationSlot](https://docs.blender.org/api/5.0/bpy.types.TransformOrientationSlot.html), [Blender developer discussion](https://devtalk.blender.org/t/how-to-get-transform-orientations-data/19706).

## Executed validation
Blender 5.2.3 LTS / Windows:
- Real GUI timer: no orientations, external native creation, quotes/apostrophes/backslashes/Unicode in names, scene isolation, matrix agreement across all three consumers, unchanged active viewport orientation, external rename/deletion, Frame publication, simulated adapter failure, and repeated register/unregister. All panel draw wrappers recorded zero exceptions.
- Saved .blend reopened in a fresh Blender process: existing name references preserved, disposable index cleared and reconstructed.
- Existing 1.7.3 functional checks and 96 Live batches / 192 reference updates repeated successfully.
- Archive syntax/integrity and tests repeated against extracted installer contents before publication.

Only 5.2.3 was runtime-tested. Popup selection with a physical mouse, interactive native Undo/Redo and other Blender versions were not retested for this patch. The tests set the same saved string properties used by the searchable UI and draw the real panels. Earlier numerical test grids are historical evidence, not rerun claims for this patch. The 1.7.3 handoff document remains a versioned baseline; this report records the subsequent change.
