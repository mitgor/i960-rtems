/* One-shot stock IOCTL 0x8f observation. No DMA buffer, SGE, flash write,
 * reset or unbind. A pending job pins this module indefinitely; never cancel
 * the underlying myrs_exec_cmd wait or reuse its command block on timeout.
 */
static char *probe_bdf = "";
module_param(probe_bdf, charp, 0444);
static DEFINE_MUTEX(unsupported_lock);
static struct work_struct unsupported_work;
static struct myrs_hba *unsupported_cs;
static int unsupported_state, unsupported_status, unsupported_residual;
static u8 unsupported_mailbox[64];

static void unsupported_worker(struct work_struct *work)
{
 struct myrs_hba *cs = unsupported_cs;
 struct myrs_cmdblk *cmd = &cs->dcmd_blk;
 u8 *raw = (u8 *)&cmd->mbox;
 mutex_lock(&cs->dcmd_mutex);
 myrs_reset_cmd(cmd);
 cmd->mbox.common.id = MYRS_DCMD_TAG;
 cmd->mbox.common.opcode = MYRS_CMD_OP_IOCTL;
 cmd->mbox.common.control.no_autosense = true;
 raw[21] = 0x8f;
 memcpy(unsupported_mailbox, raw, sizeof(unsupported_mailbox));
 myrs_exec_cmd(cs, cmd);
 unsupported_status = cmd->status;
 unsupported_residual = cmd->residual;
 mutex_unlock(&cs->dcmd_mutex);
 mutex_lock(&unsupported_lock);
 unsupported_state = 2;
 mutex_unlock(&unsupported_lock);
}

static ssize_t stock_unsupported_show(struct device *dev,
 struct device_attribute *attr, char *buf)
{
 int n, i;
 mutex_lock(&unsupported_lock);
 n = sysfs_emit(buf, "state=%d status=%d residual=%d\n",
  unsupported_state, unsupported_status, unsupported_residual);
 if (unsupported_state == 2) {
  n += sysfs_emit_at(buf, n, "mailbox=");
  for (i = 0; i < sizeof(unsupported_mailbox); ++i)
   n += sysfs_emit_at(buf, n, "%02x", unsupported_mailbox[i]);
  n += sysfs_emit_at(buf, n, "\n");
 }
 mutex_unlock(&unsupported_lock);
 return n;
}

static ssize_t stock_unsupported_store(struct device *dev,
 struct device_attribute *attr, const char *buf, size_t count)
{
 struct myrs_hba *cs = shost_priv(class_to_shost(dev));
 int rc = 0;
 mutex_lock(&unsupported_lock);
 if (sysfs_streq(buf, "clear")) {
  if (unsupported_state == 1) { rc = -EBUSY; goto out; }
  if (unsupported_state == 2) {
   flush_work(&unsupported_work);
   unsupported_state = 0;
   unsupported_cs = NULL;
   module_put(THIS_MODULE);
  }
 } else if (sysfs_streq(buf, "probe")) {
  if (unsupported_state) { rc = -EBUSY; goto out; }
  unsupported_cs = cs;
  unsupported_state = 1;
  unsupported_status = -1;
  unsupported_residual = -1;
  memset(unsupported_mailbox, 0, sizeof(unsupported_mailbox));
  __module_get(THIS_MODULE);
  INIT_WORK(&unsupported_work, unsupported_worker);
  schedule_work(&unsupported_work);
 } else rc = -EINVAL;
out:
 mutex_unlock(&unsupported_lock);
 return rc ? rc : count;
}
static DEVICE_ATTR_RW(stock_unsupported);
