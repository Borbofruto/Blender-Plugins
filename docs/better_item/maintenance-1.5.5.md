# Better Item 1.5.5 maintenance audit

Reviewed the ten Python runtime modules against the spatial-precision scope. This revision is a targeted cleanup, not a rewrite of the numeric engine. No new transform modes were added.

## Changes and reasons

| Area | Action | Reason |
| --- | --- | --- |
| Retired animation | Removed automatic dependency-stamp deletion and legacy panel warning from load/register/timer/UI paths | Current runtime must not manage archived authoring data |
| Cache | Removed action/driver discovery and selective-time key branch | Frame/subframe invalidation already handles evaluated geometry; cache identity needs only graph/object/data |
| Frame Apply | Removed cache fallback arguments used only by the archived prototype | Applying current frame components must resolve valid live sources; missing sources reject atomically |
| Geometry Nodes | Added a single ownership/stack validator before Reference Dimensions writes | Never duplicate, reorder or silently choose between owned affine modifiers |
| Frame properties | Moved selector declarations into BetterItemFrame | The owning class defines its own properties instead of root-module annotation injection |
| Selector storage | Replaced the first-five-item slice with a named historical extension; removed unused Location catalog | Remove positional coupling while retaining serialized enum IDs |
| Arrangement | Removed unused _frame_origin helper | Current shared resolver already supplies the data |
| Native names | Exclude empty custom-orientation names from lookup | Avoid unnecessary native-slot probes; no Normal sampling behavior change |
| UI/manual | Scale (Default), Dimensions tooltip, removed active Relative Animation claim | Explain native channels vs measurements without inventing another transform feature |

## Deliberately retained compatibility

Historical enum identifiers/numbers, the old single-source frame pointer and source-schema conversion are needed to open existing .blend reference data. Old Local/Viewport/Parent choices are not current selector features; migration converts their saved meaning. Frame UID identity, component links and persistent consumer choices are retained. Computed link aliases remain used by frame creation and earlier scripts. These are compatibility boundaries, not active animation functionality.

## Geometry Nodes policy

Reading Dimensions includes the current evaluated stack even if that stack is not editable by Better Item. A Reference Dimensions edit requires zero or one owned affine modifier. If present, it must be final and enabled. BI-M001 reports duplicate owned stages; BI-M002 reports downstream modifiers. The addon never repairs those conditions automatically. It does not touch the original mesh or impose a live source relationship. Default / Local dimension edits still use native Scale.

## Animation scope

The active extension does not add/remove drivers, insert/delete keys, bake, evaluate relative authoring channels, display legacy clip controls or alter their data. Old raw properties, actions and driver curves are left as Blender stored them; native Blender can report unresolved old paths. Users evaluating those historical files must use the archived prototype separately. No automatic cleanup is attempted. The driver safety guard inspects driven channels only to avoid overwriting them. The frame-change callback clears numeric measurement caches only.

## Deferred items explained

- **Normal optimization:** the current detector scans edit-selection state periodically to decide whether it needs a native Normal sample. On dense selections that scan itself has a cost. Optimizing it means reducing scans while still detecting changed selection/history; it is not a new Normal feature.
- **Constraint flexibility:** current operations conservatively reject active target constraints. Allowing a rotation-only constraint during a position edit would require verifying its actual channel/hierarchy effects. This revision does not loosen that guard.
- **New interactions:** directly dragging a frame's indicator, adding viewport pivot manipulators or other interactive editing modes would add new UI/behavior. Existing numeric frame editing and native orientation export remain the supported workflow.

## Validation

Tests reproduce renamed-modifier reuse, downstream/duplicate/disabled-stack atomic rejection, readable invalid stacks, Apply component atomicity, stable persisted enum serials, absence of runtime animation-write calls, and unchanged old authoring data/driver curves. A real Blender GUI test checks the stack error, Scale labels and absence of a retired-animation panel. Prior suites cover native axis directions, frames, migration/save/reopen, current UI, projected Dimensions/base-mesh preservation, cache frame/subframe/driver/shape-key behavior, undo/redo and locked-parent numeric roundoff. These results establish tested behavior, not a claim of exhaustive bug freedom.
