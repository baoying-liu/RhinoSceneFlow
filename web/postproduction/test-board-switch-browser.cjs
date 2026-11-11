// Board navigation with controlled selects and an async save barrier. No model calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
const f=JSON.parse(fs.readFileSync(path.join(root,'artifacts/workflow021-http-latest.json'))),base=`http://127.0.0.1:${f.port}`;
async function api(p,b,method){const r=await fetch(base+'/api'+p,{method:method||(b?'POST':'GET'),headers:{Authorization:'Bearer workflow-fixture-token','Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});assert(r.ok,await r.clone().text());return r.json()}
(async()=>{
 const before=await api('/boards/'+f.board),empty=await api('/boards',{name:'Empty navigation fixture'});await api('/board-preferences',{language:'en',lastBoard:empty.id},'PUT');
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
 await page.goto(base+'/#token=workflow-fixture-token');const picker=page.getByRole('combobox',{name:'Board',exact:true});await picker.waitFor();
 // A clean empty board still crosses an await in flush: the selected target must be pinned first.
 await picker.selectOption(f.board);await page.locator('.resource').nth(1).waitFor();assert.equal(await picker.inputValue(),f.board);assert((await page.title()).startsWith(before.name));
 const prompt=page.locator('.contentFields textarea');const brief='Save this to the original board before switching';await prompt.fill(brief);
 await picker.selectOption(empty.id);await page.getByRole('heading',{name:'Images 0',exact:true}).waitFor();assert.equal((await api('/boards/'+f.board)).nodes.find(n=>n.id===f.original).params.prompt,brief);
 await page.getByPlaceholder('Find an image…').fill('no-such-image');
 // Loading is explicit and the old editor cannot receive edits while the next board is loading.
 await page.route(base+'/api/boards/'+f.board,async route=>{if(route.request().method()==='GET')await new Promise(r=>setTimeout(r,700));await route.continue()});
 await picker.selectOption(f.board);await page.waitForFunction(()=>document.querySelector('.boardPicker select').disabled);assert(await page.locator('.studioBody').evaluate(el=>el.inert));await page.locator('.resource').nth(1).waitFor();await page.waitForFunction(()=>!document.querySelector('.boardPicker select').disabled);assert.equal(await page.getByPlaceholder('Find an image…').inputValue(),'');await page.unroute(base+'/api/boards/'+f.board);
 // A failed save must not switch away or lose the text. The user can retry afterward.
 const pending='Keep this draft if saving fails';await prompt.fill(pending);
 await page.route(base+'/api/boards/'+f.board,async route=>{if(route.request().method()==='PUT')await route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({detail:'Fixture save failure'})});else await route.continue()});
 await picker.selectOption(empty.id);await page.getByRole('alert').waitFor();await page.waitForFunction(()=>!document.querySelector('.boardPicker select').disabled);assert.equal(await picker.inputValue(),f.board);assert.equal(await prompt.inputValue(),pending);assert.equal((await api('/boards/'+f.board)).nodes.find(n=>n.id===f.original).params.prompt,brief);
 await page.unroute(base+'/api/boards/'+f.board);await picker.selectOption(empty.id);await page.getByRole('heading',{name:'Images 0',exact:true}).waitFor();assert.equal((await api('/boards/'+f.board)).nodes.find(n=>n.id===f.original).params.prompt,pending);
 await page.reload();await page.waitForFunction(id=>document.querySelector('.boardPicker select')?.value===id,empty.id);assert.equal(await picker.inputValue(),empty.id);await picker.selectOption(f.board);await page.locator('.resource').nth(1).waitFor();
 const after=await api('/boards/'+f.board);for(const old of before.nodes){const n=after.nodes.find(n=>n.id===old.id);assert.equal(n.asset,old.asset);assert.equal(n.versionId,old.versionId)}assert.deepEqual(errors,[]);
 await page.screenshot({path:path.join(f.folder,'board-switch-browser.png')});const report={emptyToPopulated:true,populatedToEmpty:true,unsavedBriefSavedToCorrectBoard:true,loadFeedback:true,editorInertDuringSwitch:true,filtersReset:true,saveFailurePreservesDraftAndBoard:true,retryAndReload:true,sourcePixelsUnchanged:true,modelCalls:0};fs.writeFileSync(path.join(f.folder,'board-switch-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
