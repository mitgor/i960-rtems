"""Passive accounting of successful card HTTP responses (one per connection).

Unique visitors are source IP addresses, not people. SQLite is the durable log;
statistics.json is an atomic, human-readable summary regenerated on startup.
"""
import ipaddress
import json
import os
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path


def response_identity(packet):
    """Return visitor and retransmission key, or None. TUN packets have no L2."""
    if not packet:
        return None
    version = packet[0] >> 4
    if version == 4:
        if len(packet) < 20:
            return None
        end = struct.unpack_from('!H', packet, 2)[0]
        offset = (packet[0] & 15) * 4
        if offset < 20 or end > len(packet) or end < offset:
            return None
        if packet[9] != 6 or struct.unpack_from('!H', packet, 6)[0] & 0x3fff:
            return None
        source, destination = packet[12:16], packet[16:20]
    elif version == 6:
        if len(packet) < 40 or packet[6] != 6:
            return None  # Card emits plain TCP; extension/fragment headers ignored.
        offset = 40
        end = 40 + struct.unpack_from('!H', packet, 4)[0]
        if end > len(packet):
            return None
        source, destination = packet[8:24], packet[24:40]
    else:
        return None
    if end < offset + 20:
        return None
    sport, dport, sequence = struct.unpack_from('!HHI', packet, offset)
    header = (packet[offset + 12] >> 4) * 4
    if sport != 80 or header < 20 or offset + header > end:
        return None
    if str(ipaddress.ip_address(bytes(source))) not in ('10.196.0.2', 'fd96:196:960::2'):
        return None
    if not packet[offset + header:end].startswith(b'HTTP/1.0 200 OK\r\n'):
        return None
    visitor = str(ipaddress.ip_address(bytes(destination)))
    return visitor, f'{version}/{visitor}/{dport}/{sequence}'


class VisitorLog:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.directory / 'visitor-log.sqlite3')
        os.chmod(self.directory / 'visitor-log.sqlite3', 0o600)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS responses '
                        '(identity TEXT PRIMARY KEY, address TEXT NOT NULL, utc TEXT NOT NULL)')
        self.db.commit()
        self.summary()

    def observe(self, packet):
        identity = response_identity(packet)
        if identity is None:
            return
        address, key = identity
        now = datetime.now(timezone.utc).isoformat()
        with self.db:
            inserted = self.db.execute('INSERT OR IGNORE INTO responses VALUES (?, ?, ?)',
                                       (key, address, now)).rowcount
        if inserted:
            self.summary()

    def summary(self):
        rows = self.db.execute('SELECT address, COUNT(*), MIN(utc), MAX(utc) '
                               'FROM responses GROUP BY address ORDER BY address').fetchall()
        data = dict(definition='Unique destination IPs of emitted card HTTP 200 responses; not people',
                    updated_utc=datetime.now(timezone.utc).isoformat(),
                    unique_visitors=len(rows), successful_page_responses=sum(r[1] for r in rows),
                    visitors=[dict(ip=r[0],responses=r[1],first_seen=r[2],last_seen=r[3]) for r in rows])
        temp = self.directory / 'statistics.json.tmp'
        with temp.open('w') as f:
            os.chmod(temp, 0o600)
            json.dump(data, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        temp.replace(self.directory / 'statistics.json')

    def close(self):
        self.db.close()
