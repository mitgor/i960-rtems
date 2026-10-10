"""Small, shared adaptations to the pinned lwIP 2.1.3 source tree."""
def apply(root):
 p=root/'src/core/dns.c';s=p.read_text();s=s.replace('struct dns_answer {','struct __attribute__((packed)) dns_answer {');p.write_text(s)
 p=root/'src/core/udp.c';s=p.read_text()
 marker='/* i960 profile: IPv6 UDP always requires a nonzero checksum. */'
 old='        if (udphdr->chksum != 0) {'
 if marker not in s:
  assert s.count(old)==1
  s=s.replace(old,'        '+marker+'\n        if (IP_IS_V6(ip_current_dest_addr()) && udphdr->chksum == 0) {\n          goto chkerr;\n        }\n'+old)
 p.write_text(s)
