# Better Item compatibility matrix

This matrix is pinned to the 1.7.9 installer SHA256 in suite.json. It uses actual official Blender portable builds, separate factory profiles, fresh processes for each entry point, and both background and GUI tests. It does not establish compatibility with every possible scene or future Blender version. New executions are stored under results/1.7.9 in the repository; earlier release results are historical evidence. The new gui_async test_native_sync179.py checks real-timer failure isolation/recovery, bounded retry, native deletion, scene switching and transient-health cleanup. Existing operator/cache regressions remain in the suite.

## Reproduce on Windows

Use a repository checkout and a separate writable workspace. With Python 3.11+ (the Blender-bundled Python also works):

```powershell
python tests/better_item/compatibility/prepare_matrix.py --repository C:/work/Blender-Plugins --workspace C:/work/better-item-matrix
python C:/work/better-item-matrix/download_portables.py 5.3.0
python C:/work/better-item-matrix/extract_portable.py 5.3.0
python C:/work/better-item-matrix/run_matrix.py --exe C:/work/better-item-matrix/portable/blender-5.3.0-windows-x64/blender.exe --version 5.3.0
```

Repeat with exact versions in the report. Downloads are official Windows x64 ZIPs checked against official SHA256 files before extraction/execution. Only one older portable extraction needs to be kept at a time; preserve its archive and results. The cleanup script validates the exact workspace target and removes only a named portable extraction. Never use it on your normal Blender installation. Disk and download time are substantial; allow roughly 1 GB per extraction plus each compressed archive.

The launcher sets isolated BLENDER_USER_CONFIG/SCRIPTS/DATAFILES/EXTENSIONS paths and uses factory startup. It does not alter file associations or your default Blender preferences. The archive-install test uses the real extension installation operator in an isolated local repository. Installation expectations are read from the packaged manifest. The current minimum is 4.2.0; 4.5 is no longer an expected rejection.

Each summary.json records process exit status, timeouts and test JSON. Python failures, reported draw exceptions and unsuccessful asynchronous GUI tests are failures. Source scripts with old release numbers are regression entry points; only those explicitly listed in suite.json belong to the default matrix. Tests for the retired 1.7.4 Custom Orientation source are historical and intentionally excluded. The current stress grid omits that removed source (8,064 combinations), while keeping native transform operator comparisons.

## Blender 5.1 exit diagnostic

The first GUI stress invocation exposed a test-launcher issue: after file reload the timer had no current window, and calling wm.quit_blender crashed in wm_exit_schedule_delayed. diagnose_exit.py reproduces it without Better Item. Run it in a real GUI with and without `-- --safe`. The safe variant obtains a valid window and uses a public context override for shutdown. The generic synchronous-GUI launcher now does the same. This change only controls the test process; no runtime add-on workaround was added. Initial failure and corrected-run evidence are recorded separately in the compatibility report.

The reports distinguish successful runtime tests, legitimate solver refusals, manifest restrictions and untested interactions. Physical mouse dragging, all render backends, all platforms, migration from every historic .blend and every Edit Mode pivot configuration are not certified by this matrix.

## Optional Edit Mode foundation study

`run_matrix.py --exe PATH_TO_BLENDER --version VERSION --studies --only test_editmode_foundations.py` runs the independent GUI BMesh probe. It does not import Better Item and is not a shipped Edit Mode feature. The default runtime suite has 25 entry points (the 24 entries from the consolidation plus the scene-unit regression). The probe is intentionally small; it does not certify dense-mesh performance, shape keys or a complete reference identity implementation.

`prepare_matrix.py` also copies `test_cross_version_state.py` into the workspace tests directory. Run it with Blender 4.2.0 and `-- --write --fixture PATH/state.blend`, then with 5.3.0 and `-- --fixture PATH/state.blend`. Use `--background --factory-startup --python-exit-code 1 --python PATH_TO_SCRIPT` for both. This checks one representative upward migration, not universal backward file compatibility.

For 4.2, the cache fixture selects the native legacy Action API when slots/layers are absent. This only prepares native test data; no animation runtime or Action compatibility layer is added to Better Item. Original user installations are not modified. Some previously used compressed downloads may be evicted to preserve disk space; official URLs and checksum records are retained and the download command can recreate them.

Historical release reports must be reproduced from their recorded Git commit. The toolkit on main is pinned to the current installer, not all historical ZIPs.

