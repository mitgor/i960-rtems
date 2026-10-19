#!/usr/bin/env python3
"""Explicit, reversible host route/proxy-NDP for the card's compiled IPv6.
Does not configure the upstream router or claim external reachability.
Only the designated card's HTTP and ICMPv6 are admitted from the LAN.
"""
import argparse,ipaddress,json,subprocess,time
from pathlib import Path
STATE=Path('/run/i960-public-ipv6.json')
TABLE='i960_card_public'
def run(*args):return subprocess.check_output(args,text=True).strip()
def sysctl(key,value=None):
 return run('sysctl','-n',key) if value is None else run('sysctl','-q','-w',key+'='+str(value))
def apply(address,lan,tun):
 ip=ipaddress.IPv6Address(address)
 if not ip.is_global:raise ValueError('global unicast required')
 if STATE.exists():raise RuntimeError('existing routing state; remove first')
 for dev in (lan,tun):
  if not dev.replace('_','').replace('-','').isalnum():raise ValueError('invalid interface')
 info=json.loads(run('ip','-j','-6','addr','show','dev',lan))
 if not any(ip in ipaddress.ip_network(a['local']+'/'+str(a['prefixlen']),strict=False) for d in info for a in d['addr_info'] if a['scope']=='global'):
  raise ValueError('card address must belong to current LAN prefix')
 # Never replace an existing route/address/table. DAD is checked before proxying.
 if run('ip','-6','route','show','exact',str(ip)+'/128'):raise RuntimeError('existing /128 route')
 tables=json.loads(run('nft','-j','list','tables'))['nftables']
 if any(x.get('table',{}).get('name')==TABLE for x in tables):raise RuntimeError('existing table')
 if sysctl('net.ipv6.conf.all.forwarding')!='0':raise RuntimeError('existing IPv6 router requires a reviewed policy')
 forwarding=['net.ipv6.conf.'+d['ifname']+'.forwarding' for d in json.loads(run('ip','-j','link','show'))]
 keys=['net.ipv6.conf.'+lan+'.accept_ra','net.ipv6.conf.'+lan+'.forwarding',
       'net.ipv6.conf.'+tun+'.forwarding','net.ipv6.conf.'+lan+'.proxy_ndp']
 keys=['net.ipv6.conf.all.forwarding','net.ipv6.conf.default.forwarding','net.ipv6.conf.all.proxy_ndp']+keys+forwarding
 keys=list(dict.fromkeys(keys))
 state=dict(address=str(ip),lan=lan,tun=tun,sysctls={k:sysctl(k) for k in keys},dad=False,table=False,route=False,proxy=False)
 def save():STATE.write_text(json.dumps(state,indent=2)+'\n')
 save()
 try:
  run('ip','-6','addr','add',str(ip)+'/128','dev',lan);state['dad']=True;save()
  for _ in range(50):
   addresses=json.loads(run('ip','-j','-6','addr','show','dev',lan))[0]['addr_info']
   item=next(a for a in addresses if a['local']==str(ip))
   flags=item.get('flags',[])
   if item.get('dadfailed') or 'dadfailed' in flags:raise RuntimeError('duplicate address')
   if not item.get('tentative') and 'tentative' not in flags:break
   time.sleep(.1)
  else:raise RuntimeError('DAD timeout')
  run('ip','-6','addr','del',str(ip)+'/128','dev',lan);state['dad']=False;save()
  rules=f'''table ip6 {TABLE} {{
 chain forward {{ type filter hook forward priority -10; policy accept;
  iifname "{lan}" oifname != "{tun}" drop
  iifname "{lan}" oifname "{tun}" ip6 daddr != {ip} drop
  iifname "{lan}" oifname "{tun}" ct state established,related accept
  iifname "{lan}" oifname "{tun}" ip6 daddr {ip} meta l4proto ipv6-icmp accept
  iifname "{lan}" oifname "{tun}" ip6 daddr {ip} tcp dport 80 accept
  iifname "{lan}" oifname "{tun}" drop
  iifname "{tun}" ip6 saddr {ip} accept
  counter drop
 }}
}}'''
  subprocess.run(['nft','-f','-'],input=rules,text=True,check=True);state['table']=True;save()
  # Keep accepting RA/default-route refresh after enabling router behaviour.
  sysctl('net.ipv6.conf.'+lan+'.accept_ra',2)
  sysctl('net.ipv6.conf.all.forwarding',1)
  # The global write changes interface defaults: preserve unrelated interfaces.
  for k in forwarding:
   sysctl(k,1 if k in ('net.ipv6.conf.'+lan+'.forwarding','net.ipv6.conf.'+tun+'.forwarding') else state['sysctls'][k])
  sysctl('net.ipv6.conf.default.forwarding',state['sysctls']['net.ipv6.conf.default.forwarding'])
  sysctl('net.ipv6.conf.all.proxy_ndp',1);sysctl('net.ipv6.conf.'+lan+'.proxy_ndp',1)
  run('ip','-6','route','add',str(ip)+'/128','dev',tun);state['route']=True;save()
  run('ip','-6','neigh','add','proxy',str(ip),'dev',lan);state['proxy']=True;save()
 except BaseException:
  remove();raise
 return state

def remove():
 if not STATE.exists():return
 s=json.loads(STATE.read_text());ip=s['address'];lan=s['lan'];tun=s['tun']
 # On failure keep state for explicit repair; never flush unrelated rules.
 if s['proxy']:run('ip','-6','neigh','del','proxy',ip,'dev',lan);s['proxy']=False;STATE.write_text(json.dumps(s))
 if s['route']:run('ip','-6','route','del',ip+'/128','dev',tun);s['route']=False;STATE.write_text(json.dumps(s))
 for k,v in s['sysctls'].items():sysctl(k,v)
 if s['table']:run('nft','delete','table','ip6',TABLE);s['table']=False;STATE.write_text(json.dumps(s))
 if s['dad']:run('ip','-6','addr','del',ip+'/128','dev',lan)
 STATE.unlink()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=('apply','remove'));p.add_argument('--address');p.add_argument('--lan',default='enp1s0');p.add_argument('--tun',default='accele0');a=p.parse_args()
 if a.action=='apply':print(json.dumps(apply(a.address,a.lan,a.tun),indent=2))
 else:remove()
