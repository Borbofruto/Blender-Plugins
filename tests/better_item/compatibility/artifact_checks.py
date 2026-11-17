"""Small integrity checks shared by the existing matrix and release check."""
import hashlib
import json
import tomllib
import zipfile
from pathlib import Path, PurePosixPath


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def archive_files(path, expected_sha256):
    path = Path(path)
    if sha256(path) != expected_sha256:
        raise ValueError('Installer SHA256 differs from suite.json: ' + str(path))
    files = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe archive entry: ' + name)
            if info.is_dir():continue
            if name in files or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Duplicate or symbolic-link archive entry: ' + name)
            files[name] = archive.read(info)
    return files


def tree_files(directory):
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError('Symbolic-link source directory: ' + str(directory))
    files = {}
    for path in directory.rglob('*'):
        if path.is_symlink():raise ValueError('Symbolic link in source: ' + str(path))
        if path.is_file():files[path.relative_to(directory).as_posix()] = path.read_bytes()
    return files


def verify_tree(directory, expected):
    actual = tree_files(directory)
    extra = sorted(actual.keys() - expected.keys())
    missing = sorted(expected.keys() - actual.keys())
    changed = sorted(name for name in actual.keys() & expected.keys() if actual[name] != expected[name])
    if extra or missing or changed:
        raise ValueError('Source differs from frozen archive in %s: extra=%s missing=%s changed=%s. Use a fresh workspace; no files were removed.'
                         % (directory, extra, missing, changed))


def verify_existing(directory, expected):
    if Path(directory).exists():verify_tree(directory, expected)


def runtime_fingerprint(files):
    digest=hashlib.sha256()
    for name in sorted(name for name in files if name.endswith('.py')):
        digest.update(name.encode('utf-8'));digest.update(b'\0');digest.update(files[name])
    return digest.hexdigest()


def verify_suite_archive(path,suite):
    files=archive_files(path,suite['addon_zip_sha256'])
    manifest=tomllib.loads(files['blender_manifest.toml'].decode('utf-8'))
    if manifest['version']!=suite['addon_version']:
        raise ValueError('Installer version differs from suite.json')
    if runtime_fingerprint(files)!=suite['python_source_sha256']:
        raise ValueError('Installer Python fingerprint differs from suite.json')
    return files


def verify_workspace_inputs(root):
    root = Path(root)
    manifest = json.loads((root / 'workspace-inputs.json').read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
            raise ValueError('Unsafe workspace input: ' + name)
        path = root / name
        if path.is_symlink() or sha256(path) != digest:
            raise ValueError('Prepared input was changed: ' + name)
    expected = {name for name in manifest['files'] if name.startswith('tests/')}
    actual = {'tests/' + name for name in tree_files(root / 'tests')}
    if actual != expected:raise ValueError('Prepared test inventory was changed; use a fresh workspace')
