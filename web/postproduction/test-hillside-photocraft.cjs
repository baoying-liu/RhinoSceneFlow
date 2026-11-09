// Real pinned Wasm editor, headless Edge mouse events; no model calls or system mouse.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const a=JSON.parse(fs.readFileSync(path.join(root,'artifacts/feature-audit-20261109/latest.json'))),service=JSON.parse(fs.readFileSync(path.join(process.env.LOCALAPPDATA,'RhinoSceneFlow/postproduction/service.json'))),f={board:a.photoBoard,original:a.sourceNode,folder:a.folder},base=`http://127.0.0.1:${service.port}`,headers={Authorization:'Bearer '+service.token};
 const prefs=await fetch(base+'/api/board-preferences',{headers}).then(r=>r.json());
 await fetch(base+'/api/board-preferences',{method:'PUT',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({language:'en',lastBoard:f.board})});
 const get=async p=>{const r=await fetch(base+'/api'+p,{headers});assert(r.ok);return r.json();};
 const before=await get('/boards/'+f.board),original=before.nodes.find(n=>n.id===f.original);
 assert(!original.editReference,'Start a new isolated fixture');
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/#token='+service.token);
 await page.locator('.contentFields').waitFor();await page.locator('.contextTools>summary').click();
 async function open(){await page.locator('.workActions').getByRole('button',{name:'Edit in PhotoCraft'}).click();await page.waitForFunction(()=>document.querySelector('.photoCraftOverlay .primary')?.disabled===false,{timeout:90000});await page.waitForTimeout(900);await page.frameLocator('iframe').locator('canvas#photocraft_canvas').focus();}
 async function paint(y){await page.keyboard.press('b');await page.mouse.move(590,y);await page.mouse.down();await page.mouse.move(650,y+12,{steps:14});await page.mouse.up();}
 const slots=[];
 for(let i=0;i<2;i++){
  await open();await paint(542+i*40);await page.screenshot({path:path.join(f.folder,`photocraft-edit-${i+1}.png`)});
  await page.getByRole('button',{name:'Apply and return',exact:true}).click();await page.locator('.photoCraftOverlay').waitFor({state:'detached',timeout:20000});
  const b=await get('/boards/'+f.board),n=b.nodes.find(n=>n.id===f.original);slots.push(n.editReference);
  assert.equal(n.asset,original.asset);assert.equal(n.versionId,original.versionId);assert.deepEqual(n.versions,original.versions);
  assert.equal(n.editReference.sourceAsset,original.asset);assert.equal(b.nodes.length,before.nodes.length);
  if(i===0)await page.getByRole('button',{name:'Hide editing reference',exact:true}).click();
  if(i===1)assert.equal(n.editReference.visible,false,'Replacing the reference preserves its hidden setting');
  const r=await fetch(base+`/api/boards/${f.board}/assets/${n.editReference.asset}`,{headers});fs.writeFileSync(path.join(f.folder,`photocraft-reference-${i+1}.png`),Buffer.from(await r.arrayBuffer()));
 }
 assert.notEqual(slots[0].project,slots[1].project);assert.notEqual(slots[0].asset,slots[1].asset);
 await page.locator('.editReferencePreview').click();await page.locator('.referenceComparison [role=slider]').waitFor();await page.screenshot({path:path.join(f.folder,'photocraft-reference-compare.png')});await page.getByRole('button',{name:'Close',exact:true}).click();
 await open();await paint(565);await page.getByRole('button',{name:'Cancel',exact:true}).click();
 let b=await get('/boards/'+f.board);assert.deepEqual(b.nodes.find(n=>n.id===f.original).editReference,slots[1]);
 await page.reload();await page.locator('.contentFields').waitFor();await page.locator('.contextTools>summary').click();await page.locator('.editingReference .thumbBox img').waitFor();
 await page.screenshot({path:path.join(f.folder,'photocraft-reference-returned.png')});assert.deepEqual(errors,[]);
 const report={realPhotoCraft:'0.21.0 Web/Wasm',paintedTwice:true,reopenedEditableProject:true,singleSlotReplaced:true,cancelPreservedSlot:true,reloadThumbnail:true,referenceComparison:true,sourcePixelsAndVersionsUnchanged:true,modelCalls:0,folder:f.folder,slots};
 fs.writeFileSync(path.join(f.folder,'photocraft-browser-verified.json'),JSON.stringify(report,null,2));console.log('Real Hillside PhotoCraft roundtrip passed');
 }finally{await browser.close();await fetch(base+'/api/board-preferences',{method:'PUT',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(Object.entries(prefs).filter(([k])=>k!=='listWheelVersion')))});}
})().catch(e=>{console.error(e);process.exitCode=1;});
