/* Replace c000c9cc ret with branch to the copied-loader cave. */
 .text
 .globl late_callsite
late_callsite:
 b dispatch_hook
