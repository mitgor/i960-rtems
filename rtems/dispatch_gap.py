"""Build-local i960 dispatcher fix: never expose the heir with outgoing FP.
Keep the original saved interrupt level across the masked context transfer."""
import hashlib
from pathlib import Path

def patch(source):
 early='    _ISR_Enable( level );\n\n    heir->ticks_executed++;'
 late='    executing = _Thread_Executing;\n\n    _ISR_Disable( level );'
 assert source.count(early)==1 and source.count(late)==1
 return source.replace(early,'    /* i960: heir identity must not be interrupt-visible on outgoing FP. */\n\n    heir->ticks_executed++;').replace(late,'    executing = _Thread_Executing;\n\n    /* Still masked: preserve the original saved level, not priority 31. */')

def generate(source,out):
 original=source.read_bytes();modified=patch(original.decode()).encode();out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(modified)
 return dict(source=str(source),before_sha256=hashlib.sha256(original).hexdigest(),after_sha256=hashlib.sha256(modified).hexdigest(),fix='mask heir publication through context transfer; preserve original ISR level')
