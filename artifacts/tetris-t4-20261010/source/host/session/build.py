#!/usr/bin/env python3
"""Generate persistent-session module using the audited loadrun transport."""
import sys,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'loadrun'))
from build import build as baseline,replace

def build(out):
    baseline(out)
    p=out/'stage_rehearsal.h';s=p.read_text()
    s=s[:s.index('static int run_stage(')]+(HERE/'transaction.h').read_text()
    a=s.index('static int load_output(');b=s.index('/* Persistent BIO1',a)
    helper=s[a:b].replace('load_output(struct experiment *d)','session_output(struct experiment *d,unsigned int length)').replace('IMAGE_WINDOW','length')
    s=s[:a]+helper+s[b:];p.write_text(s)
    p=out/'dac960loadrun.c';s=p.read_text()
    s=replace(s,'#include <linux/firmware.h>','#include <linux/firmware.h>\n#include <linux/miscdevice.h>\n#include <linux/mutex.h>\n#include <linux/uaccess.h>\n#include <linux/kref.h>')
    s=replace(s,'    const struct firmware *payload;','''    struct kref refs;
    struct mutex session_lock;
    struct miscdevice misc;
    bool owned, removed, ready, runner_uncertain, response_ready;
    u32 sequence, steps, output_length;
    bool output_valid;
    const struct firmware *payload;''')
    s=replace(s,'static int probe(struct pci_dev *pdev, const struct pci_device_id *id)',(HERE/'fileops.h').read_text()+'\nstatic int probe(struct pci_dev *pdev, const struct pci_device_id *id)')
    s=replace(s,'    d->pdev = pdev;','    d->pdev = pdev;\n    mutex_init(&d->session_lock);\n    kref_init(&d->refs);')
    s=replace(s,'    return 0;\n free_dma:','''    if(!rc && !d->pinned) {
        d->misc.minor=MISC_DYNAMIC_MINOR;d->misc.name="i960-session";
        d->misc.fops=&session_fops;d->misc.mode=0600;
        rc=misc_register(&d->misc);
        if(rc) record(d,"misc_register failed=%d\\n",rc);
        else d->misc_registered=true;
    }
    return 0;
 free_dma:''')
    s=replace(s,'    bool owned, removed, ready, runner_uncertain, response_ready;', '    bool owned, removed, ready, runner_uncertain, response_ready, misc_registered;')
    a=s.index('static void remove(struct pci_dev *pdev)');b=s.index('static struct pci_driver',a)
    s=s[:a]+"""static void remove(struct pci_dev *pdev)
{
    struct experiment *d=pci_get_drvdata(pdev);
    if(d->misc_registered) misc_deregister(&d->misc);
    mutex_lock(&d->session_lock);
    if(d->owned && !d->pinned) {session_close(d);session_pin(d);}
    d->removed=true;
    debugfs_remove_recursive(d->directory);
    if(d->pending || d->exec_dirty || d->stage_dirty) {
        session_pin(d);mutex_unlock(&d->session_lock);return;
    }
    writel(d->saved_irq,d->bar+IRQMASK);readl(d->bar+IRQMASK);
    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);
    pci_iounmap(pdev,d->bar);pci_release_regions(pdev);pci_disable_device(pdev);
    pci_write_config_word(pdev,PCI_COMMAND,d->saved_command);
    mutex_unlock(&d->session_lock);kref_put(&d->refs,session_free);
}
"""+s[b:]
    s=replace(s,'    if (!firmware_name || !stage_check', '    if (!buffer_io || !firmware_name || !stage_check')
    s=s.replace('dac960loadrun','dac960session')
    (out/'dac960session.c').write_text(s);p.unlink()
    p=out/'Makefile';p.write_text(p.read_text().replace('dac960loadrun','dac960session'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
