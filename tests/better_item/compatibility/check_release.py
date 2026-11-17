"""Verify public release identifiers and exact package/source parity."""
import argparse
import ast
import hashlib
import json
import re
import tomllib
from pathlib import Path
from artifact_checks import verify_suite_archive, verify_tree


def check_release(repo):
    repo=Path(repo).resolve();source=repo/'src/better_item'
    manifest=tomllib.loads((source/'blender_manifest.toml').read_text(encoding='utf-8'))
    version=manifest['version']
    suite=json.loads((repo/'tests/better_item/compatibility/suite.json').read_text(encoding='utf-8'))
    if suite['addon_version']!=version:raise ValueError('suite.json version differs from manifest')
    package=verify_suite_archive(repo/'addons/better_item.zip',suite)
    verify_tree(source,package)
    for name,data in package.items():
        if b'\r\n' in data:raise ValueError('Package text must use LF: '+name)
    root=(repo/'README.md').read_text(encoding='utf-8')
    match=re.search(r'^## Better Item (\S+)',root,re.M)
    if not match or match.group(1)!=version:raise ValueError('Root README version differs from manifest')
    if f'(docs/better_item/release-{version}.md)' not in root:raise ValueError('Root README release-report link is outdated')
    if f'(docs/better_item/handoff-{version}.json)' not in root:raise ValueError('Root README snapshot link is outdated')
    if not (source/'README.md').read_text(encoding='utf-8').startswith('# Better Item '+version+'\n'):
        raise ValueError('Packaged README version differs from manifest')
    changelog=(source/'CHANGELOG.md').read_text(encoding='utf-8')
    if not changelog.startswith('# Better Item — changelog\n\n## '+version+'\n'):
        raise ValueError('First changelog entry differs from manifest')
    checksum=(repo/'dist/SHA256SUMS').read_text(encoding='utf-8').splitlines()
    if suite['addon_zip_sha256']+'  ../addons/better_item.zip' not in checksum:
        raise ValueError('Stable ZIP checksum is outdated')
    h=hashlib.sha256();individual={}
    for path in sorted(source.glob('*.py')):
        data=path.read_bytes();ast.parse(data,filename=path.name)
        h.update(path.name.encode());h.update(b'\0');h.update(data)
        individual['src/better_item/'+path.name]=hashlib.sha256(data).hexdigest()
    if h.hexdigest()!=suite['python_source_sha256']:raise ValueError('Suite Python fingerprint differs from source')
    snapshot_path=repo/f'docs/better_item/handoff-{version}.json'
    snapshot=json.loads(snapshot_path.read_text(encoding='utf-8'))
    if snapshot['version']!=version or snapshot['archive']['sha256']!=suite['addon_zip_sha256']:
        raise ValueError('Handoff artifact differs from release')
    if {row['path']:row['sha256'] for row in snapshot['files']}!=individual:
        raise ValueError('Handoff Python inventory differs from source')
    for path in (repo/'README.md',repo/f'docs/better_item/release-{version}.md'):
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            if not (path.parent/target.split('#')[0]).exists():raise ValueError('Broken local link: '+target)
    return {'passed':True,'version':version,'archive_sha256':suite['addon_zip_sha256'],'python_files':len(individual)}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[3])
    args=parser.parse_args()
    try:print(json.dumps(check_release(args.repository),indent=2))
    except (ValueError,OSError,KeyError) as exc:parser.exit(1,str(exc)+'\n')
