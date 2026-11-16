# Better Item compatibility matrix

This matrix is pinned to the 1.7.7 installer SHA256 in suite.json. It uses actual official Blender portable builds, separate factory profiles, fresh processes for each entry point, and both background and GUI tests. It does not establish compatibility with every possible scene or future Blender version. New executions are stored under results/1.7.7 in the repository; earlier release results are historical evidence. The new gui_sync entry test_better_item_operator177.py checks public Endpoint/Offset kwargs with independent analytic centers, rejection, invoke, repeat-last, Undo/Redo and per-method operator memory.

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

`run_matrix.py --exe PATH_TO_BLENDER --version VERSION --studies --only test_editmode_foundations.py` runs the independent GUI BMesh probe. It does not import Better Item and is not a shipped Edit Mode feature. The default runtime suite has 21 entry points (API probe, 19 existing tests and the new operator regression). The probe is intentionally small; it does not certify dense-mesh performance, shape keys or a complete reference identity implementation.

`prepare_matrix.py` also copies `test_cross_version_state.py` into the workspace tests directory. Run it with Blender 4.2.0 and `-- --write --fixture PATH/state.blend`, then with 5.3.0 and `-- --fixture PATH/state.blend`. Use `--background --factory-startup --python-exit-code 1 --python PATH_TO_SCRIPT` for both. This checks one representative upward migration, not universal backward file compatibility.

For 4.2, the cache fixture selects the native legacy Action API when slots/layers are absent. This only prepares native test data; no animation runtime or Action compatibility layer is added to Better Item. Original user installations are not modified. Some previously used compressed downloads may be evicted to preserve disk space; official URLs and checksum records are retained and the download command can recreate them.

Historical release reports must be reproduced from their recorded Git commit. The toolkit on main is pinned to the current installer, not all historical ZIPs.

For a fresh-process Placement persistence check, first run `test_better_item_173.py` through the matrix, then run the copied auxiliary `tests/test_better_item_placement177_persistence.py` in a new Blender background process with `--python-exit-code 1 --python SCRIPT -- --source WORKSPACE/source --fixture WORKSPACE/results/VERSION/test_better_item_173.blend`. It verifies Volume for Endpoint, Geometry for Offset and no persisted Live session. Legacy migration still uses the existing two-phase `test_better_item_migration173.py`, with a real 1.7.2 source for `--prepare --source OLD/src`, followed by a fresh current-source process. Exact commands used for 1.7.7 are preserved in that release's extra-results summary. `python_source_sha256` in the current suite hashes the sorted Python basenames, each followed by NUL and its raw file bytes; individual hashes are in the 1.7.7 handoff snapshot.
