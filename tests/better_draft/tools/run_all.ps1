# SPDX-License-Identifier: GPL-3.0-or-later
# Run every Blender battery on one ZIP: wheel + end-to-end on all portable
# versions, GUI on three, library conflict (both modes), modifier and
# performance studies. Portables missing from -Portable are extracted from
# -Downloads (SHA256 checked) and removed after use.
# Usage: run_all.ps1 -Zip <zip> -Work <dir> -Portable <dir> -Downloads <dir> -Wheels <conflict wheels dir>
param(
    [Parameter(Mandatory = $true)][string]$Zip,
    [Parameter(Mandatory = $true)][string]$Work,
    [Parameter(Mandatory = $true)][string]$Portable,
    [Parameter(Mandatory = $true)][string]$Downloads,
    [Parameter(Mandatory = $true)][string]$Wheels,
    [string]$Python = 'C:\Program Files\Blender Foundation\Blender 5.3\5.3\python\bin\python.exe'
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tests = Split-Path -Parent $here
New-Item -ItemType Directory -Force (Join-Path $Work 'results') | Out-Null
Write-Output "zip sha256 $((Get-FileHash $Zip).Hash)"
$keep = '4.2.0', '4.2.23', '4.5.16', '5.3.0'
$all = '4.2.0', '4.3.2', '4.4.3', '4.5.16', '5.0.1', '5.1.2', '5.2.4', '5.3.0'
function Exe($v) { Join-Path $Portable "blender-$v-windows-x64\blender.exe" }
foreach ($v in $all) {
    $extracted = $false
    if (-not (Test-Path (Exe $v))) { & $Python -I (Join-Path $here 'extract_portable.py') $Downloads $v $Portable | Out-Null; $extracted = $true }
    & (Join-Path $here 'run_e2e.ps1') -Blender (Exe $v) -Zip $Zip -Work $Work 2>&1 | Select-String -Pattern 'e2e:|failed|^FAIL'
    if ($v -in '4.2.0', '4.5.16', '5.3.0') {
        & (Join-Path $here 'run_gui.ps1') -Blender (Exe $v) -Work $Work | Select-String -Pattern 'gui:|^FAIL'
    }
    if ($extracted -and $v -notin $keep) { Remove-Item -Recurse -Force (Join-Path $Portable "blender-$v-windows-x64") }
}
foreach ($v in $keep) {
    foreach ($fs in $false, $true) {
        & (Join-Path $here 'conflict_test.ps1') -Blender (Exe $v) -Zip $Zip -Wheels $Wheels -Work $Work -FactoryStartup:$fs 2>&1 | Select-String 'check exit' | ForEach-Object { "$v $($_.Line)" }
    }
}
foreach ($study in @(@('modifiers', '4.2.0'), @('performance', '4.2.0'), @('performance', '5.3.0'))) {
    $v = $study[1]
    $profile = Join-Path $Work "profiles\e2e-$v"
    $env:BLENDER_USER_CONFIG = Join-Path $profile 'config'
    $env:BLENDER_USER_SCRIPTS = Join-Path $profile 'scripts'
    $env:BLENDER_USER_DATAFILES = Join-Path $profile 'datafiles'
    $env:BLENDER_USER_EXTENSIONS = Join-Path $profile 'extensions'
    & (Exe $v) --offline-mode --background --factory-startup --python-exit-code 1 --python (Join-Path $tests 'test_blender_studies.py') -- --out (Join-Path $Work 'results') --study $study[0] 2>&1 | Out-Null
    Write-Output "study $($study[0]) $v exit $LASTEXITCODE"
}
