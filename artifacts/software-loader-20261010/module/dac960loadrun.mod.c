#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/export-internal.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

#ifdef CONFIG_UNWINDER_ORC
#include <asm/orc_header.h>
ORC_HEADER;
#endif

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_MITIGATION_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif



static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x87a21cb3, "__ubsan_handle_out_of_bounds" },
	{ 0xf9a482f9, "msleep" },
	{ 0xadd26b67, "debugfs_remove" },
	{ 0x7671ec45, "_dev_err" },
	{ 0x7271639f, "dma_free_attrs" },
	{ 0x63d719fc, "pci_iounmap" },
	{ 0x6ac83e98, "pci_release_regions" },
	{ 0x4829d0bb, "pci_disable_device" },
	{ 0x9dd7733, "pci_write_config_word" },
	{ 0x37a0cba, "kfree" },
	{ 0x7aa1756e, "kvfree" },
	{ 0xc6d09aa9, "release_firmware" },
	{ 0xade87842, "crypto_alloc_shash" },
	{ 0xeb233a45, "__kmalloc" },
	{ 0x46484290, "crypto_shash_digest" },
	{ 0x415a891f, "crypto_destroy_tfm" },
	{ 0xf0fdf6cb, "__stack_chk_fail" },
	{ 0xe2d5255a, "strcmp" },
	{ 0x9ed12e20, "kmalloc_large" },
	{ 0xee7a43b5, "request_firmware" },
	{ 0xfd710147, "pci_read_config_word" },
	{ 0xf35b3830, "pci_enable_device" },
	{ 0x2f2fceca, "pci_request_regions" },
	{ 0xa49317d2, "dma_set_mask" },
	{ 0x713213b1, "dma_set_coherent_mask" },
	{ 0xdaefa31, "pci_iomap" },
	{ 0x6b18d4d2, "dma_alloc_attrs" },
	{ 0x599fb41c, "kvmalloc_node" },
	{ 0x2e7544b4, "pci_set_master" },
	{ 0x82eaa415, "__module_get" },
	{ 0xb43a0df8, "pci_dev_get" },
	{ 0x67a9646, "debugfs_create_dir" },
	{ 0xe1bebdb2, "debugfs_create_blob" },
	{ 0x680d96f1, "param_ops_uint" },
	{ 0x1c7f70d1, "param_ops_bool" },
	{ 0x2d04f9df, "param_ops_charp" },
	{ 0xbdfb6dbb, "__fentry__" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0x449ad0a7, "memcmp" },
	{ 0xeffd6814, "pci_unregister_driver" },
	{ 0xcc7266e8, "__pci_register_driver" },
	{ 0x54b1fac6, "__ubsan_handle_load_invalid_value" },
	{ 0xb43f9365, "ktime_get" },
	{ 0xe2c17b5d, "__SCT__might_resched" },
	{ 0xc3055d20, "usleep_range_state" },
	{ 0xfb578fc5, "memset" },
	{ 0x69acdf38, "memcpy" },
	{ 0x96848186, "scnprintf" },
	{ 0xb165f690, "_dev_info" },
	{ 0x2f93810, "module_layout" },
};

MODULE_INFO(depends, "");

MODULE_ALIAS("pci:v00001069d00000010sv*sd*bc*sc*i*");

MODULE_INFO(srcversion, "24318151EA9DF16EA0F65D6");
