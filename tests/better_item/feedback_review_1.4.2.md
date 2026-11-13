# Better Item 1.4.2 feedback review

The pasted document was reviewed as evidence, not treated as implementation instructions.

| Item | Finding and action |
| --- | --- |
| Confirmed BI-T006 | Accepted locked-axis inverse-solve roundoff is now propagated into final world verification. 1,500 rotated/scaled-parent cases pass; genuine lock movement and injected unexpected errors still fail and roll back. |
| README encoding | Replaced the damaged arrow/range text and checked the English manual as ASCII/UTF-8. Tests remain in the repository, outside the runtime ZIP. |
| Attachment 1-3: enums | The premise is incorrect. Blender explicitly supports four-item `(identifier, name, description, number)` tuples. Raw PropertyGroup enum storage is integer, not UID text. Stable serials already survive intermediate removal; a dedicated execution test confirms it. The proposed string-IDProperty rewrite would break the RNA contract. |
| 4: multiwindow | Added full window/screen/area/region overrides and one refresh per visible scene. A real two-main-window test passes. Secondary child windows share a scene by Blender design; the test uses independent main windows. |
| 5: context | Scene-owned frame chains and enum items use their owner scene. Viewport-dependent sources reject a foreign scene explicitly; scalar getters handle domain/context failures without tracebacks. |
| 6: dialog name | Retaining an operator's last values is standard Blender behavior, not data corruption. An unset name gets the default; explicitly supplied names remain supported. |
| 7: linked fields | The UI already disabled all non-Manual source fields. Scalar writes now also check Manual mode rather than only the old Object-link flag. |
| 8: singular inverse | Added a local BI-T005 wrapper around the inverse solve. The earlier absolute-target solver already rejects a singular parent first in normal operation. |
| 9: small dimensions | A large finite ratio is not itself a bug. No arbitrary 1e-6-unit cutoff was introduced; such a cutoff is scale-dependent and would reject legitimate small geometry. Existing requested-result verification and rollback remain. |
| 10: unit scale | RNA clamps normal assignments above zero. Added a defensive finite-positive check with BI-D001; a corrupted/script-bypassed value was not reproduced. |
| 11: old API | Kept the existing compatibility API and scene migration. Removing public properties during a maintenance release is unnecessary. |
| 12: applied basis offset | Kept the existing world-space left-multiplied offset; clarified its order in the manual. |
| 13: Normal probe | Sampling is exact native behavior, deduplicated by changed selection/geometry/source transforms. Probe names are unique. Unchanged selection does not create/delete an orientation every tick. |
| 14: Gimbal | The suggested Quaternion/Local fallback is incorrect for the tested Blender version. Existing 48 execution comparisons with Blender's native transforms pass, including Quaternion and Axis-Angle. |
| 15: redraw | No persistent UI failure was reproduced. Link controls remain standard RNA/UI properties. |
| 16: tiny positions | No blanket tolerance relaxation was introduced. The fix accounts only for accepted, actually snapped locked channels; final distribution separation still has independent verification. |
| 17: legacy schema | Existing 1.3 migration and fresh-process persistence tests pass. No evidence of the hypothesized additional schema was provided. |
| 18: Normal in Object Mode | Matching Blender's Local fallback is intentional and is now explicit in the manual. |

Enum contract: https://docs.blender.org/api/5.2/bpy.props.html#bpy.props.EnumProperty

Native-menu deletion ends only the native export, not the scene frame. Invalid-source suspension remains distinct: an export deliberately removed by the add-on can recover when its source is repaired.
