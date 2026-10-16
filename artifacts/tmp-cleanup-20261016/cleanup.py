#!/usr/bin/env python3
"""Delete only audited project temp roots after verifying committed recovery bytes."""
import argparse,gzip,hashlib,json,os,shutil,stat,subprocess,tarfile,tempfile
from pathlib import Path
from audit import digest,OUT,ROOT,WORK

def committed(path,commit):
 rel=path.relative_to(ROOT).as_posix()
 expected=subprocess.check_output(['git','rev-parse',commit+':'+rel],cwd=ROOT,text=True).strip()
 actual=subprocess.check_output(['git','hash-object',str(path)],cwd=ROOT,text=True).strip()
 assert actual==expected,'Not the committed bytes: '+rel

def open_roots(roots):
 r=subprocess.run(['lsof','-nP','-Fpn'],capture_output=True,text=True)
 assert r.returncode in (0,1),r.stderr
 hits={};pid=None
 for line in r.stdout.splitlines():
  if line.startswith('p'):pid=line[1:]
  if line.startswith('n'):
   name=line[1:];name='/private'+name if name.startswith('/tmp/') else name
   for root in roots:
    if name==root or name.startswith(root+'/'):hits.setdefault(root,[]).append(dict(pid=pid,path=name))
 ps=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
 for line in ps.splitlines():
  if int(line.split(None,1)[0])==os.getpid():continue
  line=line.replace('/tmp/','/private/tmp/')
  for root in roots:
   if root in line:hits.setdefault(root,[]).append(dict(process=line.strip()))
 return hits

def tree(root):
 result={};items=[Path(root)]
 while items:
  p=items.pop();s=p.lstat();row=dict(mode=stat.S_IMODE(s.st_mode),mtime_ns=s.st_mtime_ns)
  if stat.S_ISLNK(s.st_mode):row.update(kind='symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):row['kind']='directory';items.extend(p.iterdir())
  elif stat.S_ISREG(s.st_mode):row.update(kind='file',size=s.st_size)
  else:row['kind']='special'
  result[str(p)]=row
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--delete',action='store_true');args=p.parse_args()
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 for n in ('files.jsonl.gz','roots.json','recovery-parts.json','base-commit.txt','audit.py','cleanup.py'):committed(OUT/n,commit)
 rows=[json.loads(x) for x in gzip.open(OUT/'files.jsonl.gz','rt')];roots=json.loads((OUT/'roots.json').read_text());byroot={r:[] for r in roots}
 for row in rows:byroot[row['root']].append(row)
 missing={r['sha256']:r['size'] for r in rows if r['kind']=='file' and r['git_source'] is None}
 parts=json.loads((OUT/'recovery-parts.json').read_text());whole=hashlib.sha256()
 with tempfile.NamedTemporaryFile(dir=WORK,suffix='.tar.gz') as f:
  for row in parts['parts']:
   assert Path(row['name']).name==row['name'];path=OUT/row['name'];committed(path,commit)
   with path.open('rb') as inp:
    h=hashlib.sha256();n=0
    while True:
     b=inp.read(1024*1024)
     if not b:break
     h.update(b);whole.update(b);n+=len(b);f.write(b)
   assert h.hexdigest()==row['sha256'] and n==row['size']
  assert whole.hexdigest()==parts['archive_sha256'];f.flush();seen=set()
  with tarfile.open(f.name,'r|gz') as t:
   for m in t:
    assert m.isfile()
    with t.extractfile(m) as inp:sha,n=digest(inp)
    assert m.name=='sha256/'+sha and missing[sha]==n and sha not in seen;seen.add(sha)
  assert seen==missing.keys()
 print('Committed recovery verified',len(missing),'unique files',flush=True)
 protected=open_roots(roots);ready={};skipped={}
 for root,entries in byroot.items():
  assert Path(root).parent==Path('/private/tmp') and any(x in Path(root).name.lower() for x in ('i960','doom','mylex'))
  if root in protected:skipped[root]=dict(reason='in use',details=protected[root]);continue
  try:
   actual=tree(root);assert set(actual)=={r['path'] for r in entries},'Tree membership changed'
   for row in entries:
    if row['kind']=='special':raise ValueError('Special file')
    a=actual[row['path']];assert all(row[k]==v for k,v in a.items()),'Metadata changed: '+row['path']
    if row['kind']=='file':
     with Path(row['path']).open('rb') as f:assert digest(f)==(row['sha256'],row['size']),'Content changed: '+row['path']
   ready[root]=actual
  except (AssertionError,ValueError,OSError) as e:skipped[root]=dict(reason=str(e))
 print('Rehashed current roots:',len(ready),'ready;',len(skipped),'retained',flush=True)
 protected=open_roots(roots)
 result=dict(recovery_commit=commit,source_commit=(OUT/'base-commit.txt').read_text().strip(),deleted=[],quarantined={},skipped=skipped,dry_run=not args.delete,disk_free_before=shutil.disk_usage('/private/tmp').free)
 quarantine=WORK/'quarantine';quarantine.mkdir(exist_ok=True)
 for root,expected in ready.items():
  if root in protected:result['skipped'][root]=dict(reason='in use',details=protected[root]);continue
  try:
   assert tree(root)==expected,'Changed after hashing'
   if args.delete:
    dest=quarantine/Path(root).name;assert not dest.exists() and not dest.is_symlink()
    Path(root).rename(dest);result['quarantined'][root]=str(dest)
    if dest.is_symlink() or dest.is_file():dest.unlink()
    else:shutil.rmtree(dest)
    result['quarantined'].pop(root);result['deleted'].append(root)
    (OUT/'deletion.json').write_text(json.dumps(result,indent=2)+'\n')
  except (AssertionError,OSError) as e:result['skipped'][root]=dict(reason=str(e))
 result['disk_free_after']=shutil.disk_usage('/private/tmp').free
 (OUT/('deletion.json' if args.delete else 'dry-run.json')).write_text(json.dumps(result,indent=2)+'\n')
 print('Deleted',len(result['deleted']),'roots; retained',len(result['skipped']),flush=True)
if __name__=='__main__':main()
