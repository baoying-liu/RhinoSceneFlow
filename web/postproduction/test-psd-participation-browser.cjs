// Existing HTTP/browser harness: real Edge, file raster worker, no image calls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'artifacts/psd-guides-02214');
const {chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const f=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'))),base=`http://127.0.0.1:${f.port}`,headers={Authorization:'Bearer psd-guide-fixture-token','Content-Type':'application/json'};
 const api=async(p,body,method)=>{const r=await fetch(base+'/api'+p,{headers,method:method||(body?'POST':'GET'),body:body?JSON.stringify(body):undefined});assert(r.ok,await r.clone().text());return r.json()};
 const initial=await api('/boards/'+f.board);await api('/boards/'+f.board,{revision:initial.revision,selectedId:f.original},'PUT');await api('/board-preferences',{language:'en'},'PUT');
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1540,height:1040}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/#token=psd-guide-fixture-token');await page.locator('.psdParticipation').waitFor();
  const show=async()=>{if(!await page.locator('.psdParticipation').evaluate(n=>n.open))await page.locator('.psdParticipation>summary').click();};
  await show();await page.getByRole('button',{name:'Restore defaults',exact:true}).click();await page.waitForTimeout(1150);
  const ground=page.getByRole('checkbox',{name:'Use in AI: Ground',exact:true}),facade=page.getByRole('checkbox',{name:'Use in AI: Facade',exact:true}),depth=page.getByRole('checkbox',{name:'Use in AI: Depth',exact:true});
  assert(await ground.isChecked());assert(await facade.isChecked());assert(!await depth.isChecked());assert(await page.getByRole('combobox',{name:'Usage: Depth',exact:true}).isDisabled());
  await depth.check();await page.waitForTimeout(1150);assert(await page.getByRole('combobox',{name:'Usage: Depth',exact:true}).isEnabled());
  await page.locator('.resourceHead h2').click();await page.keyboard.press('Control+z');await page.waitForFunction(()=>!document.querySelector('[aria-label="Use in AI: Depth"]').checked);
  await page.keyboard.press('Control+r');await page.waitForFunction(()=>document.querySelector('[aria-label="Use in AI: Depth"]').checked);
  await page.waitForTimeout(550);await page.reload();await page.locator('.psdParticipation').waitFor();await show();assert(await depth.isChecked());
  let b=await api('/boards/'+f.board),source=b.nodes.find(n=>n.id===f.original);const row=source.source.layers.find(l=>l.name==='Depth');assert.equal(source.source.layers.find(l=>l.id===row.id).visible,false);assert.equal(source.params.layerParticipation[row.id],true);
  await page.getByRole('button',{name:'Create proposal',exact:true}).click();await page.getByRole('button',{name:'Generate image…',exact:true}).waitFor();await show();assert(await depth.isChecked());
  await page.locator('.contentFields textarea').fill('Refine the facade using real wood; keep massing and the camera.');
  await page.getByRole('button',{name:'Generate image…',exact:true}).click();await page.locator('.inputCheck').waitFor({timeout:30000});
  assert.equal(await page.locator('.psdGuideManifest').count(),1);assert.match(await page.locator('.psdGuideManifest').innerText(),/Depth/);
  const oldImage=await page.locator('.inputCheck img').getAttribute('src');await page.getByRole('button',{name:'PSD guides',exact:true}).click();await page.waitForFunction(old=>{const image=document.querySelector('.inputCheck img');return image&&image.src!==old&&image.complete&&image.naturalWidth>0;},oldImage);await page.screenshot({path:path.join(out,'browser-input-guides.png')});
  await page.getByRole('button',{name:'Back to editing',exact:true}).click();
  await api('/board-preferences',{language:'zh-CN'},'PUT');await page.reload();await page.locator('.psdParticipation').waitFor();await show();assert.match(await page.locator('.psdParticipation>summary').innerText(),/参与 AI 计算/);
  assert(await page.getByRole('checkbox',{name:'参与 AI: Depth',exact:true}).isChecked());
  await page.getByRole('button',{name:'恢复默认',exact:true}).click();assert(!await page.getByRole('checkbox',{name:'参与 AI: Depth',exact:true}).isChecked());
  await page.screenshot({path:path.join(out,'browser-layer-settings-zh.png')});assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'browser-verified.json'),JSON.stringify({defaults:true,independentHiddenVisibility:true,autosave:true,undoRedo:true,inheritedSettings:true,realPreflightGuides:true,resetDefaults:true,localized:true,pageErrors:errors,realModelCalls:0},null,2));
  console.log('PASS: PSD participation defaults, persistence, Undo/Redo, inheritance, actual preflight guide preview, Chinese and reset. No model calls.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
