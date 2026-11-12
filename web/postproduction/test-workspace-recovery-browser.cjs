// Recovery may change a board revision before the first edit. No model calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const f=JSON.parse(fs.readFileSync(path.join(root,'artifacts/workflow021-http-latest.json'),'utf8'));
 const base='http://127.0.0.1:'+f.port,headers={Authorization:'Bearer workflow-fixture-token','Content-Type':'application/json'};
 const api=async(p,body)=>{const r=await fetch(base+'/api'+p,{headers,method:body?'PUT':'GET',body:body?JSON.stringify(body):undefined});assert(r.ok,await r.clone().text());return r.json()};
 const before=await api('/boards/'+f.board),source=before.nodes.find(n=>n.id===f.original);
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1700,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));let recovered=false;
  await page.route('**/api/boards/'+f.board+'/tasks',async route=>{
   if(!recovered){recovered=true;const b=await api('/boards/'+f.board);await api('/boards/'+f.board,{revision:b.revision,name:b.name+' · recovered'});}
   await route.continue();
  });
  await page.addInitScript(()=>sessionStorage.setItem('sceneflow-post-token','workflow-fixture-token'));
  await page.goto(base);await page.locator('.contentFields textarea').waitFor();
  await page.locator('.contentFields textarea').fill('Immediate edit after task recovery');await page.locator('.workFooter').click();
  await page.waitForFunction(()=>document.querySelector('.saveState')?.textContent==='Saved locally');
  // Wait for the debounce, then verify persistence rather than trusting the label.
  await page.waitForTimeout(1200);const after=await api('/boards/'+f.board);
  assert(recovered);assert.equal(after.nodes.find(n=>n.id===f.original).params.prompt,'Immediate edit after task recovery');
  assert.equal(await page.locator('.errorBanner').count(),0);assert.equal(after.nodes.find(n=>n.id===f.original).asset,source.asset);assert.deepEqual(errors,[]);
  const report={taskRecoveryBeforeEditableRevision:true,immediateEditPersists:true,noFalseConflict:true,sourcePixelsUnchanged:true,modelCalls:0,errors};
  fs.writeFileSync(path.join(f.folder,'workspace-recovery-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1});
