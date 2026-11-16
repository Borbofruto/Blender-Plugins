"""Prepare a writable, release-pinned compatibility workspace from a checkout."""
import argparse,json,hashlib,shutil,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);a=p.parse_args()
repo=a.repository.resolve();work=a.workspace.resolve();tools=Path(__file__).resolve().parent
assert work!=repo,'Use a separate writable workspace'
suite=json.loads((tools/'suite.json').read_text(encoding='utf-8'));archive=repo/'addons/better_item.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==suite['addon_zip_sha256'],'Installer differs from this pinned matrix; update the suite baseline before testing another release'
work.mkdir(parents=True,exist_ok=True)
for name in ('run_matrix.py','api_probe.py','suite.json','download_portables.py','extract_portable.py','cleanup_portable.ps1'):
 src=tools/name;dst=work/name
 if src.resolve()!=dst.resolve():shutil.copyfile(src,dst)
(work/'source').mkdir(exist_ok=True);(work/'source/better_item.zip').write_bytes(archive.read_bytes())
with zipfile.ZipFile(archive) as z:
 dest=work/'source/better_item'
 for f in z.infolist():assert (dest/f.filename).resolve().is_relative_to(dest.resolve())
 z.extractall(dest)
(work/'tests').mkdir(exist_ok=True)
for entry in suite['tests']:
 name=entry['script'];assert Path(name).name==name
 source=repo/'tests/better_item'/name
 text=source.read_text(encoding='utf-8-sig')
 # Repo entry points may add repo/src. The matrix must use its frozen archive.
 prefix='import sys as _compat_sys\nfrom pathlib import Path as _CompatPath\n_compat_sys.path.insert(0,str(_CompatPath(__file__).resolve().parent))\n'
 assert 'from __future__' not in text,'Update bootstrap for future-import ordering'
 (work/'tests'/name).write_text(prefix+text,encoding='utf-8',newline='\n')
print('Prepared',suite['addon_version'],'in',work)
