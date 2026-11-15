# Better Item 1.7.1 — Offset corrections and Live UI

## Changes
- Offset only modifies selected reference coordinates. A stored `arrange_on_axis=True` no longer projects objects onto the reference line. This option caused the transverse alignment seen in the 1.7.0 sidebar and is no longer displayed. The legacy direct Python planning path retains its explicit compatibility behavior.
- Geometry Bounds at zero gap retains the last entered nonzero sign. First use defaults positive. The sign is scene data, survives save/reopen, and migrates from existing nonzero Spacing. There is no new Direction selector.
- Live is a checkbox. Enabling it captures current poses without moving objects or replacing the one-shot Spacing request. In Live the field reads actual uniform spacing; editing updates the selection. Disabling keeps the result. With Live off, Distribute applies the requested value. Current inspection is automatic independently of Live. The sidebar has no Confirm/Cancel transaction buttons.
- Changing selection or target transforms outside Live requires disabling/re-enabling it. Native undo/redo clears the transient session. Existing preview Python operators remain available for compatibility.
- Endpoint placement and geometry measurement contracts are unchanged. No animation or permanent linkage is introduced.

## Executed validation
Blender 5.2.3 LTS / Windows.
- New five-cube regression: 30 combinations of five placement bases, X/Y/Z, global/rotated object orientation; unselected reference coordinates preserved even with the old alignment flag enabled.
- Negative → zero, positive → zero, negative → zero: packed geometry keeps the requested side. Last-sign persistence and transient checkbox state checked across file save/reopen.
- Checkbox activation has no initial movement/request mutation; live edits update; disabling retains poses; subsequent non-live edits do not move objects.
- Existing matrix regression: 320 Endpoint batches and 140 Offset batches, including all placement bases, parents, mirrors, unit scales and masks.
- Existing contract, preview/native-operator Undo/Redo, geometry/cache/dependency/rollback regressions pass again.
- Actual Blender sidebar: checked all six timed phases, live checkbox state, geometry updates, endpoint control updates, disable behavior; no panel draw exceptions. The script changes RNA controls directly; it does not automate physical mouse dragging or claim a new mouse-driven undo test.
- Installer syntax/archive/extension validation and the new regression against its extracted contents are checked before publication.

Result JSON files are in `tests/better_item/results/1.7.1/`. The new regressions are `test_better_item_171.py` and `test_better_item_gui171.py`; existing 1.7.0 suites remain under the same test paths.
