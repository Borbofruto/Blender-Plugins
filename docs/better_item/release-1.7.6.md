# Better Item 1.7.6 — Blender 4.2 support

Lower the manifest minimum to Blender 4.2.0 after validating current Object Mode capabilities on 4.2.0, 4.2.23 and intermediate 4.x release lines. Runtime Python is unchanged from 1.7.5. No capabilities were removed to achieve this baseline and no new compatibility branches were added to the extension.

The final archive passed the complete matrix on 4.2.0 and 5.3.0, plus a native install check on 4.5.16. Candidate and earlier identical-code evidence are separately identified in the [compatibility report](compatibility-1.7.6.md). The native-animation cache fixture now supports public pre/post Action-slot test-data APIs; this adds no animation feature. The install test derives eligibility from the actual manifest.

A separate [Edit Mode 2.0 feasibility study](edit-mode-2.0-feasibility.md) documents BMesh primitives, matrix transforms, component references, topology identity, shared vertices and future decisions. Its experimental tests are outside the installer. Edit Mode target manipulation is not implemented in 1.7.6.

The stable addons/better_item.zip is updated in place. Historical release reports and handoff snapshots remain historical. Tested platform: Windows x64; see the report for finite coverage and remaining limits.
