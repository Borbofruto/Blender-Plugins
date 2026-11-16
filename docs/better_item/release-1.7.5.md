# Better Item 1.7.5 — remove brittle custom-orientation discovery

The Custom Orientation input is removed from Transform, Align and Distribute and Frame editing. The exception-text adapter, dynamic scene-name search collection and custom orientation matrix cache are gone. Existing saved references display **Custom Orientation (Removed)** with informational setup guidance until the user selects Object, Frame or a supported default orientation. No target is moved and no unrelated native orientation is deleted as a side effect of retiring that source.

Frame export to a native transform orientation remains available for G/R through Blender's public operators. Native deletion detection remains. Compatibility storage IDs are intentionally retained so old files are diagnosed honestly instead of appearing to use Global silently; the removed option is not offered for new references.

The same installer was tested on official portable Windows x64 builds 5.3.0, 5.2.4, 5.1.2, 5.0.1 and diagnostically on 4.5.16. See the [compatibility report](compatibility-1.7.5.md) for exact hashes, expected refusals, installation eligibility, corrected test-launcher issues and limits. The 5.0 manifest minimum is unchanged. Earlier release reports and the 1.7.3 maintainer handoff are historical baselines.

No animation runtime, constraint relaxation or new spatial operations were added. The stable addons/better_item.zip replaces the installer in place; prior versions remain in Git history.
