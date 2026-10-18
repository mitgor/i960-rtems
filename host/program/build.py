#!/usr/bin/env python3
"""Generate a fixed one-shot module. Generation neither connects nor programs."""
from pathlib import Path
import argparse,hashlib,importlib.util,shutil
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT))
from card_profiles import require_workflow
HERE=Path(__file__).resolve().parent
SHA='a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError(f'base source changed: expected exactly one {old[:80]!r}')
    return s.replace(old,new,1)

def build(out):
    if out.exists(): raise ValueError('output must be a new directory')
    spec=importlib.util.spec_from_file_location('cpu_builder',ROOT/'loader/staging-cpu/build_probe.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    binary=ROOT/'artifacts/programming-preflight-20261010/build/probe.bin'
    mod.build(binary,out)
    for name in ['one_shot.h','program_kernel.h']: shutil.copyfile(HERE/name,out/name)
    p=out/'dac960dump.c';s=p.read_text()
    s=replace(s,'#include <crypto/hash.h>','#include <crypto/hash.h>\n#include <linux/workqueue.h>\n#include "one_shot.h"')
    s=replace(s,'static bool stage_check;',f'''#define PROGRAM_CANDIDATE_SHA "{SHA}"
static bool program_enable;
static char *program_token = "";
module_param(program_enable, bool, 0444);
module_param(program_token, charp, 0400);
MODULE_PARM_DESC(program_enable, "Irreversible: one 2B/1 program after full preflight; default false rehearses and restores RAM");
MODULE_PARM_DESC(program_token, "Must equal exact candidate SHA256 for programming");
static bool stage_check;''')
    s=replace(s,'    struct pci_dev *pdev;','''    struct po_state program;
    struct work_struct program_work;
    u32 worker_state; /* 0=rehearsal, 1=running, 2=finished; see result for outcome */
    struct pci_dev *pdev;''')
    s=replace(s,'    if (d->pending) return -EPERM;','''    if (d->pending) return -EPERM;
    if (d->program.submitted && opcode != 0x20 && opcode != 0x1c) return -EPERM;''')
    s=replace(s,'static const struct pci_device_id ids[] = {','''static void program_worker(struct work_struct *work)
{
    struct experiment *d = container_of(work, struct experiment, program_work);
    int rc = run(d);
    record(d, "experiment-result=%d pending=%u stage-dirty=%u exec-dirty=%u\\n",
           rc, d->pending, d->stage_dirty, d->exec_dirty);
    record(d, "worker finished: program-state=%u submitted=%d completed=%d verified=%d; module retained until reboot\\n",
           d->program.phase, d->program.submitted, d->program.completed, d->program.verified);
    /* Keep module/device/resources pinned for every enabled run, including
     * preflight failure. This avoids releasing module text inside its worker. */
    smp_wmb();
    WRITE_ONCE(d->result_blob.size, d->used);
    WRITE_ONCE(d->worker_state, 2);
}

static const struct pci_device_id ids[] = {''')
    s=replace(s,'    if (!stage_check) return -EINVAL; /* fixed combined rehearsal only */','''    if (!stage_check) return -EINVAL; /* fixed combined rehearsal only */
    if (program_enable && strcmp(program_token, PROGRAM_CANDIDATE_SHA)) return -EPERM;
    if (!program_enable && program_token[0]) return -EINVAL;''')
    start=s.index('    rc = run(d);',s.index('static int probe('))
    end=s.index('    /* Even a negative experiment',start)
    old=s[start:end]
    s=s[:start]+'''    if (!program_enable) {
'''+old+'''    }
'''+s[end:]
    s=replace(s,'    return 0;\n free_dma:','''    if (program_enable) {
        __module_get(THIS_MODULE);
        pci_dev_get(pdev);
        d->pinned = true;
        d->worker_state = 1;
        debugfs_create_u32("worker-state", 0400, d->directory, &d->worker_state);
        INIT_WORK(&d->program_work, program_worker);
        schedule_work(&d->program_work);
    }
    return 0;
 free_dma:''')
    # Reuse the last two image slots for fresh flash in enabled runs.
    s=replace(s,'            debugfs_create_blob(stage_names[i], 0400, d->directory, &d->stage[i].blob);','''            debugfs_create_blob(program_enable && i >= 4 ?
                (i == 4 ? "flash-readback-a5.bin" : "flash-readback-5a.bin") :
                stage_names[i], 0400, d->directory, &d->stage[i].blob);''')
    # remove() can be called through sysfs despite a module refcount.
    mark=s.index('static void remove(')
    before,after=s[:mark],s[mark:]
    after=replace(after,'if (d->pending || d->scratch_dirty || d->exec_dirty || d->stage_dirty)',
                  'if (program_enable || d->pending || d->scratch_dirty || d->exec_dirty || d->stage_dirty)')
    s=before+after
    s=replace(s,'module_pci_driver(dac960dump_driver);','''static int __init program_init(void)
{
    if (!stage_check || !runtime_check || !pointer_check || attempt ||
        scratch_check || dram_hook_check || rom_table_check || rom_exec_check || flash_map_check)
        return -EINVAL;
    if (program_enable && strcmp(program_token, PROGRAM_CANDIDATE_SHA)) return -EPERM;
    if (!program_enable && program_token[0]) return -EINVAL;
    return pci_register_driver(&dac960dump_driver);
}
static void __exit program_exit(void) { pci_unregister_driver(&dac960dump_driver); }
module_init(program_init);
module_exit(program_exit);''')
    p.write_text(s)
    p=out/'stage_rehearsal.h';s=p.read_text()
    s=replace(s,'static int run_stage(struct experiment *d)','#include "program_kernel.h"\n\nstatic int run_stage(struct experiment *d)')
    s=replace(s,'    if (d->pending || d->exec_dirty) goto done;','''    if (d->pending || d->exec_dirty) goto done;
    if (!rc) rc = run_program_once(d);
    if (d->program.submitted) goto done; /* Never restore possibly freed staging. */''')
    p.write_text(s)
    shutil.copyfile(binary,out/'probe.bin')
    print(f'Generated {out}; program_enable defaults to false')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--card-profile',default='dac960pg')
    args=parser.parse_args()
    profile=require_workflow(args.card_profile,'firmware_one_shot')
    if profile['firmware']['one_shot_candidate_sha256']!=SHA:
        parser.error('one-shot candidate differs from card profile')
    build(args.out)
