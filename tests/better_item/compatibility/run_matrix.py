"""Run isolated Blender processes against a frozen add-on package."""
import argparse,json,os,subprocess,sys,time,shutil,hashlib,zipfile
from pathlib import Path
from artifact_checks import verify_suite_archive,verify_tree,verify_existing,verify_workspace_inputs
parser=argparse.ArgumentParser();parser.add_argument('--exe',required=True);parser.add_argument('--version',required=True);parser.add_argument('--only',nargs='*');parser.add_argument('--studies',action='store_true');args=parser.parse_args()
root=Path(__file__).resolve().parent
if Path(args.version).name!=args.version or args.version in {'.','..'}:parser.error('Version must be a single directory name')
out=root/'results'/args.version
out.mkdir(parents=True,exist_ok=True)
summary={'requested_version':args.version,'executable':args.exe,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'tests':[],'passed':False}
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
def integrity_failed(error):
 summary.update(passed=False,integrity_error=str(error),finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 parser.exit(2,'Integrity check failed: '+str(error)+'\n')
try:
 suite=json.loads((root/'suite.json').read_text(encoding='utf-8'))
 summary.update(addon_version=suite['addon_version'],addon_zip_sha256=suite['addon_zip_sha256'])
 verify_workspace_inputs(root)
 frozen=verify_suite_archive(root/'source/better_item.zip',suite)
 verify_tree(root/'source/better_item',frozen)
 verify_existing(out/'better_item',frozen)
except (ValueError,OSError,KeyError,zipfile.BadZipFile) as exc:integrity_failed(exc)
entries=([{'script':'api_probe.py','mode':'background'}] if (root/'api_probe.py').exists() else [])+suite['tests']
if args.studies:entries+=suite.get('studies',[])
if args.only and set(args.only)-{entry['script'] for entry in entries}:parser.error('Unknown or disabled test in --only')
if not entries:parser.error('No test entries selected')
allowed_scripts={p.name for p in (root/'tests').glob('*.py')}|{'api_probe.py'}|{'launch_'+e['script'] for e in entries if e['mode']=='gui_sync'}
if {p.name for p in out.glob('*.py')}-allowed_scripts:parser.error('Output test inventory contains stale scripts; use a fresh workspace')
out.mkdir(parents=True,exist_ok=True)
shutil.copytree(root/'source/better_item',out/'better_item',dirs_exist_ok=True)
for f in (root/'tests').glob('*.py'):shutil.copyfile(f,out/f.name)
probe=root/'api_probe.py'
if probe.exists():shutil.copyfile(probe,out/probe.name)
env=os.environ.copy()
for kind in ('CONFIG','SCRIPTS','DATAFILES','EXTENSIONS'):
 path=out/'profile'/kind.lower();path.mkdir(parents=True,exist_ok=True);env['BLENDER_USER_'+kind]=str(path)
temp=out/'profile/temp';temp.mkdir(parents=True,exist_ok=True)
env['TEMP']=str(temp);env['TMP']=str(temp)
env['PYTHONIOENCODING']='utf-8';env['PYTHONDONTWRITEBYTECODE']='1'
info=subprocess.run([args.exe,'--version'],capture_output=True,env=env,encoding='utf-8',errors='replace',timeout=30)
(out/'blender-version.txt').write_text(info.stdout+info.stderr,encoding='utf-8')
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
for entry in entries:
 name=entry['script'];mode=entry['mode']
 if args.only and name not in args.only:continue
 # Check the actual imported runtime before every process, not just a hash
 # declared in the summary or a previous preparation step.
 try:
  verify_workspace_inputs(root)
  verify_suite_archive(root/'source/better_item.zip',suite)
  verify_tree(root/'source/better_item',frozen)
  verify_tree(out/'better_item',frozen)
 except (ValueError,OSError,KeyError,zipfile.BadZipFile) as exc:integrity_failed(exc)
 script=out/name
 expected_script=root/'api_probe.py' if name=='api_probe.py' else root/'tests'/name
 if script.read_bytes()!=expected_script.read_bytes():integrity_failed('Copied test script was changed: '+name)
 script.with_suffix('.results.json').unlink(missing_ok=True)
 (out/(name+'.failed')).unlink(missing_ok=True)
 cmd=[args.exe,'--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1']
 if mode=='background':cmd+=['--background']
 if mode=='gui_sync':
  wrapper=out/('launch_'+name)
  wrapper.write_text('import bpy,runpy,traceback\nfrom pathlib import Path\ndef run():\n try:\n  area=next(a for a in bpy.context.screen.areas if a.type=="VIEW_3D");region=next(r for r in area.regions if r.type=="WINDOW")\n  with bpy.context.temp_override(area=area,region=region):runpy.run_path('+repr(str(script))+',run_name="__main__")\n except Exception:\n  traceback.print_exc();Path('+repr(str(out/(name+'.failed')))+').write_text(traceback.format_exc(),encoding="utf-8")\n window=next(iter(bpy.context.window_manager.windows))\n with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()\n return None\nbpy.app.timers.register(run,first_interval=1)\n',encoding='utf-8')
  cmd+=['--python',str(wrapper)]
 else:cmd+=['--python',str(script)]
 start=time.monotonic();timed_out=False
 with (out/(name+'.log')).open('w',encoding='utf-8') as log:
  try:p=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW);code=p.returncode
  except subprocess.TimeoutExpired:code=None;timed_out=True
 text=(out/(name+'.log')).read_text(encoding='utf-8',errors='replace');result_path=script.with_suffix('.results.json');data=None
 if result_path.exists():
  try:data=json.loads(result_path.read_text(encoding='utf-8-sig'))
  except ValueError:pass
 passed=code==0 and not timed_out and not (out/(name+'.failed')).exists() and 'Traceback (most recent call last)' not in text and not (data and (data.get('passed') is False or data.get('draw_errors') or data.get('errors')))
 if mode=='gui_async':passed=passed and bool(data and data.get('passed'))
 row={'script':name,'mode':mode,'passed':bool(passed),'exit_code':code,'timeout':timed_out,'seconds':round(time.monotonic()-start,3),'result':data}
 summary['tests'].append(row);summary['passed']=all(x['passed'] for x in summary['tests']);(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(args.version,name,'PASS' if passed else 'FAIL',row['seconds'],flush=True)
summary['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
sys.exit(0 if summary['passed'] else 1)
