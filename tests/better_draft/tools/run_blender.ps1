# SPDX-License-Identifier: GPL-3.0-or-later
# Run a Python script in a portable Blender with an isolated profile.
# Usage: run_blender.ps1 -Blender <blender.exe> -Profile <dir> -Script <file.py> [-- script args]
param(
    [Parameter(Mandatory = $true)][string]$Blender,
    [Parameter(Mandatory = $true)][string]$Profile,
    [Parameter(Mandatory = $true)][string]$Script,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ScriptArgs
)
New-Item -ItemType Directory -Force $Profile | Out-Null
foreach ($name in 'config', 'scripts', 'datafiles', 'extensions') {
    New-Item -ItemType Directory -Force (Join-Path $Profile $name) | Out-Null
}
$env:BLENDER_USER_CONFIG = Join-Path $Profile 'config'
$env:BLENDER_USER_SCRIPTS = Join-Path $Profile 'scripts'
$env:BLENDER_USER_DATAFILES = Join-Path $Profile 'datafiles'
$env:BLENDER_USER_EXTENSIONS = Join-Path $Profile 'extensions'
$argsList = @('--background', '--factory-startup', '--python-exit-code', '1', '--python', $Script)
if ($ScriptArgs) { $argsList += '--'; $argsList += $ScriptArgs }
& $Blender @argsList
exit $LASTEXITCODE
