// Real Edge + real PSD + owned raster worker; no image model request.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),f=JSON.parse(fs.readFileSync(path.join(root,'artifacts/emission/browser-fixture.json')));
const {chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const base=`http://127.0.0.1:${f.port}`,headers={Authorization:'Bearer emission-fixture-token','Content-Type':'application/json'};
 const api=async(p,body,method)=>{const r=await fetch(base+'/api'+p,{headers,method:method||(body?'POST':'GET'),body:body?JSON.stringify(body):undefined});assert(r.ok,await r.clone().text());return r.json()};
 const browser=await chromium.launch({channel:'msedge',headless:true});
 let page;try{
  page=await browser.newPage({viewport:{width:1500,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/#token=emission-fixture-token');await page.locator('.psdParticipation').waitFor();
  const show=async()=>{if(!await page.locator('.psdParticipation').evaluate(n=>n.open))await page.locator('.psdParticipation>summary').click()};await show();
  const emission=page.getByRole('checkbox',{name:'Use in AI: Emission · 自发光',exact:true});assert(await emission.isChecked());
  assert.equal(await page.locator('.psdLayer:not(.isGroup)').filter({hasText:'Emission'}).locator('select').first().inputValue(),'reference');
  await emission.uncheck();await page.waitForTimeout(1000);await page.reload();await page.locator('.psdParticipation').waitFor();await show();assert(!await emission.isChecked());
  await emission.check();await page.waitForTimeout(1000);await page.getByRole('button',{name:'Create proposal',exact:true}).click();
  await page.getByRole('button',{name:'Generate image…',exact:true}).waitFor();
  await page.locator('.contentFields textarea').fill('Make a night scene. Preserve both colored emitters and the opaque wall. Add restrained local light spill.');
  await page.getByRole('button',{name:'Generate image…',exact:true}).click();await page.locator('.inputCheck').waitFor({timeout:30000});
  assert.match(await page.locator('.psdGuideManifest').innerText(),/Emission/);
  const previous=await page.locator('.inputCheck img').getAttribute('src');await page.getByRole('button',{name:'PSD guides',exact:true}).click();
  await page.waitForFunction(old=>{const im=document.querySelector('.inputCheck img');return im&&im.getAttribute('src')!==old&&im.complete&&im.naturalWidth>0},previous);
  await page.screenshot({path:path.join(f.folder,'emission-preflight.png')});
  await page.getByRole('button',{name:'Back to editing',exact:true}).click();
  await api('/board-preferences',{language:'zh-CN'},'PUT');await page.reload();await page.locator('.psdParticipation').waitFor();await show();
  assert.match(await page.locator('.psdLayerList').innerText(),/自发光/);assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(f.folder,'verified.json'),JSON.stringify({realPsd:true,defaultReference:true,participationPersistence:true,actualPreflightGuide:true,localized:true,pageErrors:errors,realModelCalls:0},null,2));
  console.log('PASS: real emission PSD, Reference default, participation persistence, real preflight guide, localization and zero browser errors.');
 }catch(error){if(page){await page.screenshot({path:path.join(f.folder,'failure.png')});fs.writeFileSync(path.join(f.folder,'failure.txt'),await page.locator('body').innerText());}throw error;}finally{await browser.close();await api('/shutdown',{},'POST').catch(()=>{});}
})().catch(e=>{console.error(e);process.exitCode=1});
