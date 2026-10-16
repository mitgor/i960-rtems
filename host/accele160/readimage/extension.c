/* Read-only protocol experiment: only the vendor's 1 KiB descriptor read.
 * Loaded only for one explicitly selected 1069:0050/1069:0054 device.
 * A pending job pins the module and DMA buffer; never cancel/free on timeout.
 */
static char *read_bdf = "";
module_param(read_bdf, charp, 0444);
static DEFINE_MUTEX(image_lock);
static struct work_struct image_work;
static struct myrs_hba *image_cs;
static void *image_buf;
static dma_addr_t image_dma;
static int image_state, image_status, image_residual;

static void image_worker(struct work_struct *work)
{
 struct myrs_hba *cs = image_cs;
 struct myrs_cmdblk *cmd = &cs->dcmd_blk;
 u8 *raw = (u8 *)&cmd->mbox;
 mutex_lock(&cs->dcmd_mutex);
 myrs_reset_cmd(cmd);
 cmd->mbox.common.id = MYRS_DCMD_TAG;
 raw[2] = 0x20;
 /* Vendor ReadImage uses control=0, no sense address, sense length 0x40.
  * Use Linux no_autosense with no sense buffer; data direction is read.
  */
 cmd->mbox.common.control.dma_ctrl_to_host = true;
 cmd->mbox.common.control.no_autosense = true;
 cmd->mbox.common.dma_size = 1024;
 raw[21] = 0x2d;
 raw[22] = 0x0e;
 cmd->mbox.common.dma_addr.sge[0].sge_addr = image_dma;
 cmd->mbox.common.dma_addr.sge[0].sge_count = 1024;
 /* Existing driver waits for completion while command and DMA stay alive.
  * Userspace polls asynchronously with a bounded deadline. No reuse while pending.
  */
 myrs_exec_cmd(cs, cmd);
 image_status = cmd->status;
 image_residual = cmd->residual;
 mutex_unlock(&cs->dcmd_mutex);
 mutex_lock(&image_lock);
 image_state = 2;
 mutex_unlock(&image_lock);
}
static ssize_t stock_descriptor_show(struct device *dev,
 struct device_attribute *attr, char *buf)
{
 int i, n;
 mutex_lock(&image_lock);
 n = sysfs_emit(buf, "state=%d status=%d residual=%d\n", image_state, image_status, image_residual);
 if (image_state == 2)
  for (i=0; i<1024; i++) n += sysfs_emit_at(buf,n,"%02x%s",((u8 *)image_buf)[i],i==1023?"\n":"");
 mutex_unlock(&image_lock);
 return n;
}
static ssize_t stock_descriptor_store(struct device *dev,
 struct device_attribute *attr, const char *buf, size_t count)
{
 struct myrs_hba *cs = shost_priv(class_to_shost(dev));
 int rc = 0;
 mutex_lock(&image_lock);
 if (sysfs_streq(buf,"clear")) {
  if (image_state == 1) { rc=-EBUSY; goto out; }
  if (image_state == 2) {
   /* Worker may be returning after publishing state. */
   flush_work(&image_work);
   dma_free_coherent(&cs->pdev->dev,1024,image_buf,image_dma);
   image_buf=NULL;image_state=0;image_cs=NULL;
   module_put(THIS_MODULE);
  }
 } else if (sysfs_streq(buf,"descriptor")) {
  if (image_state) { rc=-EBUSY; goto out; }
  image_buf=dma_alloc_coherent(&cs->pdev->dev,1024,&image_dma,GFP_KERNEL);
  if (!image_buf) { rc=-ENOMEM; goto out; }
  memset(image_buf,0xa5,1024);
  image_cs=cs; image_state=1;image_status=-1;image_residual=-1;
  __module_get(THIS_MODULE);
  INIT_WORK(&image_work,image_worker);
  schedule_work(&image_work);
 } else rc=-EINVAL;
 out: mutex_unlock(&image_lock);return rc?rc:count;
}
static DEVICE_ATTR_RW(stock_descriptor);
static ssize_t stock_controller_show(struct device *dev,
 struct device_attribute *attr, char *buf)
{
 struct myrs_hba *cs=shost_priv(class_to_shost(dev));
 int i,n=0;
 mutex_lock(&cs->cinfo_mutex);
 for(i=0;i<sizeof(*cs->ctlr_info);i++)
  n+=sysfs_emit_at(buf,n,"%02x%s",((u8 *)cs->ctlr_info)[i],i==sizeof(*cs->ctlr_info)-1?"\n":"");
 mutex_unlock(&cs->cinfo_mutex);return n;
}
static DEVICE_ATTR_RO(stock_controller);
