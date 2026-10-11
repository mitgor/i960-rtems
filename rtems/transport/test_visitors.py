#!/usr/bin/env python3
import ipaddress
import json
import struct
import tempfile
import unittest
from pathlib import Path
from visitors import VisitorLog, response_identity


def packet(version=6, seq=100, port=12345, status=b'HTTP/1.0 200 OK\r\n', address=None):
    tcp=struct.pack('!HHIIBBHHH',80,port,seq,0,0x50,0x18,4096,0,0)+status
    if version==6:
        return struct.pack('!IHBB',6<<28,len(tcp),6,64)+ipaddress.ip_address('fd96:196:960::2').packed+ipaddress.ip_address(address or '2001:db8::1').packed+tcp
    return struct.pack('!BBHHHBBH',0x45,0,20+len(tcp),0,0,64,6,0)+ipaddress.ip_address('10.196.0.2').packed+ipaddress.ip_address(address or '192.0.2.1').packed+tcp


class Tests(unittest.TestCase):
    def test_retransmissions_restart_and_addresses(self):
        with tempfile.TemporaryDirectory() as directory:
            log=VisitorLog(directory)
            for p in [packet(),bytearray(packet()),bytearray(packet(seq=101)),packet(4),packet(status=b'HTTP/1.0 400 Bad Request\r\n')]:
                log.observe(p)
            log.close()
            log=VisitorLog(directory)
            log.observe(packet())
            stats=json.loads((Path(directory)/'statistics.json').read_text())
            self.assertEqual(stats['unique_visitors'],2)
            self.assertEqual(stats['successful_page_responses'],3)
            self.assertEqual(log.db.execute('SELECT COUNT(*) FROM responses').fetchone()[0],3)
            log.close()

    def test_malformed_and_unrelated(self):
        for version in (4,6):
            p=packet(version)
            for length in range(len(p)):
                self.assertIsNone(response_identity(p[:length]))
            offset=20 if version==4 else 40
            b=bytearray(p);b[offset:offset+2]=struct.pack('!H',9600)
            self.assertIsNone(response_identity(b))
            b=bytearray(p);b[offset+12]=0xf0
            self.assertIsNone(response_identity(b))
        b=bytearray(packet(4));b[6]=0x20
        self.assertIsNone(response_identity(b))
        b=bytearray(packet());b[6]=44
        self.assertIsNone(response_identity(b))

if __name__=='__main__':unittest.main()
