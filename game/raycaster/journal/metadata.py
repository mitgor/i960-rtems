"""Bounded intent/result journal; incomplete sessions can never be accepted."""
import hashlib
import json
from pathlib import Path

LIMIT = 8193
MAX_LINE = 16384
HEADER = dict(kind='header', version=1, limit=LIMIT)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

class Metadata:
    def __init__(self, output, mode):
        if mode not in ('rewrite', 'journal'):
            raise ValueError('metadata mode')
        self.output, self.mode = Path(output), mode
        self.ordinal, self.previous = 0, '0' * 64
        self.stream = None
        if mode == 'journal':
            self.stream = (self.output/'metadata-journal.jsonl').open('xb')
            self.append(HEADER)

    def append(self, payload):
        body = [self.ordinal, self.previous, payload]
        digest = hashlib.sha256(canonical(body)).hexdigest()
        line = canonical(body + [digest]) + b'\n'
        if len(line) > MAX_LINE:
            raise ValueError('journal record too large')
        if self.stream.write(line) != len(line):
            raise OSError('short journal write')
        self.stream.flush()
        self.ordinal += 1
        self.previous = digest

    def intent(self, label, data, requests):
        if not 1 <= len(requests) <= LIMIT:
            raise ValueError('request bound exceeded')
        if self.mode == 'journal':
            self.append(dict(kind='intent', sequence=len(requests), label=label, data=data.hex()))
        else:
            (self.output/'browser-requests.json').write_text(json.dumps(requests)+'\n')

    def result(self, row, rows):
        if self.mode == 'journal':
            self.append(dict(kind='result', sequence=row['sequence'], row=row))
        else:
            (self.output/'phases.json').write_text(json.dumps(rows, indent=2)+'\n')

    def finish(self, requests, rows, sequence):
        if len(requests) != len(rows) or len(rows) != sequence or not sequence:
            raise ValueError('unfinished journal')
        if self.mode == 'journal':
            # Compatibility exports are derived once, after verified card CLOSE.
            for name, value in [('browser-requests.json', requests), ('phases.json', rows)]:
                temporary = self.output/(name+'.tmp')
                temporary.write_text(json.dumps(value, indent=2)+'\n')
                temporary.replace(self.output/name)
            self.append(dict(kind='seal', requests=sequence, results=sequence))

    def close(self):
        if self.stream is not None:
            self.stream.close()


def read_journal(path):
    previous = '0'*64
    requests, rows = [], []
    sealed = False
    count = 0
    with Path(path).open('rb') as stream:
        while True:
            line = stream.readline(MAX_LINE+1)
            if not line:
                break
            if sealed or not line.endswith(b'\n') or len(line)>MAX_LINE or count>=2*LIMIT+2:
                raise ValueError('truncated, oversized or trailing journal record')
            item = json.loads(line)
            if not isinstance(item,list) or len(item)!=4 or canonical(item)+b'\n'!=line:
                raise ValueError('noncanonical journal record')
            ordinal, parent, payload, digest = item
            if type(ordinal) is not int or not isinstance(parent,str) or not isinstance(digest,str) or not isinstance(payload,dict):
                raise ValueError('journal record types')
            if ordinal!=count or parent!=previous or digest!=hashlib.sha256(canonical(item[:3])).hexdigest():
                raise ValueError('journal chain')
            if count==0:
                if canonical(payload)!=canonical(HEADER):raise ValueError('journal header')
            elif payload.get('kind')=='intent':
                if set(payload)!= {'kind','sequence','label','data'} or len(requests)!=len(rows) or type(payload['sequence']) is not int or payload['sequence']!=len(requests)+1 or len(requests)>=LIMIT:
                    raise ValueError('intent ordering')
                if not isinstance(payload['label'],str) or not isinstance(payload['data'],str) or len(payload['data'])!=128 or len(bytes.fromhex(payload['data']))!=64:
                    raise ValueError('intent encoding')
                requests.append([payload['label'],payload['data']])
            elif payload.get('kind')=='result':
                if set(payload)!= {'kind','sequence','row'} or len(requests)!=len(rows)+1 or type(payload['sequence']) is not int or payload['sequence']!=len(requests) or not isinstance(payload['row'],dict) or type(payload['row'].get('sequence')) is not int or payload['row'].get('sequence')!=len(requests):
                    raise ValueError('result ordering')
                rows.append(payload['row'])
            elif payload.get('kind')=='seal':
                if not rows or len(rows)!=len(requests) or canonical(payload)!=canonical(dict(kind='seal',requests=len(requests),results=len(rows))):
                    raise ValueError('incomplete seal')
                sealed = True
            else:
                raise ValueError('unknown journal record')
            previous = digest
            count += 1
    if not sealed:
        raise ValueError('journal has no completion seal')
    return requests, rows


def read_metadata(capture):
    capture = Path(capture)
    cfg = json.loads((capture/'queue-test.json').read_text())
    mode = cfg.get('metadata_format', 'rewrite-v1')
    requests = json.loads((capture/'browser-requests.json').read_text())
    rows = json.loads((capture/'phases.json').read_text())
    if mode=='journal-v1' or (capture/'metadata-journal.jsonl').exists():
        if mode!='journal-v1':raise ValueError('journal mode mismatch')
        if read_journal(capture/'metadata-journal.jsonl') != (requests, rows):
            raise ValueError('journal/export mismatch')
    elif mode!='rewrite-v1':
        raise ValueError('unknown metadata format')
    return requests, rows
