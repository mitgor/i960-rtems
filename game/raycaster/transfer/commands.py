"""Parse exact successful command timing rows, refusing incomplete profiles."""
import re
FIELDS=('gate','input','prepare','submit_log','submit','wait','consume','scan','complete_log','tail')
PATTERN=re.compile(r'CMDPROFILE op=([0-9a-f]+) count=(\d+) offset=([0-9a-f]+) '+ ' '.join(k+r'=(\d+)' for k in FIELDS)+r' total=(\d+)')
def parse(log):
 if 'CMDFAIL' in log:raise ValueError('failed command in timing sample')
 rows=[]
 for match in PATTERN.finditer(log):
  values=match.groups();row=dict(op=int(values[0],16),count=int(values[1]),offset=int(values[2],16))
  row.update(zip(FIELDS+('total',),map(int,values[3:])))
  assert sum(row[k] for k in FIELDS)==row['total']
  rows.append(row)
 assert len(rows)==log.count('CMDPROFILE ')
 assert len(rows)==log.count('submit op=')==log.count('complete op=')
 assert rows and sum(r['op']==0x21 for r in rows)>=3
 return rows
