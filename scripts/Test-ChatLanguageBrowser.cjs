const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{
 const input=JSON.parse(fs.readFileSync(0,'utf8')),u=new URL(input.url),base=u.origin,token=u.searchParams.get('token');
 const html=fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/ChatKit/index.html'),'utf8').replace('__TOKEN__',token).replace('__BASE__',base);
 const out=path.join(root,'artifacts/presentation-fix-02216'),browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:360,height:620}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route(url=>url.origin===base&&url.pathname==='/',route=>route.fulfill({contentType:'text/html',body:html}));
  await page.goto(base+'/?token='+token+'&language=en&scheme=dark&background=%2319382B&foreground=%23EAEAEA');
  await page.waitForFunction(()=>window.chatkitState?.ready||window.chatkitState?.error,{},{timeout:45000});
  assert.equal(await page.evaluate(()=>window.chatkitState.error),null);
  const frame=page.frameLocator('openai-chatkit iframe');await frame.getByText('What material or plant would you like to create?',{exact:true}).waitFor();
  await frame.getByText('Exposed concrete',{exact:true}).waitFor();
  const composer=frame.getByRole('textbox');await composer.fill('Language-switch draft / do not send');
  await page.screenshot({path:path.join(out,'chat-english.png')});
  await page.evaluate(()=>{window.__languageFrame=document.querySelector('openai-chatkit').shadowRoot.querySelector('iframe');window.sceneFlowSetLanguage('zh');});
  await frame.getByText('想创建什么材质或植物？',{exact:true}).waitFor();
  assert.equal(await composer.inputValue().catch(()=>composer.innerText()),'Language-switch draft / do not send');
  assert(await page.evaluate(()=>window.__languageFrame===document.querySelector('openai-chatkit').shadowRoot.querySelector('iframe')));
  await page.evaluate(()=>{window.sceneFlowSetLanguage('en');window.sceneFlowSetTheme({colorScheme:'light',background:'#f1f3f1',foreground:'#1e241e'});});
  await frame.getByText('What material or plant would you like to create?',{exact:true}).waitFor();
  assert.equal(await composer.inputValue().catch(()=>composer.innerText()),'Language-switch draft / do not send');
  assert.equal(await page.evaluate(()=>window.chatkitState.language),'en');assert.equal(await page.evaluate(()=>location.search),'');assert.deepEqual(errors,[]);
  const receipt={officialComponent:true,englishUi:true,zhEnRoundtrip:true,draftPreserved:true,iframePreserved:true,themePreserved:true,urlCredentialsRemoved:true,modelCalls:0};
  fs.writeFileSync(path.join(out,'chat-language-verified.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
 }finally{await browser.close();}
})().catch(e=>{console.error(String(e.message).replace(/token=[^&\s'"<>]+/g,'token=[REDACTED]'));process.exit(1)});
