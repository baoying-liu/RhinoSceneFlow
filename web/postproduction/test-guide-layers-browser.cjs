// Actual PhotoCraft Wasm + HTTP + canvas events; no system mouse or model calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const f=JSON.parse(fs.readFileSync(path.join(root,'artifacts/guide-layers-latest.json'))),base=`http://127.0.0.1:${f.port}`,headers={Authorization:'Bearer workflow-fixture-token','Content-Type':'application/json'},prefix='/boards/'+f.board;
 async function api(p,b,method){const r=await fetch(base+'/api'+p,{headers,method:method||(b?'POST':'GET'),body:b?JSON.stringify(b):undefined});assert(r.ok,await r.clone().text());return r.json();}
 let b=await api(prefix);await api(prefix,{revision:b.revision,selectedId:f.original},'PUT');await api('/board-preferences',{language:'en',lastBoard:f.board},'PUT');
 const before=await api(prefix),source=before.nodes.find(n=>n.id===f.original);
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage({viewport:{width:1700,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/#token=workflow-fixture-token');await page.locator('.guideLayers').waitFor();
 const row=id=>page.locator(`[data-guide-layer="${id}"]`),eye=locator=>locator.getByRole('button',{name:'Show layer',exact:true}),enable=locator=>locator.getByRole('checkbox',{name:'Use for AI generation',exact:true});
 await row(f.mark).locator('.guideLayerName').click();await page.waitForTimeout(700);assert(await row(f.mark).evaluate(el=>el.classList.contains('selected')));
 await eye(row(f.protect)).click();await page.waitForTimeout(400);let after=await api(prefix);assert.equal(after.nodes.find(n=>n.id===f.original).annotations.find(a=>a.id===f.protect).visible,false);
 await eye(row(f.protect)).click();await page.waitForTimeout(300);
 await page.locator('.modeSwitch button').nth(0).click();await page.locator('.currentPreview .instructionOverlay').waitFor();const beforeImages=await page.locator('.instructionOverlay image').count();await eye(row(f.protect)).click();await page.waitForTimeout(350);assert.equal(await page.locator('.instructionOverlay image').count(),beforeImages-1);await eye(row(f.protect)).click();await page.waitForTimeout(300);
 const allEye=page.locator('.guideLayers>header').getByRole('button',{name:'Show layer',exact:true});await allEye.click();await page.waitForTimeout(350);assert.equal(await page.locator('.currentPreview .instructionOverlay').count(),0);await allEye.click();await page.waitForTimeout(300);
 const header=page.locator('.guideLayers>header');await enable(header).click();await page.waitForTimeout(300);assert.equal(await enable(row(f.mark)).isChecked(),false);await enable(header).click();await page.waitForTimeout(300);assert.equal(await enable(row(f.mark)).isChecked(),false);
 await page.locator('.workActions').getByRole('button',{name:'Edit in PhotoCraft',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.photoCraftOverlay .primary')?.disabled===false,null,{timeout:90000});await page.waitForTimeout(1200);await page.screenshot({path:path.join(f.folder,'guide-photocraft-open.png')});
 await page.getByRole('button',{name:'Apply and return',exact:true}).click();await page.locator('.photoCraftOverlay').waitFor({state:'detached',timeout:45000});
 after=await api(prefix);const n=after.nodes.find(n=>n.id===f.original);assert.equal(n.asset,source.asset);assert.equal(n.versionId,source.versionId);assert.deepEqual(n.versions,source.versions);assert.equal(n.editReference.declaration.schema,1);assert.equal(n.editReference.declaration.appearance.excludesInstructions,true);assert.equal(n.annotations.find(a=>a.id===f.mark).enabled,false);
 await page.reload();await row(f.mark).waitFor();assert.equal(await enable(row(f.mark)).isChecked(),false);await page.screenshot({path:path.join(f.folder,'guide-layers-panel.png')});assert.deepEqual(errors,[]);
 const report={realPhotoCraftRoundtrip:true,stableIDs:n.annotations.map(a=>a.id),appearanceSeparated:true,masterPreservesChildren:true,selectionSynchronized:true,listInstructionOverlay:true,totalEyeHidesAllInstructions:true,eyeIndependentOfEnable:true,reloadPreserved:true,sourceAndBackupsUnchanged:true,modelCalls:0,folder:f.folder};fs.writeFileSync(path.join(f.folder,'guide-browser-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
