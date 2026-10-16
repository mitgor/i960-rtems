#!/usr/bin/env python3
"""Content-based audit against an immutable Git commit; never extracts old archives."""
import argparse,gzip,hashlib,json,lzma,os,sqlite3,stat,subprocess,tarfile,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
WORK=Path('/tmp/codex-tmp-cleanup-work');WORK.mkdir(exist_ok=True)
DB=sqlite3.connect(WORK/'content.sqlite');DB.execute('create table if not exists content (sha text primary key, size integer, locator text)')
def digest(f):
 h=hashlib.sha256();n=0
 while True:
  b=f.read(1024*1024)
  if not b:break
  h.update(b);n+=len(b)
 return h.hexdigest(),n
def add(sha,n,loc):DB.execute('insert or ignore into content values (?,?,?)',(sha,n,loc))
def stream(f,loc):
 sha,n=digest(f);add(sha,n,loc);return sha,n
def scan_archive(path,loc):
 name=str(path)
 if name.endswith(('.tar.gz','.tgz','.tar.xz','.tar')):
  with tarfile.open(path,'r|*') as t:
   for m in t:
    if m.isfile():
     with t.extractfile(m) as f:stream(f,loc+'::'+m.name)
 elif name.endswith('.zip'):
  with zipfile.ZipFile(path) as z:
   for m in z.infolist():
    if not m.is_dir():
     try:
      with z.open(m) as f:stream(f,loc+'::'+m.filename)
     except NotImplementedError:
      with (OUT/'unsupported-zip-members.jsonl').open('a') as log:log.write(json.dumps(dict(archive=loc,member=m.filename,compression=m.compress_type))+'\n')
 elif name.endswith(('.gz','.xz')):
  with (gzip.open if name.endswith('.gz') else lzma.open)(path,'rb') as f:stream(f,loc+'::decompressed')
