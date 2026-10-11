"""Opt-in same-slot ACK+PUBLISH; preserve the accepted original queue source."""
def once(s,old,new):
 assert s.count(old)==1,old
 return s.replace(old,new)

def combined(s):
 s=once(s,'if(op>3||slot>1||!epoch||fq_word(in+20)||fq_word(in+24)||fq_word(in+28))',
        'if(op>4||slot>1||!epoch||(op!=4&&fq_word(in+20))||fq_word(in+24)||fq_word(in+28))')
 s=once(s,'if(op!=1){','if(op!=1&&op!=4){')
 s=once(s,'if(op==1){','if(op==1||op==4){')
 s=once(s,'   if(s->mask&(1u<<slot)){status=FQ_BUSY;goto done;}', '''   if(op==4){
    /* All request/publication checks precede any change. Replace this exact
     * acknowledged slot; the other slot stays byte-for-byte unchanged.
     * No separate ACK commit: READY is cleared only when publication begins.
     * Hardware failure after that boundary is uncertain, never retryable. */
    if(!(s->mask&(1u<<slot))||fq_word(in+20)!=s->gen[slot]){status=FQ_STALE;goto done;}
   }else if(s->mask&(1u<<slot)){status=FQ_BUSY;goto done;}''')
 return s
