const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const input=JSON.parse(fs.readFileSync(0,'utf8')),u=new URL(input.url),base=u.origin,token=u.searchParams.get('token');
 const html=fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/ChatKit/index.html'),'utf8').replace('__TOKEN__',token).replace('__BASE__',base);
 const out=path.join(root,'artifacts/theme-ui-0227'),browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:360,height:620}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route(url=>url.origin===base&&url.pathname==='/',route=>route.fulfill({contentType:'text/html',body:html}));
  await page.goto(base+'/?token='+token+'&scheme=dark&background=%2319382B&foreground=%23EAEAEA');
  await page.waitForFunction(()=>window.chatkitState?.ready||window.chatkitState?.error,{},{timeout:45000});
  const initial=await page.evaluate(()=>({state:window.chatkitState,background:getComputedStyle(document.body).backgroundColor,search:location.search}));
  assert.equal(initial.state.error,null);assert.equal(initial.state.ready,true);assert.equal(initial.search,'');assert.equal(initial.state.theme.colorScheme,'dark');
  const frame=page.frameLocator('openai-chatkit iframe');await frame.getByText('想创建什么材质或植物？',{exact:true}).waitFor();
  const composer=frame.getByRole('textbox');await composer.fill('主题切换测试草稿，不发送');
  await page.screenshot({path:path.join(out,'chat-dark-browser.png')});
  await page.evaluate(()=>{window.__themeFrame=document.querySelector('openai-chatkit').shadowRoot.querySelector('iframe');window.sceneFlowSetTheme({colorScheme:'light',background:'#eeeeee',foreground:'#222222'});});
  await page.waitForTimeout(700);assert.equal(await composer.inputValue().catch(()=>composer.innerText()),'主题切换测试草稿，不发送');
  assert(await page.evaluate(()=>window.__themeFrame===document.querySelector('openai-chatkit').shadowRoot.querySelector('iframe')));
  await page.screenshot({path:path.join(out,'chat-light-browser.png')});
  await page.evaluate(()=>window.sceneFlowSetTheme({colorScheme:'dark',background:'#19382B',foreground:'#EAEAEA'}));await page.waitForTimeout(500);
  assert.equal(await composer.inputValue().catch(()=>composer.innerText()),'主题切换测试草稿，不发送');assert.equal(errors.length,0,errors.join(';'));
  assert.notEqual(initial.state.theme.color.surface.foreground,'#EAEAEA');
  await page.emulateMedia({colorScheme:'light'});await page.goto(base+'/');await page.waitForFunction(()=>window.chatkitState?.ready);
  assert.equal(await page.evaluate(()=>window.chatkitState.theme.colorScheme),'light');
  await frame.getByRole('textbox').fill('系统主题草稿');await page.emulateMedia({colorScheme:'dark'});
  await page.waitForFunction(()=>window.chatkitState.theme.colorScheme==='dark');
  assert.equal(await frame.getByRole('textbox').inputValue().catch(()=>frame.getByRole('textbox').innerText()),'系统主题草稿');
  assert.equal(errors.length,0,errors.join(';'));
  const receipt={officialComponent:true,initialDark:true,rhinoBackground:initial.background,lightDarkRoundtrip:true,systemMediaFollow:true,draftPreserved:true,iframePreserved:true,urlCredentialsRemoved:true,pageErrors:errors,modelCalls:0};
  fs.writeFileSync(path.join(out,'chat-browser-verified.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
 }finally{await browser.close();}
})().catch(e=>{console.error(String(e.message).replace(/token=[^&\s'"<>]+/g,'token=[REDACTED]'));process.exit(1)});
