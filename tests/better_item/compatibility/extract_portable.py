from pathlib import Path
import argparse,zipfile,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('version');a=p.parse_args();root=Path(__file__).parent
name='blender-'+a.version+'-windows-x64.zip';archive=root/'downloads'/name
expected=next(line.split()[0] for line in (root/'downloads'/('blender-'+a.version+'.sha256')).read_text(encoding='utf-8').splitlines() if line.endswith(name));assert hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()==expected
with zipfile.ZipFile(archive) as z:
 size=sum(f.file_size for f in z.infolist());assert shutil.disk_usage(root).free>size+300*1024*1024,('Need more free disk space',size,shutil.disk_usage(root).free)
 dest=root/'portable';dest.mkdir(exist_ok=True)
 for f in z.infolist():assert (dest/f.filename).resolve().is_relative_to(dest.resolve())
 z.extractall(dest)
print('Extracted verified portable',a.version,size,flush=True)
