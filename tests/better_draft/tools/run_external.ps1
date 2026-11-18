# SPDX-License-Identifier: GPL-3.0-or-later
# Validate end-to-end DXFs with programs independent of ezdxf:
# ODA File Converter round trip, LibreCAD PNG rendering, FreeCAD headless import.
# Usage: run_external.ps1 -DxfDir <dir with .dxf> -Out <dir> -Tools <dir with oda, librecad, freecad>
param(
    [Parameter(Mandatory = $true)][string]$DxfDir,
    [Parameter(Mandatory = $true)][string]$Out,
    [Parameter(Mandatory = $true)][string]$Tools,
    [string]$Python = 'C:\Program Files\Blender Foundation\Blender 5.3\5.3\python\bin\python.exe'
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ext = Join-Path (Split-Path -Parent $here) 'external'
$in = Join-Path $Out 'input'; $dwg = Join-Path $Out 'oda-dwg'; $rt = Join-Path $Out 'oda-roundtrip'; $png = Join-Path $Out 'librecad-png'
foreach ($p in $in, $dwg, $rt, $png) { if (Test-Path $p) { Remove-Item -Recurse -Force $p }; New-Item -ItemType Directory -Force $p | Out-Null }
Copy-Item (Join-Path $DxfDir '*.dxf') $in

$oda = Join-Path $Tools 'oda\ODAFileConverter.exe'
Start-Process $oda -ArgumentList "`"$in`"", "`"$dwg`"", 'ACAD2018', 'DWG', '0', '1', '*.DXF' -Wait
Start-Process $oda -ArgumentList "`"$dwg`"", "`"$rt`"", 'ACAD2018', 'DXF', '0', '1', '*.DWG' -Wait
& $Python -I (Join-Path $ext 'roundtrip_compare.py') $in $dwg $rt (Join-Path $Out 'oda-roundtrip.json')

$lc = Join-Path $Tools 'librecad\LibreCAD.exe'
$okPng = 0
foreach ($f in Get-ChildItem (Join-Path $in '*.dxf')) {
    $target = Join-Path $png ($f.BaseName + '.png')
    $p = Start-Process $lc -ArgumentList 'dxf2png', '-r', '1000x700', '-o', "`"$target`"", "`"$($f.FullName)`"" -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Out 'lc.out') -RedirectStandardError (Join-Path $Out 'lc.err')
    $null = $p.Handle
    if ($p.WaitForExit(60000) -and $p.ExitCode -eq 0 -and (Test-Path $target)) { $okPng++ } else { Write-Output "librecad failed: $($f.Name)" }
}
Write-Output "librecad png: $okPng / $((Get-ChildItem (Join-Path $in '*.dxf')).Count)"

$fc = Get-ChildItem (Join-Path $Tools 'freecad') -Recurse -Filter FreeCADCmd.exe | Select-Object -First 1
$fcHome = Join-Path $Tools 'freecad-home'
New-Item -ItemType Directory -Force $fcHome | Out-Null
$env:FREECAD_USER_HOME = $fcHome; $env:FREECAD_USER_DATA = Join-Path $fcHome 'data'; $env:FREECAD_USER_TEMP = Join-Path $fcHome 'temp'
$env:BD_DXF_DIR = $in; $env:BD_OUT = Join-Path $Out 'freecad-check.json'
& $fc.FullName (Join-Path $ext 'freecad_check.py') 2>&1 | Select-String 'freecad check'
