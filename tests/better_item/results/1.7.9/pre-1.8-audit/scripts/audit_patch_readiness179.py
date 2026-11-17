"""Prepare new diagnostic-only inputs; never change the stable package."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT/'Blender-Plugins'
BASE=Path('D:/Codex-BetterItem-Patch-Readiness179')
INPUT=BASE/'input'
WORK=BASE/'workspace-v3'
tools=REPO/'tests/better_item/compatibility'
INPUT.mkdir(parents=True,exist_ok=True)
(INPUT/'addons').mkdir(exist_ok=True)
shutil.copyfile(REPO/'addons/better_item.zip',INPUT/'addons/better_item.zip')
dest=INPUT/'tests/better_item'
dest.mkdir(parents=True,exist_ok=True)
for path in (REPO/'tests/better_item').glob('*.py'):
    shutil.copyfile(path,dest/path.name)
for name in ('probe_window_boundary179.py','probe_blender_window_control179.py'):
    shutil.copyfile(ROOT/name,dest/name)
shutil.copytree(tools,dest/'compatibility',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
suite=json.loads((dest/'compatibility/suite.json').read_text())
suite['studies'] += [{'script':name,'mode':'gui_async'} for name in ('probe_window_boundary179.py','probe_blender_window_control179.py')]
(dest/'compatibility/suite.json').write_text(json.dumps(suite,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(dest/'compatibility/prepare_matrix.py'),'--repository',str(INPUT),'--workspace',str(WORK)],check=True)
for version,exe in [
 ('4.2.0','D:/Codex-BetterItem-179-Portable/blender-4.2.0-windows-x64/blender.exe'),
 ('5.3.0','C:/Users/gabri/Documents/Codex/better-item-compatibility/portable/blender-5.3.0-windows-x64/blender.exe')]:
    completed=subprocess.run([sys.executable,str(WORK/'run_matrix.py'),'--exe',exe,'--version',version,'--studies','--only','probe_window_boundary179.py','probe_blender_window_control179.py'])
    print('DIAGNOSTIC RUN EXIT',version,completed.returncode,flush=True)
    for name in ('probe_window_boundary179','probe_blender_window_control179'):
        data=WORK/'results'/version/(name+'.results.json')
        if data.exists():print(data.read_text(encoding='utf-8'),flush=True)