def index():
 DB.execute('delete from content');DB.commit()
 (OUT/'unsupported-zip-members.jsonl').write_text('')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 (OUT/'base-commit.txt').write_text(commit+'\n')
 rows=[]
 for entry in subprocess.check_output(['git','ls-tree','-rz',commit],cwd=ROOT).split(b'\0'):
  if not entry:continue
  meta,name=entry.split(b'\t',1);mode,typ,oid=meta.split()
  if typ==b'blob':rows.append((name.decode(),oid.decode()))
 artifacts=[];parts=[];cache={}
 with subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE) as p:
  for name,oid in rows:
   if oid not in cache:
    p.stdin.write((oid+'\n').encode());p.stdin.flush();header=p.stdout.readline().split();assert header[:2]==[oid.encode(),b'blob'];n=int(header[2]);left=n;h=hashlib.sha256()
    while left:
     b=p.stdout.read(min(left,1024*1024));assert b;left-=len(b);h.update(b)
    assert p.stdout.read(1)==b'\n';cache[oid]=(h.hexdigest(),n)
   sha,n=cache[oid];add(sha,n,'git:'+commit+':'+name)
   if name.startswith('artifacts/'):
    if name.endswith(('.gz','.xz','.tar','.tgz','.zip')):artifacts.append((name,sha))
    if name.endswith('candidate-parts.json'):parts.append(name)
  p.stdin.close();assert p.wait()==0
 DB.commit();print('Indexed committed blobs',len(rows),flush=True)
 seen=set()
 for i,(name,sha) in enumerate(artifacts):
  if sha in seen:continue
  seen.add(sha);path=ROOT/name
  with path.open('rb') as f:assert digest(f)[0]==sha,'Working archive differs from committed blob: '+name
  scan_archive(path,'git:'+commit+':'+name)
  if i%20==0:DB.commit();print('Archive',i,'/',len(artifacts),name,flush=True)
 for name in parts:
  # Manifests/parts must equal the Git blobs already indexed, not dirty files.
  directory=(ROOT/name).parent
  for path in [ROOT/name]+[directory/x['name'] for x in json.loads((ROOT/name).read_text())]:
   expected=subprocess.check_output(['git','rev-parse',commit+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True).strip()
   actual=subprocess.check_output(['git','hash-object',str(path)],cwd=ROOT,text=True).strip();assert actual==expected
  with tempfile.NamedTemporaryFile(dir=WORK,suffix='.tar.gz') as tmp:
   h=hashlib.sha256();n=0
   for row in json.loads((ROOT/name).read_text()):
    assert Path(row['name']).name==row['name'];part=directory/row['name'];ph=hashlib.sha256();pn=0
    with part.open('rb') as f:
     while True:
      b=f.read(1024*1024)
      if not b:break
      tmp.write(b);h.update(b);ph.update(b);pn+=len(b);n+=len(b)
    assert ph.hexdigest()==row['sha256'] and pn==row['bytes']
   tmp.flush();loc='git:'+commit+':'+name+'::concatenated';add(h.hexdigest(),n,loc);scan_archive(tmp.name,loc)
  DB.commit();print('Split archive indexed',name,flush=True)
 DB.commit();print('Index complete',DB.execute('select count(*) from content').fetchone()[0],flush=True)
def inventory():
 roots=sorted(p for p in Path('/private/tmp').iterdir() if any(x in p.name.lower() for x in ('i960','doom','mylex')))
 (OUT/'roots.json').write_text(json.dumps([str(p) for p in roots],indent=2)+'\n')
 count=matched=missing=total=missing_bytes=0;unique={}
 with gzip.open(OUT/'files.jsonl.gz','wt') as f:
  for root in roots:
   items=[root]
   while items:
    p=items.pop();s=p.lstat();row=dict(path=str(p),root=str(root),mode=stat.S_IMODE(s.st_mode),mtime_ns=s.st_mtime_ns)
    if stat.S_ISLNK(s.st_mode):row.update(kind='symlink',target=os.readlink(p))
    elif stat.S_ISDIR(s.st_mode):row['kind']='directory';items.extend(sorted(p.iterdir(),reverse=True))
    elif stat.S_ISREG(s.st_mode):
     with p.open('rb') as inp:sha,n=digest(inp)
     assert p.stat().st_mtime_ns==s.st_mtime_ns and n==s.st_size,'Changed during inventory: '+str(p)
     hit=DB.execute('select locator from content where sha=? and size=?',(sha,n)).fetchone()
     row.update(kind='file',sha256=sha,size=n,git_source=hit[0] if hit else None)
     count+=1;total+=n
     if hit:matched+=1
     else:missing+=1;missing_bytes+=n;unique.setdefault(sha,dict(path=str(p),size=n))
    else:row['kind']='special'
    f.write(json.dumps(row)+'\n')
   if count%10000<500:print('Inventory',root.name,count,'files',missing,'unmatched',flush=True)
 (WORK/'missing.json').write_text(json.dumps(unique))
 report=dict(roots=len(roots),files=count,logical_bytes=total,matched_files=matched,unmatched_files=missing,unmatched_logical_bytes=missing_bytes,unique_missing=len(unique),unique_missing_bytes=sum(x['size'] for x in unique.values()))
 (OUT/'inventory-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
def pack():
 unique=json.loads((WORK/'missing.json').read_text())
 with tarfile.open(WORK/'missing.tar.gz','w:gz',compresslevel=6) as t:
  for sha,row in unique.items():
   path=Path(row['path'])
   with path.open('rb') as f:assert digest(f)==(sha,row['size'])
   info=t.gettarinfo(str(path),arcname='sha256/'+sha);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with path.open('rb') as f:t.addfile(info,f)
 with tarfile.open(WORK/'missing.tar.gz','r|gz') as t:
  seen=set()
  for m in t:
   with t.extractfile(m) as f:sha,n=digest(f)
   assert m.name=='sha256/'+sha and unique[sha]['size']==n;seen.add(sha)
  assert seen==unique.keys()
 rows=[];whole=hashlib.sha256()
 with (WORK/'missing.tar.gz').open('rb') as f:
  while True:
   b=f.read(80*1024*1024)
   if not b:break
   name='missing.tar.gz.part%03d'%len(rows);(OUT/name).write_bytes(b);whole.update(b);rows.append(dict(name=name,size=len(b),sha256=hashlib.sha256(b).hexdigest()))
 (OUT/'recovery-parts.json').write_text(json.dumps(dict(archive_sha256=whole.hexdigest(),parts=rows),indent=2)+'\n');print('Recovery verified:',len(unique),'unique files;',sum(x['size'] for x in rows),'compressed bytes',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('step',choices=['index','inventory','pack']);a=p.parse_args();globals()[a.step]()
