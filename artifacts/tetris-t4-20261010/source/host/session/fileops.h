/* A file reference owns the session. Synchronous operations serialize with
 * release/remove; file_operations.owner holds the module through final close.
 * An uncertain transaction additionally pins module/DMA until reboot. */
static void session_free(struct kref *ref)
{
    struct experiment *d=container_of(ref,struct experiment,refs);
    free_captures(d);release_firmware(d->payload);kfree(d);
}
static void session_pin(struct experiment *d)
{
    if(!d->pinned && (d->pending || d->exec_dirty || d->stage_dirty)) {
        __module_get(THIS_MODULE);pci_dev_get(d->pdev);d->pinned=true;
        record(d,"SESSION FAILED: retained DMA/module; reboot required\n");
    }
}
static void session_log_start(struct experiment *d)
{ d->used=0;d->result[0]=0; }
static void session_log_end(struct experiment *d)
{ d->result_blob.size=d->used; }
static int session_file_open(struct inode *inode,struct file *file)
{
    struct miscdevice *misc=file->private_data;
    struct experiment *d=container_of(misc,struct experiment,misc);
    int rc;
    mutex_lock(&d->session_lock);
    if(d->owned || d->removed || d->pinned) {rc=-EBUSY;goto out;}
    session_log_start(d);d->sequence=0;d->response_ready=false;
    rc=session_open(d);
    if(rc) {session_close(d);session_pin(d);}
    else {kref_get(&d->refs);d->owned=true;file->private_data=d;}
    session_log_end(d);
out:
    mutex_unlock(&d->session_lock);return rc;
}
static ssize_t session_file_write(struct file *file,const char __user *buf,size_t count,loff_t *pos)
{
    struct experiment *d=file->private_data;u8 *request;int rc;
    if(count!=BIO_SIZE) return -EINVAL;
    request=memdup_user(buf,count);if(IS_ERR(request)) return PTR_ERR(request);
    mutex_lock(&d->session_lock);
    if(d->removed || !d->ready || d->pinned) {rc=-EIO;goto out;}
    if(d->response_ready) {rc=-EBUSY;goto out;}
    if(!bio_request_valid(request) || bio_word(request+8)<=d->sequence) {rc=-EINVAL;goto out;}
    session_log_start(d);rc=session_step(d,request);
    if(rc) {d->ready=false;session_close(d);session_pin(d);}
    else {
        d->response_ready=true;
        d->stage[6].blob.size=d->output_length;d->stage[7].blob.size=d->output_length;
    }
    session_log_end(d);
out:
    mutex_unlock(&d->session_lock);kfree(request);return rc?rc:count;
}
static ssize_t session_file_read(struct file *file,char __user *buf,size_t count,loff_t *pos)
{
    struct experiment *d=file->private_data;int rc;
    if(count!=BIO_SIZE) return -EINVAL;
    mutex_lock(&d->session_lock);
    if(d->removed || d->pinned) rc=-EIO;
    else if(!d->response_ready) rc=-EAGAIN;
    else if(copy_to_user(buf,d->stage[6].data+BIO_OFFSET,BIO_SIZE)) rc=-EFAULT;
    else {d->response_ready=false;rc=BIO_SIZE;}
    mutex_unlock(&d->session_lock);return rc;
}
static int session_file_release(struct inode *inode,struct file *file)
{
    struct experiment *d=file->private_data;int rc=0;
    mutex_lock(&d->session_lock);
    if(!d->removed && !d->pinned) {
        session_log_start(d);rc=session_close(d);session_pin(d);session_log_end(d);
    }
    d->owned=false;
    mutex_unlock(&d->session_lock);
    kref_put(&d->refs,session_free);
    return rc;
}
static const struct file_operations session_fops={
    .owner=THIS_MODULE,.open=session_file_open,.write=session_file_write,
    .read=session_file_read,.release=session_file_release,.llseek=no_llseek,
};
