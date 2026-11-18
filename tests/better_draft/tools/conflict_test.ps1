# SPDX-License-Identifier: GPL-3.0-or-later
# Library conflict study: better_draft plus a fake extension bundling another
# ezdxf or pyparsing wheel, installed in both orders into fresh profiles.
# Usage: conflict_test.ps1 -Blender <exe> -Zip <better_draft.zip> -Wheels <dir> -Work <dir>
param(
    [Parameter(Mandatory = $true)][string]$Blender,
    [Parameter(Mandatory = $true)][string]$Zip,
    [Parameter(Mandatory = $true)][string]$Wheels,
    [Parameter(Mandatory = $true)][string]$Work,
    # With -FactoryStartup each install/check ignores the saved preferences
    # (as the e2e runner does); without it the isolated profile's preferences load.
    [switch]$FactoryStartup
)
$fs = if ($FactoryStartup) { @('--factory-startup') } else { @() }
$modeTag = if ($FactoryStartup) { 'fs' } else { 'prefs' }
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tests = Split-Path -Parent $here
$version = (Split-Path -Leaf (Split-Path -Parent $Blender)) -replace '^blender-', '' -replace '-windows-x64$', ''
$results = Join-Path $Work 'results'
$fakes = @{
    'bd_conflict_pyparsing' = 'pyparsing-3.1.4-py3-none-any.whl'
    'bd_conflict_ezdxf'     = 'ezdxf-1.3.5-py3-none-any.whl'
}
$fakeZips = @{}
foreach ($id in $fakes.Keys) {
    $src = Join-Path $Work "fake\$id"
    if (Test-Path $src) { Remove-Item -Recurse -Force $src }
    New-Item -ItemType Directory -Force (Join-Path $src 'wheels') | Out-Null
    Copy-Item (Join-Path $Wheels $fakes[$id]) (Join-Path $src 'wheels')
    Set-Content -Encoding ascii (Join-Path $src '__init__.py') "def register():`n    pass`n`n`ndef unregister():`n    pass`n"
    $manifest = @"
schema_version = "1.0.0"
id = "$id"
name = "Conflict test $id"
version = "0.0.1"
tagline = "Test extension bundling another library version"
maintainer = "test"
type = "add-on"
blender_version_min = "4.2.0"
license = ["SPDX:GPL-3.0-or-later"]
wheels = ["./wheels/$($fakes[$id])"]
"@
    Set-Content -Encoding ascii (Join-Path $src 'blender_manifest.toml') $manifest
    $outDir = Join-Path $Work 'fake-build'
    New-Item -ItemType Directory -Force $outDir | Out-Null
    & $Blender --factory-startup --command extension build --source-dir $src --output-dir $outDir | Out-Null
    $fakeZips[$id] = Join-Path $outDir "$id-0.0.1.zip"
}
foreach ($id in $fakes.Keys) {
    foreach ($order in 'draft_first', 'fake_first') {
        $label = "$id-$order-$modeTag"
        $profile = Join-Path $Work "profiles\conflict-$version-$label"
        if (Test-Path $profile) { Remove-Item -Recurse -Force $profile }
        foreach ($n in 'config', 'scripts', 'datafiles', 'extensions') { New-Item -ItemType Directory -Force (Join-Path $profile $n) | Out-Null }
        $env:BLENDER_USER_CONFIG = Join-Path $profile 'config'
        $env:BLENDER_USER_SCRIPTS = Join-Path $profile 'scripts'
        $env:BLENDER_USER_DATAFILES = Join-Path $profile 'datafiles'
        $env:BLENDER_USER_EXTENSIONS = Join-Path $profile 'extensions'
        $zips = if ($order -eq 'draft_first') { @($Zip, $fakeZips[$id]) } else { @($fakeZips[$id], $Zip) }
        foreach ($z in $zips) {
            & $Blender --offline-mode $fs --command extension install-file -r user_default --enable $z | Out-Null
            Write-Output "$label installed $(Split-Path -Leaf $z): $LASTEXITCODE"
        }
        & $Blender --offline-mode --background $fs --python-exit-code 1 --python (Join-Path $tests 'test_conflict_check.py') -- --out $results --label $label | Out-Null
        Write-Output "$label check exit $LASTEXITCODE"
    }
}
