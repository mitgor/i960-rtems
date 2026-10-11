#!/usr/bin/env python3
"""Generate exact-image-pinned autonomous module with a one-shot MU echo ioctl."""
import argparse,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('auto_builder',HERE.parent/'autonomous/build_transport.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args()
m.build(a.out,a.payload)
p=a.out/'dac960auto.c';s=p.read_text().replace('bool output_valid, irq_may_run;','bool output_valid, irq_may_run, mu_used;')
# A private helper captures d while sharing the exact loop with native tests.
helper=(HERE/'mu_host.h').read_text().replace('mu_exchange(unsigned int *words)','mu_exchange(struct experiment *d,unsigned int *words)')
helper='#define MU_READ(off) readl(d->bar+(off))\n#define MU_WRITE(off,v) writel((v),d->bar+(off))\n#define MU_PAUSE() usleep_range(1000,1500)\n'+helper+'\n#undef MU_READ\n#undef MU_WRITE\n#undef MU_PAUSE\n'
helper+='''
static long mu_ioctl(struct file *file,unsigned int cmd,unsigned long arg)
{
 struct experiment *d=file->private_data;unsigned int words[8];int rc;
 if(cmd!=0xc0204d01u)return -ENOTTY;
 if(copy_from_user(words,(void __user*)arg,sizeof(words)))return -EFAULT;
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->ready||d->pending||d->runner_uncertain||
    !d->irq_may_run||d->response_ready||d->steps!=1||d->sequence!=1||d->mu_used){rc=-EBUSY;goto out;}
 d->mu_used=true;words[2]=d->sequence;
 rc=mu_exchange(d,words);words[3]=d->sequence;
 record(d,"MU echo rc=%d request=%08x response=%08x sequence=%u/%u\\n",rc,words[0],words[1],words[2],words[3]);
 session_log_end(d);
 if(copy_to_user((void __user*)arg,words,sizeof(words)))rc=-EFAULT;
 out:mutex_unlock(&d->session_lock);return rc;
}
'''
assert 'static const struct file_operations session_fops=' in s
s=s.replace('static const struct file_operations session_fops=',helper+'\nstatic const struct file_operations session_fops=').replace('.owner=THIS_MODULE,.open=session_file_open,','.owner=THIS_MODULE,.unlocked_ioctl=mu_ioctl,.open=session_file_open,')
p.write_text(s)

p=a.out/'stage_rehearsal.h';s=p.read_text()
cleanup=(HERE/'mu_cleanup.h').read_text().replace('mu_cleanup(unsigned int owned,unsigned int used)', 'mu_cleanup(struct experiment *d,unsigned int owned,unsigned int used)')
cleanup='#define MU_READ(off) readl(d->bar+(off))\n#define MU_WRITE(off,v) writel((v),d->bar+(off))\n'+cleanup+'\n#undef MU_READ\n#undef MU_WRITE\n'
s=s.replace('static int autonomous_stop(',cleanup+'\nstatic int autonomous_stop(')
s=s.replace('    d->irq_may_run=false;','''    rc=mu_cleanup(d,bio_word(d->stage[6].data+n+8)==0x4d554f4bu,d->mu_used);
    if(rc)return rc;
    record(d,"MU message words/masks/pending restored by target plus host OISR ack\\n");
    d->irq_may_run=false;''')
p.write_text(s)
