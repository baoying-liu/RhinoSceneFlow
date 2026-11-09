// Real headless Edge, actual HTTP input preparation; no image model calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{const f=JSON.parse(fs.readFileSync(path.join(root,'artifacts/workflow021-http-latest.json'))),base=`http://127.0.0.1:${f.port}`,headers={Authorization:'Bearer workflow-fixture-token','Content-Type':'application/json'};
 const api=async(p,body)=>{const r=await fetch(base+'/api'+p,{headers,method:body?'POST':'GET',body:body?JSON.stringify(body):undefined});assert(r.ok,await r.clone().text());return r.json()};
 const before=await api('/boards/'+f.board),browser=await chromium.launch({channel:'msedge',headless:true});
 try{const page=await browser.newPage({viewport:{width:1800,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/#token=workflow-fixture-token');await page.locator('.generationInput').waitFor();
 const source=()=>page.locator('.resource').filter({has:page.locator('.treeToggle')}).first();
 await page.locator('.resource').nth(1).click();await page.getByRole('button',{name:'High-resolution output',exact:true}).waitFor();
 assert.equal(await page.locator('.generationInput .inputSourceLink').innerText(),'Architecture.psd');
 await page.getByRole('button',{name:'High-resolution output',exact:true}).click();await page.getByRole('button',{name:'Generate image…',exact:true}).waitFor();
 let b=await api('/boards/'+f.board),hd=b.nodes.find(n=>n.id===b.selectedId);assert.equal(hd.parentId,f.child);assert.equal(hd.params.generationStage,'detail');assert.equal(hd.params.prompt,'');assert(hd.pending&&!hd.locked);
 await page.getByRole('button',{name:'Generate image…',exact:true}).click();await page.locator('.inputCheck').waitFor({timeout:30000});
 assert.equal(await page.locator('.inputCheck strong').innerText(),before.nodes.find(n=>n.id===f.child).name);assert.equal(await page.locator('.inputCheck img').count(),1);
 assert(await page.getByRole('button',{name:'Confirm and generate',exact:true}).isEnabled());await page.getByRole('button',{name:'Back to editing',exact:true}).click();
 await page.locator('.resource').nth(1).click();const oldCount=await page.locator('.resource').count();await page.getByRole('button',{name:'Another proposal · sibling',exact:true}).click();await page.locator('.resource').nth(oldCount).waitFor();await page.locator('.pendingBoard').waitFor();
 b=await api('/boards/'+f.board);const draft=b.nodes.find(n=>n.id===b.selectedId);assert.equal(draft.parentId,f.original);assert.equal(draft.params.prompt,'');
 const prompt=page.locator('.contentFields textarea');await prompt.fill('Refine the wood cladding');
 assert((await prompt.boundingBox()).y<650,'Brief must be in the first screen');assert.equal(await page.locator('.contextTools').getAttribute('open'),null);
 await page.getByRole('button',{name:'Generate image…',exact:true}).click();await page.locator('.inputCheck').waitFor({timeout:30000});
 assert.equal(await page.locator('.inputCheck strong').innerText(),'Architecture.psd');await page.getByRole('button',{name:'Editable mask',exact:true}).click();await page.locator('.inputCheck img').waitFor();
 assert.match(await page.locator('.inputCheck').innerText(),/White: editable/);await page.getByRole('button',{name:'Back to editing',exact:true}).click();
 await page.getByRole('button',{name:'Use input as annotation background',exact:true}).click();await page.getByRole('button',{name:'Input background · not generated',exact:true}).waitFor();assert.equal(await page.locator('.viewerToolbar').getByRole('button',{name:'AI result',exact:true}).count(),0);
 await page.locator('.contextTools>summary').click();await page.getByRole('button',{name:'Adjust context frame',exact:true}).click();await page.locator('.konvajs-content').waitFor();
 await page.screenshot({path:path.join(f.folder,'task-flow-canvas.png')});
 // Closing a preparation cannot be undone by its delayed HTTP response.
 await page.route('**/preflight',async route=>{await new Promise(r=>setTimeout(r,1200));await route.continue();});
 await page.getByRole('button',{name:'Check generation input',exact:true}).click();await page.locator('[role=dialog]').waitFor();await page.keyboard.press('Escape');await page.waitForTimeout(3000);assert.equal(await page.locator('[role=dialog]').count(),0);await page.unroute('**/preflight');
 // No preflight or draft action may publish or pretend a model call happened.
 b=await api('/boards/'+f.board);for(const n of before.nodes){const after=b.nodes.find(x=>x.id===n.id);assert.equal(after.asset,n.asset);assert.equal(after.versionId,n.versionId);assert.deepEqual(after.versions,n.versions);}
 assert.equal((await api('/boards/'+f.board+'/tasks')).filter(t=>!t.imported).length,0);assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(f.folder,'task-flow-verified.json'),JSON.stringify({hdDraft:true,siblingInput:true,promptFirstScreen:true,actualPreflight:true,canvasFrameEntry:true,sourceAndVersionsUnchanged:true,errors,modelCalls:0},null,2));console.log('Task flow browser passed: '+f.folder);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
