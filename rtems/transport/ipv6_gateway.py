"""Static IPv6 TUN addressing and optional, narrowly scoped NAT66 gateway.

The point-to-point link carries IP packets directly; Ethernet ND is unnecessary.
IPv6 routing is opt-in and has a separate, atomic cleanup journal.
"""
import ipaddress,json,re,subprocess
from pathlib import Path
CONF=Path('/proc/sys/net/ipv6/conf')
IFACE='i960rt0';HOST6='fd96:196:960::1';CARD6='fd96:196:960::2';NET6=ipaddress.ip_network('fd96:196:960::/64')
def command(*args):return subprocess.check_output(args,text=True)
def journal(path,value):
 temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)
def rule_shapes(uplink):
 if not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,15}',uplink):raise ValueError('invalid uplink')
 return [
  ['ip6tables','-t','filter','-D','FORWARD','-o',IFACE,'-j','DROP'],
  ['ip6tables','-t','filter','-D','FORWARD','-o',IFACE,'-d',CARD6,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT'],
  ['ip6tables','-t','filter','-D','FORWARD','-i',IFACE,'-s',CARD6,'-o',uplink,'-j','ACCEPT'],
  ['ip6tables','-t','nat','-D','POSTROUTING','-s',CARD6+'/128','-o',uplink,'-j','MASQUERADE']]
def published_rules(uplink,address,port):
 address=str(ipaddress.IPv6Address(address))
 if not ipaddress.IPv6Address(address).is_global or not 1024<=port<=65535:raise ValueError('global address and unprivileged port required')
 rule_shapes(uplink) # Validate interface before constructing commands.
 return [
  ['ip6tables','-t','filter','-D','FORWARD','-i',uplink,'-o',IFACE,'-d',CARD6,'-p','tcp','--dport','80','-j','ACCEPT'],
  ['ip6tables','-t','nat','-D','PREROUTING','-i',uplink,'-d',address+'/128','-p','tcp','--dport',str(port),'-j','DNAT','--to-destination','['+CARD6+']:80']]
def cleanup(output):
 path=output/'ipv6-gateway-journal.json'
 if not path.exists():return
 j=json.loads(path.read_text());allowed=rule_shapes(j['uplink']) if j['uplink'] else []
 if j.get('published'):allowed+=published_rules(j['uplink'],j['published']['address'],j['published']['port'])
 for cmd in j['undo']:
  if cmd not in allowed:raise ValueError('unexpected IPv6 journal rule')
 for row in j['sysctls']:
  rel=row['path'];parts=rel.split('/')
  if len(parts)!=2 or not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,15}',parts[0]) or parts[1] not in ('accept_ra','forwarding') or row['before'] not in ('0','1','2'):raise ValueError('unexpected IPv6 journal sysctl')
 for cmd in reversed(j['undo']):
  check=cmd[:];check[3]='-C'
  if subprocess.run(check,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:subprocess.run(cmd,check=True)
 # Restore all/forwarding first, then per-interface values which it may propagate.
 rows=sorted(j['sysctls'],key=lambda row:row['path']!='all/forwarding')
 for row in rows:
  target=CONF/row['path']
  if target.exists():target.write_text(row['before']+'\n')
 (output/'ip6tables-after.txt').write_text(command('ip6tables-save'))
 (output/'ipv6-routes-after.json').write_text(command('ip','-6','-j','route'))
 journal(output/'ipv6-cleanup.json',dict(clean=True,sysctls=[dict(path=r['path'],value=(CONF/r['path']).read_text().strip()) for r in rows if (CONF/r['path']).exists()]))
class IPv6Gateway:
 def __init__(self,output,internet=False):
  self.output=output;j=dict(uplink=None,undo=[],sysctls=[]);path=output/'ipv6-gateway-journal.json'
  routes=json.loads(command('ip','-6','-j','route'));(output/'ipv6-routes-before.json').write_text(json.dumps(routes,indent=2)+'\n')
  firewall=command('ip6tables-save');(output/'ip6tables-before.txt').write_text(firewall)
  if IFACE in firewall or CARD6 in firewall:raise RuntimeError('stale IPv6 project firewall rules')
  for route in routes:
   dst=route.get('dst','default')
   if dst!='default' and ipaddress.ip_network(dst,strict=False).overlaps(NET6):raise RuntimeError('IPv6 test subnet overlaps an existing route')
  journal(path,j)
  try:
   command('ip','link','set','dev',IFACE,'addrgenmode','none')
   command('ip','-6','addr','add',HOST6+'/64','dev',IFACE,'nodad')
   if internet:
    uplinks={r['dev'] for r in routes if r.get('dst')=='default'}
    if len(uplinks)!=1:raise RuntimeError('one working IPv6 default uplink required')
    uplink=uplinks.pop();j['uplink']=uplink
    conf=CONF
    j['sysctls']=[dict(path=str(p.relative_to(conf)),before=p.read_text().strip()) for p in sorted(conf.glob('*/forwarding'))]
    j['sysctls'].append(dict(path=uplink+'/accept_ra',before=(conf/uplink/'accept_ra').read_text().strip()));journal(path,j)
    # Preserve reception of router advertisements while forwarding is enabled.
    (conf/uplink/'accept_ra').write_text('2\n')
    for undo in rule_shapes(uplink):
     j['undo'].append(undo);journal(path,j)
     install=undo[:];install[3]='-I';command(*install)
    (conf/'all/forwarding').write_text('1\n')
  except BaseException:cleanup(output);raise
 def publish_http(self,address,port):
  path=self.output/'ipv6-gateway-journal.json';j=json.loads(path.read_text())
  if not j['uplink']:raise ValueError('publishing requires --internet6')
  address=str(ipaddress.IPv6Address(address));rules=published_rules(j['uplink'],address,port)
  addresses=json.loads(command('ip','-6','-j','addr','show','dev',j['uplink']))
  if not any(a.get('local')==address and not a.get('tentative') and not a.get('dadfailed') for interface in addresses for a in interface.get('addr_info',[])):raise ValueError('published address is not assigned to uplink')
  if command('ss','-H','-ltn','sport','=',str(port)).strip():raise ValueError('host TCP port is already listening')
  j['published']=dict(address=address,port=port);journal(path,j)
  for undo in rules:
   j['undo'].append(undo);journal(path,j);install=undo[:];install[3]='-I';command(*install)
  journal(self.output/'published-http.json',dict(url='http://['+address+']:'+str(port)+'/',card=CARD6,card_port=80,transport='IPv6 DNAT, HTTP served by card'))
 def close(self):
  (self.output/'ip6tables-active.txt').write_text(command('ip6tables-save','-c'));cleanup(self.output)
