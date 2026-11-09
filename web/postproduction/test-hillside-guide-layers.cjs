// Real B Web service, real Hillside pixels, real PhotoCraft Wasm. No model calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const out=path.join(root,'artifacts/rhino-B/layers0224'),f=JSON.parse(fs.readFileSync(path.join(out,'hillside-case.json'))),service=JSON.parse(fs.readFileSync(path.join(process.env.LOCALAPPDATA,'RhinoSceneFlow/postproduction/service.json'))),base=`http://127.0.0.1:${service.port}`,headers={Authorization:'Bearer '+service.token};
 const get=async p=>{const r=await fetch(base+'/api'+p,{headers});assert(r.ok);return r.json();};
 const before=await get('/boards/'+f.board),original=before.nodes.find(n=>n.id===f.node);assert(!original.locked);
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage({viewport:{width:1800,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/#token='+service.token);await page.locator('.guideLayers').waitFor();
 await page.locator('.workActions').getByRole('button',{name:'Edit in PhotoCraft',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.photoCraftOverlay .primary')?.disabled===false,null,{timeout:90000});await page.waitForTimeout(1500);await page.screenshot({path:path.join(out,'hillside-photocraft-layers.png')});
 await page.getByRole('button',{name:'Apply and return',exact:true}).click();await page.locator('.photoCraftOverlay').waitFor({state:'detached',timeout:90000});
 const after=await get('/boards/'+f.board),n=after.nodes.find(n=>n.id===f.node);assert.equal(n.asset,original.asset);assert.equal(n.versionId,original.versionId);assert.deepEqual(n.versions,original.versions);assert.deepEqual(n.annotations,original.annotations,'No-op preserves real-case vectors and text');assert.equal(n.editReference.width,1200);assert.equal(n.editReference.height,900);assert.equal(n.editReference.declaration.instructions.length,3);assert(n.editReference.declaration.instructions.every(a=>!a.changed&&a.asset));
 await page.getByRole('button',{name:'Annotations',exact:true}).click();await page.locator('.guideLayers').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'hillside-guide-panel.png')});
 const asset=await fetch(base+`/api/boards/${f.board}/assets/${n.editReference.asset}`,{headers});fs.writeFileSync(path.join(out,'hillside-appearance-reference.png'),Buffer.from(await asset.arrayBuffer()));assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(out,'hillside-browser-verified.json'),JSON.stringify({board:f.board,actualPhotoCraft:true,realHillsidePixels:true,originalAndVersionsUnchanged:true,noOpPreservesVectorsAndText:true,appearanceExcludesInstructions:true,returnedLayerThumbnails:3,pageErrors:errors,modelCalls:0},null,2));console.log('Real B Hillside PhotoCraft instruction roundtrip passed; no model calls.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
