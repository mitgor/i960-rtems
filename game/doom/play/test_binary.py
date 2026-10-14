#!/usr/bin/env python3
"""Execute the actual Canvas refresh code against valid and malformed packets."""
import json,subprocess,tempfile
from pathlib import Path
page=Path(__file__).with_name('index.html').read_text();script=page.split('<script>')[1].split('</script>')[0]
test=r'''
const vm=require('vm'),assert=require('assert');
const source=SOURCE;
(async()=>{for(const bad of ['none','magic','version','width','height','length','crc']){
 const packet=Buffer.alloc(65568);[0x31424644,1,0,9,320,200,65536,0].forEach((v,i)=>packet.writeUInt32LE(v,i*4));
 for(let i=0;i<64000;i++)packet[32+i]=i%256;
 for(let i=0;i<256;i++){packet[64032+i*3]=i;packet[64033+i*3]=255-i;packet[64034+i*3]=i^85}
 const at={magic:0,version:4,width:16,height:20,length:24,crc:28};if(bad!=='none')packet.writeUInt32LE(7,at[bad]);
 let paints=0;const status={textContent:''},ctx={createImageData:(w,h)=>({data:new Uint8Array(w*h*4)}),putImageData(im){paints++;for(let i=0;i<64000;i++){assert.equal(im.data[i*4],i%256);assert.equal(im.data[i*4+1],255-i%256);assert.equal(im.data[i*4+2],(i%256)^85);assert.equal(im.data[i*4+3],255)}}};
 const screen={getContext:()=>ctx,focus(){}},sandbox={document:{getElementById:id=>id==='screen'?screen:id==='status'?status:{}},window:{},setInterval(){},fetch:async path=>path==='/status'?{json:async()=>({frame:'0-8',binary:true,message:'test'})}:{ok:true,arrayBuffer:async()=>packet.buffer.slice(packet.byteOffset,packet.byteOffset+packet.length)}};
 vm.createContext(sandbox);vm.runInContext(source.replace('setInterval(refresh,50);refresh();','setInterval(refresh,50);'),sandbox);await vm.runInContext('refresh()',sandbox);
 assert.equal(paints,bad==='none'?1:0);if(bad==='none')assert.equal(vm.runInContext('last',sandbox),'0-9');else assert.equal(status.textContent,'Invalid binary frame');
}console.log('PASS actual Canvas decoder: palette/pixels, embedded generation race, malformed packet rejection');})().catch(e=>{console.error(e);process.exit(1)});
'''.replace('SOURCE',json.dumps(script))
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.js';p.write_text(test);subprocess.run(['node',str(p)],check=True)
