# Better Item compatibility matrix

This matrix is pinned to the 1.7.5 installer SHA256 in suite.json. It uses actual official Blender portable builds, separate factory profiles, fresh processes for each entry point, and both background and GUI tests. It does not establish compatibility with every possible scene or future Blender version.

## Reproduce on Windows

Use a repository checkout and a separate writable workspace. With Python 3.11+ (the Blender-bundled Python also works):

```powershell
python tests/better_item/compatibility/prepare_matrix.py --repository C:/work/Blender-Plugins --workspace C:/work/better-item-matrix
python C:/work/better-item-matrix/download_portables.py 5.3.0
python C:/work/better-item-matrix/extract_portable.py 5.3.0
python C:/work/better-item-matrix/run_matrix.py --exe C:/work/better-item-matrix/portable/blender-5.3.0-windows-x64/blender.exe --version 5.3.0
```

Repeat with exact versions in the report. Downloads are official Windows x64 ZIPs checked against official SHA256 files before extraction/execution. Only one older portable extraction needs to be kept at a time; preserve its archive and results. The cleanup script validates the exact workspace target and removes only a named portable extraction. Never use it on your normal Blender installation. Disk and download time are substantial; allow roughly 1 GB per extraction plus each compressed archive.

The launcher sets isolated BLENDER_USER_CONFIG/SCRIPTS/DATAFILES/EXTENSIONS paths and uses factory startup. It does not alter file associations or your default Blender preferences. The archive-install test uses the real extension installation operator in an isolated local repository. On 4.5 it specifically checks the existing 5.0.0 manifest restriction; this must not be confused with a runtime code failure.

Each summary.json records process exit status, timeouts and test JSON. Python failures, reported draw exceptions and unsuccessful asynchronous GUI tests are failures. Source scripts with old release numbers are regression entry points; only those explicitly listed in suite.json belong to this matrix. Tests for the retired 1.7.4 Custom Orientation source are historical and intentionally excluded. The current stress grid omits that removed source (8,064 combinations), while keeping native transform operator comparisons.

## Blender 5.1 exit diagnostic

The first GUI stress invocation exposed a test-launcher issue: after file reload the timer had no current window, and calling wm.quit_blender crashed in wm_exit_schedule_delayed. diagnose_exit.py reproduces it without Better Item. Run it in a real GUI with and without `-- --safe`. The safe variant obtains a valid window and uses a public context override for shutdown. The generic synchronous-GUI launcher now does the same. This change only controls the test process; no runtime add-on workaround was added. Initial failure and corrected-run evidence are recorded separately in the compatibility report.

The reports distinguish successful runtime tests, legitimate solver refusals, manifest restrictions and untested interactions. Physical mouse dragging, all render backends, all platforms, migration from every historic .blend and every Edit Mode pivot configuration are not certified by this matrix.
