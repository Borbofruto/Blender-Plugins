"""Prepare a writable, release-pinned compatibility workspace from a checkout."""
import argparse
import hashlib
import json
from pathlib import Path
from artifact_checks import verify_suite_archive, sha256, verify_existing

p=argparse.ArgumentParser()
p.add_argument('--repository',type=Path,required=True)
p.add_argument('--workspace',type=Path,required=True)
a=p.parse_args()
repo=a.repository.resolve();work=a.workspace.resolve();tools=Path(__file__).resolve().parent
if work==repo:p.error('Use a separate writable workspace')
suite=json.loads((tools/'suite.json').read_text(encoding='utf-8'))
archive=repo/'addons/better_item.zip'
prefix='import sys as _compat_sys\n_compat_sys.dont_write_bytecode=True\nfrom pathlib import Path as _CompatPath\n_compat_sys.path.insert(0,str(_CompatPath(__file__).resolve().parent))\n'
tests={}
for entry in suite['tests']+suite.get('studies',[])+[{'script':n} for n in suite.get('auxiliary_tests',[])]:
    name=entry['script']
    if Path(name).name!=name or Path(name).suffix!='.py':p.error('Test scripts must use flat Python filenames')
    source=(repo/'tests/better_item'/name).read_text(encoding='utf-8-sig')
    if 'from __future__' in source:p.error('Update bootstrap for future-import ordering')
    tests[name]=(prefix+source).encode('utf-8')
try:
    contents=verify_suite_archive(archive,suite)
    # Refuse incompatible reuse before overwriting anything. Never remove
    # source, results or profiles left by a previous release.
    verify_existing(work/'source/better_item',contents)
    verify_existing(work/'tests',tests)
    old=work/'source/better_item.zip'
    if old.exists() and sha256(old)!=suite['addon_zip_sha256']:
        raise ValueError('Workspace belongs to another installer; use a fresh workspace')
except (ValueError,OSError) as exc:p.error(str(exc))
work.mkdir(parents=True,exist_ok=True)
inputs={}
for name in ('run_matrix.py','api_probe.py','artifact_checks.py','suite.json','download_portables.py','extract_portable.py','cleanup_portable.ps1'):
    data=(tools/name).read_bytes()
    (work/name).write_bytes(data)
    inputs[name]=hashlib.sha256(data).hexdigest()
(work/'source').mkdir(exist_ok=True)
(work/'source/better_item.zip').write_bytes(archive.read_bytes())
for name,data in contents.items():
    target=work/'source/better_item'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
for name,data in tests.items():
    target=work/'tests'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    inputs['tests/'+name]=hashlib.sha256(data).hexdigest()
(work/'workspace-inputs.json').write_text(json.dumps({'files':inputs},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Prepared',suite['addon_version'],'in',work)
