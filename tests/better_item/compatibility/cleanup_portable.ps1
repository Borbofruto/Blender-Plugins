param([Parameter(Mandatory=$true)][string]$Version)
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid version' }
$portableRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'portable'))
$target=[IO.Path]::GetFullPath((Join-Path $portableRoot "blender-$Version-windows-x64"))
if ([IO.Path]::GetDirectoryName($target) -ne $portableRoot) { throw 'Outside portable workspace' }
if (-not (Test-Path -LiteralPath $target)) { return }
$item=Get-Item -LiteralPath $target
if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing reparse point' }
Remove-Item -LiteralPath $target -Recurse -Force
Write-Output "Removed tested extraction $Version; archive and results retained"
