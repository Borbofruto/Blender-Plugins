# SPDX-License-Identifier: GPL-3.0-or-later
# Install a better_draft ZIP into a fresh isolated profile of a portable Blender
# (offline mode) and run the wheel and end-to-end tests.
# Usage: run_e2e.ps1 -Blender <blender.exe> -Zip <better_draft.zip> -Work <dir>
param(
    [Parameter(Mandatory = $true)][string]$Blender,
    [Parameter(Mandatory = $true)][string]$Zip,
    [Parameter(Mandatory = $true)][string]$Work
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tests = Split-Path -Parent $here
$version = (Split-Path -Leaf (Split-Path -Parent $Blender)) -replace '^blender-', '' -replace '-windows-x64$', ''
$profile = Join-Path $Work "profiles\e2e-$version"
if (Test-Path $profile) { Remove-Item -Recurse -Force $profile }
foreach ($n in 'config', 'scripts', 'datafiles', 'extensions') { New-Item -ItemType Directory -Force (Join-Path $profile $n) | Out-Null }
$env:BLENDER_USER_CONFIG = Join-Path $profile 'config'
$env:BLENDER_USER_SCRIPTS = Join-Path $profile 'scripts'
$env:BLENDER_USER_DATAFILES = Join-Path $profile 'datafiles'
$env:BLENDER_USER_EXTENSIONS = Join-Path $profile 'extensions'
$results = Join-Path $Work 'results'
New-Item -ItemType Directory -Force $results | Out-Null
$ErrorActionPreference = 'Continue'
& $Blender --offline-mode --factory-startup --command extension install-file -r user_default --enable $Zip
if ($LASTEXITCODE -ne 0) { Write-Output "install failed: $LASTEXITCODE"; exit 1 }
foreach ($script in 'test_wheel_install.py', 'test_blender_v0.py') {
    & $Blender --offline-mode --background --factory-startup --python-exit-code 1 --python (Join-Path $tests $script) -- --out $results
    if ($LASTEXITCODE -ne 0) { Write-Output "$script failed on $version : $LASTEXITCODE"; exit 1 }
}
Write-Output "e2e passed on $version"
