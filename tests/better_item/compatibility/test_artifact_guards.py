"""Regression tests of the existing preparation/runner and release checks.

Uses temporary directories in the requested workspace; never launches Blender.
Every negative runner case must fail BEFORE trying the nonexistent executable.
"""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile,unittest,zipfile
import contextlib,io,runpy
from types import SimpleNamespace
from unittest.mock import patch
import artifact_checks
from pathlib import Path
from artifact_checks import archive_files,runtime_fingerprint,verify_tree
from check_release import check_release

parser=argparse.ArgumentParser()
parser.add_argument('--workspace',type=Path,required=True)
args=parser.parse_args()
base=args.workspace.resolve();base.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
tools=Path(__file__).resolve().parent


class Guards(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='guard-',dir=base)
        self.root=Path(self.tmp.name).resolve()
        self.assertTrue(self.root.is_relative_to(base))
        self.addCleanup(self.tmp.cleanup)

    def prepare(self):
        work=self.root/'matrix'
        result=subprocess.run([sys.executable,str(tools/'prepare_matrix.py'),'--repository',str(repo),'--workspace',str(work)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        return work

    def reject_runner(self,work,expected):
        result=subprocess.run([sys.executable,str(work/'run_matrix.py'),'--exe','D:/nonexistent-blender-guard.exe','--version','probe'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(expected,result.stderr)
        self.assertNotIn('nonexistent-blender-guard.exe',result.stderr)
        summary=json.loads((work/'results/probe/summary.json').read_text(encoding='utf-8'))
        self.assertFalse(summary['passed'])

    def test_exact_tree_rejects_extra_missing_and_changed(self):
        source=self.root/'source';source.mkdir()
        (source/'a.py').write_bytes(b'one')
        verify_tree(source,{'a.py':b'one'})
        for expected in ({},{'a.py':b'two'},{'a.py':b'one','b.py':b'two'}):
            with self.subTest(expected=expected),self.assertRaises(ValueError):verify_tree(source,expected)

    def test_zip_hash_and_unsafe_entries(self):
        archive=self.root/'bad.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape.py','x')
        with self.assertRaisesRegex(ValueError,'SHA256'):archive_files(archive,'wrong')
        with self.assertRaisesRegex(ValueError,'Unsafe'):archive_files(archive,hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_valid_workspace_can_be_prepared_again(self):
        work=self.prepare()
        result=subprocess.run([sys.executable,str(tools/'prepare_matrix.py'),'--repository',str(repo),'--workspace',str(work)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_preparation_rejects_stale_module_and_preserves_results(self):
        work=self.prepare()
        extra=work/'source/better_item/removed_module.py';extra.write_text('# old')
        marker=work/'results/keep.json';marker.parent.mkdir();marker.write_text('keep')
        result=subprocess.run([sys.executable,str(tools/'prepare_matrix.py'),'--repository',str(repo),'--workspace',str(work)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('removed_module.py',result.stderr)
        self.assertEqual(marker.read_text(),'keep')
        self.assertTrue(extra.exists())

    def test_runner_rejects_extra_source_module(self):
        work=self.prepare();(work/'source/better_item/extra.py').write_text('# extra')
        self.reject_runner(work,'extra.py')

    def test_runner_rejects_edited_source(self):
        work=self.prepare();path=work/'source/better_item/__init__.py'
        path.write_bytes(path.read_bytes()+b'\n# changed')
        self.reject_runner(work,'changed=')

    def test_runner_rechecks_installer_hash(self):
        work=self.prepare();path=work/'source/better_item.zip'
        path.write_bytes(path.read_bytes()+b'changed')
        self.reject_runner(work,'SHA256')

    def test_runner_rejects_modified_test_input(self):
        work=self.prepare();path=next((work/'tests').glob('*.py'))
        path.write_bytes(path.read_bytes()+b'\n# changed')
        self.reject_runner(work,'Prepared input was changed')

    def test_runner_rejects_extra_output_module(self):
        work=self.prepare();folder=work/'results/probe/better_item';folder.mkdir(parents=True)
        with zipfile.ZipFile(work/'source/better_item.zip') as z:z.extractall(folder)
        (folder/'extra.py').write_text('# extra')
        self.reject_runner(work,'extra.py')

    def test_runner_rejects_stale_output_script(self):
        work=self.prepare();folder=work/'results/probe';folder.mkdir(parents=True)
        (folder/'removed_test.py').write_text('# old helper')
        self.reject_runner(work,'stale scripts')

    def test_integrity_failure_after_a_test_replaces_partial_pass(self):
        work=self.prepare()
        original=artifact_checks.verify_tree
        calls=0
        def verified(directory,expected):
            nonlocal calls
            if Path(directory)==work/'results/probe/better_item':
                calls+=1
                if calls==2:raise ValueError('Injected between-process contamination')
            return original(directory,expected)
        fake=SimpleNamespace(stdout='Fake executable for runner unit test only',stderr='',returncode=0)
        with patch.object(sys,'argv',[str(work/'run_matrix.py'),'--exe','not-launched','--version','probe']), \
             patch.object(artifact_checks,'verify_tree',side_effect=verified), \
             patch('subprocess.run',return_value=fake),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exited:
                runpy.run_path(str(work/'run_matrix.py'),run_name='__main__')
        self.assertEqual(exited.exception.code,2)
        summary=json.loads((work/'results/probe/summary.json').read_text())
        self.assertFalse(summary['passed'])
        self.assertEqual(len(summary['tests']),1)
        self.assertIn('between-process',summary['integrity_error'])

    def release_fixture(self):
        fixture=self.root/'release';source=fixture/'src/better_item';source.mkdir(parents=True)
        archive=repo/'addons/better_item.zip'
        with zipfile.ZipFile(archive) as z:z.extractall(source)
        target=fixture/'addons/better_item.zip';target.parent.mkdir();shutil.copyfile(archive,target)
        suite=json.loads((tools/'suite.json').read_text(encoding='utf-8'))
        version=suite['addon_version'];digest=suite['addon_zip_sha256']
        target=fixture/'tests/better_item/compatibility/suite.json';target.parent.mkdir(parents=True)
        target.write_text(json.dumps(suite))
        docs=fixture/'docs/better_item';docs.mkdir(parents=True)
        (docs/f'release-{version}.md').write_text('# Release')
        (fixture/'README.md').write_text(f'## Better Item {version}\n[Report](docs/better_item/release-{version}.md)\n[Snapshot](docs/better_item/handoff-{version}.json)\n',encoding='utf-8')
        (fixture/'dist').mkdir();(fixture/'dist/SHA256SUMS').write_text(digest+'  ../addons/better_item.zip\n')
        files=[{'path':'src/better_item/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(source.glob('*.py'))]
        (docs/f'handoff-{version}.json').write_text(json.dumps({'version':version,'archive':{'sha256':digest},'files':files}))
        return fixture

    def test_release_accepts_consistent_metadata(self):
        self.assertTrue(check_release(self.release_fixture())['passed'])

    def test_release_rejects_old_root_readme(self):
        fixture=self.release_fixture();(fixture/'README.md').write_text('## Better Item 1.7.6\n')
        with self.assertRaisesRegex(ValueError,'Root README version'):check_release(fixture)

    def test_release_rejects_source_package_mismatch(self):
        fixture=self.release_fixture();(fixture/'src/better_item/extra.py').write_text('# extra')
        with self.assertRaisesRegex(ValueError,'extra.py'):check_release(fixture)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards))
    report={'passed':result.wasSuccessful(),'tests_run':result.testsRun,
            'failures':[str(item[0]) for item in result.failures],'errors':[str(item[0]) for item in result.errors]}
    (base/'artifact-guards.results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    sys.exit(0 if result.wasSuccessful() else 1)
