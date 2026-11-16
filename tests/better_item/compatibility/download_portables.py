"""Download official portable archives in validated HTTP ranges; no installer runs."""
import argparse,concurrent.futures,hashlib,json,os,re,threading,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('versions',nargs='+');a=p.parse_args();root=Path(__file__).resolve().parent/'downloads';root.mkdir(exist_ok=True)
def fetch(url,headers=None):
 req=urllib.request.Request(url,headers=headers or {})
 return urllib.request.urlopen(req,timeout=90)
for version in a.versions:
 assert re.fullmatch(r'\d+\.\d+\.\d+',version)
 series='.'.join(version.split('.')[:2]);filename='blender-'+version+'-windows-x64.zip';url='https://download.blender.org/release/Blender'+series+'/'+filename
 checksum=root/('blender-'+version+'.sha256')
 if not checksum.exists():
  with fetch(url.rsplit('/',1)[0]+'/blender-'+version+'.sha256') as response:checksum.write_bytes(response.read())
 expected=next(line.split()[0] for line in checksum.read_text(encoding='utf-8').splitlines() if line.endswith(filename))
 target=root/filename
 if target.exists() and target.stat().st_size and hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==expected:
  print(version,'already verified',flush=True);continue
 with fetch(url,{'Range':'bytes=0-0'}) as response:
  content_range=response.headers.get('Content-Range','');assert re.fullmatch(r'bytes 0-0/\d+',content_range),content_range
  size=int(content_range.split('/')[-1]);assert len(response.read())==1
 partial=target.with_suffix('.zip.part');lock=threading.Lock();block=4*1024*1024;chunks=list(range(0,size,block));done=0;started=time.monotonic()
 with partial.open('wb') as f:
  f.truncate(size)
  def chunk(start):
   end=min(size,start+block)-1
   for attempt in range(4):
    try:
     with fetch(url,{'Range':'bytes=%d-%d'%(start,end)}) as response:
      assert response.headers.get('Content-Range')=='bytes %d-%d/%d'%(start,end,size),response.headers
      data=response.read();assert len(data)==end-start+1
     with lock:f.seek(start);f.write(data)
     return len(data)
    except Exception:
     if attempt==3:raise
     time.sleep(attempt+1)
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
   for future in concurrent.futures.as_completed([pool.submit(chunk,start) for start in chunks]):
    done+=future.result()
    if done==size or (done//block)%20==0:print(version,round(100*done/size,1),'%',round(time.monotonic()-started,1),'seconds',flush=True)
 actual=hashlib.file_digest(partial.open('rb'),'sha256').hexdigest();assert actual==expected,(actual,expected)
 os.replace(partial,target)
 result={'file':filename,'url':url,'sha256':actual,'verified_against_official_checksum':True,'bytes':size,'download_seconds':round(time.monotonic()-started,2)}
 (root/('blender-'+version+'.verified.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