For a fresh-process Placement persistence check, first run `test_better_item_173.py` through the matrix, then run the copied auxiliary `tests/test_better_item_placement177_persistence.py` in a new Blender background process with `--python-exit-code 1 --python SCRIPT -- --source WORKSPACE/source --fixture WORKSPACE/results/VERSION/test_better_item_173.blend`. It verifies Volume for Endpoint, Geometry for Offset and no persisted Live session. Legacy migration still uses the existing two-phase `test_better_item_migration173.py`, with a real 1.7.2 source for `--prepare --source OLD/src`, followed by a fresh current-source process. Exact commands used for 1.7.7 are preserved in that release's extra-results summary. `python_source_sha256` in the current suite hashes the sorted Python basenames, each followed by NUL and its raw file bytes; individual hashes are in the release handoff snapshot.

## Opt-in cache benchmark

After preparing the workspace, run `run_matrix.py --exe PATH_TO_BLENDER --version VERSION --studies --only benchmark_cache_invalidation.py`. It measures 600/1500 shared-mesh cubes in Origins, Geometry Bounds and Volume, unchanged reads, unrelated Empty transforms and edits to a material actually used by the objects. Three samples per event report the median, actual full-inspection counts and aggregated evaluated-ID flags. Thirty explicit calls measure sync separately in an actual GUI context; they are not measurements of timer scheduling or whole-viewport FPS. Timings have no pass/fail threshold. Do not run other test processes concurrently with a performance comparison.

For before/after comparisons, prepare separate workspaces from each recorded commit and ZIP. The 1.7.8 baseline uses the immutable 1.7.7 archive plus the SAME benchmark script from 1.7.8; it is a new measurement of the old runtime, not reused historical timings. Results and the remaining shader/cold-read costs are in `results/1.7.8/` and `docs/better_item/release-1.7.8.md`.

## Release and workspace integrity (1.7.9)

Run `python tests/better_item/compatibility/check_release.py --repository PATH_TO_CHECKOUT` after packaging and updating current documentation/snapshot. It checks the root README and package README version, first changelog entry, release/snapshot links, suite fingerprints, checksums and exact ZIP/source bytes. It does not replace runtime tests or native extension validation.

`prepare_matrix.py` now freezes test/tool input hashes in `workspace-inputs.json`. Preparing the SAME untouched package/tests again is supported. Different, edited or extra runtime/test files are rejected with a fresh-workspace instruction before overwriting source. Results and profiles are never recursively removed to make a workspace pass. Use a new workspace for each changed artifact/test set; do not copy the new runner into an older prepared workspace.

Before launching Blender and before each test process, the runner verifies the installer hash/version/Python fingerprint, exact extracted/imported runtime inventory and bytes, and the prepared test/tool inputs. Extra output helper scripts are also rejected. These checks prevent accidental contamination; they are not a security boundary against someone deliberately rewriting the runner and its manifest. TEMP/TMP and Blender user directories are isolated inside each result profile.

Run the pure-Python guard regressions separately with `python tests/better_item/compatibility/test_artifact_guards.py --workspace PATH_TO_WRITABLE_TEST_DIRECTORY`. They use checked temporary subdirectories, exercise positive/negative preparation/runner/release paths and do not launch Blender. Their JSON count is separate from the Blender matrix entry count.

The linked-gesture regression also checks Default Euler-order changes and links switched off/on without an intervening edit. The optional `benchmark_editmode_normal179.py` measures the existing selection-Normal observer in a real GUI; it does not implement Edit Mode targets. Prepared test bootstraps disable bytecode explicitly, and any mid-run integrity failure sets the summary to failed even if preceding tests passed.

For the consolidated 1.7.9 comparison, use the immutable 1.7.8 ZIP with both CURRENT benchmark scripts and the current integrity-aware runner in a separate prepared workspace. Results are in `results/1.7.9/integration/benchmark/`; the baseline was measured again, sequentially, against the consolidated ZIP. Keep the original branch matrices/benchmarks under their original hashes.

## Scene-unit qualification

`test_better_item_units179.py` is a default background regression (590 internal cases, 26 unit configurations). The optional `test_better_item_units_gui179.py` renders six configurations and compares native/addon RNA; it does not type into widgets or certify visual rounding. Run both with `--studies --only test_better_item_units179.py test_better_item_units_gui179.py` in a fresh workspace. Results are in `results/1.7.9/units/`. These two entries were run on 4.2.0, 4.2.23 and 5.3.0; the previous full 24-entry matrices were not rerun. Do not claim three new full 25-entry suites. The runtime ZIP is unchanged; see `docs/better_item/units-1.7.9.md` for physical-error and display findings.
