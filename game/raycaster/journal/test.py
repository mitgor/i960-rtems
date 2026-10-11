#!/usr/bin/env python3
"""Journal truncation, ordering, export integrity and pre/post-execution I/O faults."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
GAME=Path(__file__).resolve().parents[1];sys.path.insert(0,str(GAME))
from journal.metadata import Metadata, read_metadata, read_journal, LIMIT
from browserqueue.backend import AuditedQueue
from browserqueue.test import FakeBoard
from host import request

class Tests(unittest.TestCase):
    def test_complete_and_every_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);m=Metadata(out,'journal');reqs=[['browser-init',bytes(64).hex()]];rows=[dict(sequence=1)]
            m.intent('browser-init',bytes(64),reqs);m.result(rows[0],rows);m.finish(reqs,rows,1);m.close()
            (out/'queue-test.json').write_text(json.dumps(dict(metadata_format='journal-v1')))
            self.assertEqual(read_metadata(out),(reqs,rows))
            raw=(out/'metadata-journal.jsonl').read_bytes();test=out/'mutated'
            for cut in range(len(raw)):
                test.write_bytes(raw[:cut])
                with self.assertRaises(ValueError):read_journal(test)
            for suffix in (b'\n',b'junk',raw.splitlines(keepends=True)[-1]):
                test.write_bytes(raw+suffix)
                with self.assertRaises(ValueError):read_journal(test)
            lines=raw.splitlines(keepends=True)
            for altered in (lines[:1]+lines[2:],lines[:2]+lines[1:],lines[:1]+[lines[2],lines[1]]+lines[3:]):
                test.write_bytes(b''.join(altered))
                with self.assertRaises(ValueError):read_journal(test)
            damaged=bytearray(raw);damaged[raw.index(b'browser-init')]^=1;test.write_bytes(damaged)
            with self.assertRaises(ValueError):read_journal(test)
            (out/'phases.json').write_text('[{"sequence":2}]')
            with self.assertRaises(ValueError):read_metadata(out)

    def test_rehashed_bad_order_is_rejected(self):
        intent=dict(kind='intent',sequence=1,label='browser-init',data=bytes(64).hex())
        result=dict(kind='result',sequence=1,row=dict(sequence=1))
        seal=dict(kind='seal',requests=1,results=1)
        for records in ([result,intent,seal],[intent,intent,result,seal],[intent,seal],[intent,result,dict(kind='seal',requests=2,results=2)]):
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp);m=Metadata(out,'journal')
                for record in records:m.append(record)
                m.close()
                with self.assertRaises(ValueError):read_journal(out/'metadata-journal.jsonl')

    def test_equivalence_and_fixed_growth(self):
        with tempfile.TemporaryDirectory() as tmp:
            exports=[]
            for mode in ('rewrite','journal'):
                out=Path(tmp)/mode;out.mkdir();b=FakeBoard(out);q=AuditedQueue(b,out,17,metadata=mode)
                q.step(request(op=0,columns=0))
                for i in range(80):
                    q.step(request(keys=i%16))
                    if i%13==0:q.step(request(op=0,columns=0))
                q.close();reqs,rows=read_metadata(out);exports.append(reqs)
                self.assertEqual(len(reqs),b.sequence);self.assertEqual(len(rows),b.sequence)
                self.assertEqual(len((out/'metadata-timing.jsonl').read_text().splitlines()),b.sequence)
            self.assertEqual(*exports)

    def test_write_failures_latch_and_leave_unsealed(self):
        for when in ('intent','result','finish'):
            with self.subTest(when=when),tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp);b=FakeBoard(out);q=AuditedQueue(b,out,17)
                q.step(request(op=0,columns=0));start=b.sequence
                if when=='finish':
                    with patch.object(q.metadata,'finish',side_effect=OSError('disk full')):
                        with self.assertRaises(OSError):q.close()
                else:
                    with patch.object(q.metadata,when,side_effect=OSError('disk full')):
                        with self.assertRaises(OSError):q.step(request())
                    self.assertEqual(b.sequence,start+(when=='result'))
                    with self.assertRaises(RuntimeError):q.step(request())
                    q.close()
                self.assertEqual(b.closes,1)
                with self.assertRaises(ValueError):read_journal(out/'metadata-journal.jsonl')

    def test_failed_card_close_never_seals(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);b=FakeBoard(out);q=AuditedQueue(b,out,17);q.step(request(op=0,columns=0))
            with patch.object(b,'close',side_effect=RuntimeError('restoration failed')):
                with self.assertRaises(RuntimeError):q.close()
            with self.assertRaises(ValueError):read_journal(out/'metadata-journal.jsonl')

    def test_limit_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);b=FakeBoard(out);q=AuditedQueue(b,out,17)
            q.requests=[['x',bytes(64).hex()]]*LIMIT
            with self.assertRaises(ValueError):q.step(request(op=0,columns=0))
            self.assertEqual(b.sequence,0);q.close()

if __name__=='__main__':unittest.main()
