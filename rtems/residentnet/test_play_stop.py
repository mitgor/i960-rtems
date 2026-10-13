#!/usr/bin/env python3
"""Run the actual nested play service against STOP/WAD teardown races, offline.

Extract only the service function so tests need no HTTP server, WAD or card.
Its nonlocal declarations become globals in an isolated per-test namespace;
all executable service statements come directly from play_client.py.
"""
import ast
from pathlib import Path
import threading
import unittest
from types import SimpleNamespace

SOURCE = Path(__file__).with_name('play_client.py')


def service_namespace(*, requested=True, sent=False, records=1, owner=True):
    tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef) and node.name == 'serve']
    assert len(functions) == 1
    function = functions[0]
    for i, node in enumerate(function.body):
        if isinstance(node, ast.Nonlocal):
            function.body[i] = ast.copy_location(ast.Global(names=node.names), node)
    calls = []
    stop = threading.Event()
    if requested:
        stop.set()

    def query():
        calls.append('query')
        return [0, 7, int(owner)]

    def request(generation):
        assert generation == 7
        calls.append('stop')

    def wad_serve():
        calls.append('wad')
        if sent or 'stop' in calls:
            raise AssertionError('WAD ioctl after STOP races a canceled loan')
        return True

    def frame_control(*args):
        raise AssertionError('frame ioctl after STOP races frame teardown')

    namespace = dict(stop=stop, stop_sent=sent, seen=0, request_base=0,
                     server=SimpleNamespace(records=[None] * records, serve=wad_serve),
                     control=SimpleNamespace(query=query, request=request),
                     ctl=frame_control, calls=calls)
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(module, str(SOURCE), 'exec'), namespace)
    return namespace


class StopServiceTests(unittest.TestCase):
    def test_request_suppresses_wad_and_frame_in_same_iteration(self):
        scope = service_namespace()
        self.assertIs(scope['serve'](), False)
        self.assertEqual(scope['calls'], ['query', 'stop'])
        self.assertTrue(scope['stop_sent'])
        # Subsequent polls must only permit Upload.command's completion query.
        self.assertIs(scope['serve'](), False)
        self.assertEqual(scope['calls'], ['query', 'stop'])

    def test_already_sent_stop_suppresses_all_new_work(self):
        scope = service_namespace(sent=True)
        self.assertIs(scope['serve'](), False)
        self.assertEqual(scope['calls'], [])

    def test_early_stop_waits_for_initialization(self):
        scope = service_namespace(records=0)
        self.assertIs(scope['serve'](), True)
        self.assertEqual(scope['calls'], ['wad'])
        self.assertFalse(scope['stop_sent'])

    def test_inactive_owner_is_not_canceled(self):
        scope = service_namespace(owner=False)
        self.assertIs(scope['serve'](), True)
        self.assertEqual(scope['calls'], ['query', 'wad'])
        self.assertFalse(scope['stop_sent'])

    def test_normal_startup_continues_wad_service(self):
        scope = service_namespace(requested=False)
        self.assertIs(scope['serve'](), True)
        self.assertEqual(scope['calls'], ['wad'])


if __name__ == '__main__':
    unittest.main()
