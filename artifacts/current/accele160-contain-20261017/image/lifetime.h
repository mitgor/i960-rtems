/* Pure ownership policy, shared by target and native failure tests. */
struct irq_lifetime {unsigned int owner,low,high,frame,pc,ac,vector,live,entries,returns;};
static int lifetime_enter(struct irq_lifetime*s,unsigned int owner,unsigned int frame,
                          unsigned int pc,unsigned int ac,unsigned int vector){
 if(!owner||owner!=s->owner||s->live||s->high<s->low||s->high-s->low<80||
    (frame&15)||frame<s->low+16||frame>s->high-64||!vector)return 0;
 s->frame=frame;s->pc=pc;s->ac=ac;s->vector=vector;s->live=1;s->entries++;return 1;
}
static int lifetime_leave(struct irq_lifetime*s,unsigned int owner,unsigned int frame,
                          unsigned int pc,unsigned int ac,unsigned int vector){
 if(!s->live||owner!=s->owner||frame!=s->frame||pc!=s->pc||ac!=s->ac||vector!=s->vector)return 0;
 s->live=0;s->returns++;return 1;
}
static int lifetime_drained(struct irq_lifetime*s){return !s[0].live&&!s[1].live&&!s[2].live&&s[0].entries==s[0].returns&&s[1].entries==s[1].returns&&s[2].entries==s[2].returns;}
