// Real Chromium canvas/control test. NODE_PATH may point at bundled Playwright.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const [url,out]=process.argv.slice(2);
if(!url||!out)throw Error('usage: node browser_test.cjs URL OUTPUT');
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true});
 const reports=[];
 try{
  // Reference preserves the former 16-ms-after-draw scheduling. Both use the
  // same audited queue, renderer, HTTP encoding, browser and controls.
  for(const [round,pacing] of ['legacy-delay','raf-single-flight','raf-single-flight','legacy-delay'].entries()){
   const name=`${round+1}-${pacing}`;
   const page=await browser.newPage({viewport:{width:1000,height:900}});
   let inFlight=0,maxInFlight=0;
   page.on('request',r=>{if(r.url().endsWith('/step'))maxInFlight=Math.max(maxInFlight,++inFlight);});
   const done=r=>{if(r.url().endsWith('/step'))inFlight--;};
   page.on('requestfinished',done);page.on('requestfailed',done);
   await page.route(url,async route=>{
    const response=await route.fetch();let html=await response.text();
    if(pacing==='legacy-delay')html=html.replace('await new Promise(resolve=>requestAnimationFrame(resolve));','').replace('setTimeout(frame,0);','setTimeout(frame,16);');
    html=html.replace('setTimeout(frame,', 'if(deliveries.length<80)setTimeout(frame,');
    await route.fulfill({response,body:html});
   });
   await page.goto(url);
   const until=n=>page.waitForFunction(n=>window.rayDelivery?.length>=n,n,{timeout:60000});
   await until(8);await page.keyboard.down('ArrowUp');await until(20);await page.keyboard.up('ArrowUp');
   await page.keyboard.down('d');await until(32);await page.keyboard.up('d');
   await page.locator('#reset').click();await until(40);
   await page.keyboard.down('w');await until(48);
   await page.evaluate(()=>window.dispatchEvent(new Event('blur')));await page.keyboard.up('w');
   await until(80);
   const data=await page.evaluate(()=>({samples:window.rayDelivery,backend:document.querySelector('#backend').textContent,status:document.querySelector('#status').textContent,pixels:Array.from(document.querySelector('canvas').getContext('2d').getImageData(0,0,80,60).data)}));
   assert.equal(data.samples.length,80);assert.equal(maxInFlight,1);
   assert(data.samples.some(s=>s.keys===1));assert(data.samples.some(s=>s.keys===8));
   assert(data.samples.some(s=>s.reset&&s.frame_id===0));
   assert(data.samples.slice(-20).every(s=>s.keys===0));
   assert(data.pixels.every((v,i)=>i%4!==3||v===255));assert(new Set(data.pixels).size>4);
   assert(!data.status.includes('Stopped'));
   const steady=data.samples.slice(5).filter(s=>!s.reset&&s.interval>0);
   const average=k=>steady.reduce((n,s)=>n+s[k],0)/steady.length;
   const result={round:round+1,pacing,backend:data.backend,frames:data.samples.length,max_in_flight:maxInFlight,mean_draw_interval_ms:average('interval'),delivered_fps:1000/average('interval'),mean_callback_ms:average('callback_ms'),samples:data.samples,status:data.status};
   fs.writeFileSync(path.join(out,name+'.json'),JSON.stringify(result,null,2)+'\n');
   await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
   reports.push({...result,samples:undefined});await page.close();
  }
  fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(reports,null,2)+'\n');console.log(JSON.stringify(reports,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
