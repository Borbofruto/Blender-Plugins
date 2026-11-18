# SPDX-License-Identifier: GPL-3.0-or-later
# Run test_gui_v0.py in a portable Blender WITH a window, using the isolated
# e2e profile (the ZIP must already be installed there by run_e2e.ps1).
# Usage: run_gui.ps1 -Blender <blender.exe> -Work <dir> [-TimeoutSeconds 240]
param(
    [Parameter(Mandatory = $true)][string]$Blender,
    [Parameter(Mandatory = $true)][string]$Work,
    [int]$TimeoutSeconds = 240
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tests = Split-Path -Parent $here
$version = (Split-Path -Leaf (Split-Path -Parent $Blender)) -replace '^blender-', '' -replace '-windows-x64$', ''
$profile = Join-Path $Work "profiles\e2e-$version"
$env:BLENDER_USER_CONFIG = Join-Path $profile 'config'
$env:BLENDER_USER_SCRIPTS = Join-Path $profile 'scripts'
$env:BLENDER_USER_DATAFILES = Join-Path $profile 'datafiles'
$env:BLENDER_USER_EXTENSIONS = Join-Path $profile 'extensions'
$results = Join-Path $Work 'results'
$log = Join-Path $results "gui-$version.log"
$script = Join-Path $tests 'test_gui_v0.py'
$argList = @('--offline-mode', '--factory-startup', '--enable-event-simulate', '--python-exit-code', '1',
    '--python', "`"$script`"", '--', '--out', "`"$results`"")
$p = Start-Process -FilePath $Blender -ArgumentList $argList -PassThru -RedirectStandardOutput $log -RedirectStandardError "$log.err"
$null = $p.Handle  # keep the handle so ExitCode is available after exit
if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
    Stop-Process -Id $p.Id -Force
    Write-Output "gui timed out on $version"
    exit 1
}
Get-Content $log | Select-String -Pattern '^(PASS|FAIL)|better_draft gui'
$json = Join-Path $results "gui-$version.json"
if ($p.ExitCode -ne 0 -or -not (Test-Path $json)) { exit 1 }
if (-not (Get-Content $json -Raw | ConvertFrom-Json).passed) { exit 1 }
exit 0
