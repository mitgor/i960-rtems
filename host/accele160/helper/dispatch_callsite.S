/* Assemble at the exact loader callsite; its only instruction calls the cave. */
 .text
 .globl dispatch_callsite
dispatch_callsite:
 call dispatch_hook
