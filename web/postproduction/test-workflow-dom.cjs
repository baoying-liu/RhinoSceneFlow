// Component event tests in jsdom with a mocked raster context, NOT browser visual QA.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'../..'),record=JSON.parse(fs.readFileSync(path.join(root,'artifacts/workflow021-http-latest.json')));
const base='http://127.0.0.1:'+record.port,errors=[];
const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!String(e.message).includes('navigation'))errors.push(e.stack);});vc.on('error',(...v)=>errors.push(v.join(' ')));
const dom=new JSDOM('<!doctype html><div id="root"></div>',{url:base+'/#token=workflow-fixture-token',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});
const w=dom.window;w.fetch=(url,options)=>fetch(new URL(url,base),options);w.crypto.randomUUID=require('node:crypto').randomUUID;
w.URL.createObjectURL=URL.createObjectURL;w.URL.revokeObjectURL=URL.revokeObjectURL;
w.ResizeObserver=class{constructor(cb){this.cb=cb;}observe(){this.cb([{contentRect:{width:900,height:600}}]);}disconnect(){}};
w.IntersectionObserver=class{constructor(cb){this.cb=cb;}observe(){this.cb([{isIntersecting:true}]);}disconnect(){}};
w.HTMLElement.prototype.scrollIntoView=function(){};
const capture=new WeakMap();w.HTMLElement.prototype.setPointerCapture=function(id){capture.set(this,id);};w.HTMLElement.prototype.hasPointerCapture=function(id){return capture.get(this)===id;};w.HTMLElement.prototype.releasePointerCapture=function(){capture.delete(this);};
w.HTMLAnchorElement.prototype.click=function(){this.dataset.testDownloaded='true';};
w.Image=class{constructor(){this.width=640;this.height=480;this.naturalWidth=640;this.naturalHeight=480;this.complete=true;this.nodeName='IMG';}set src(value){this._src=value;queueMicrotask(()=>this.onload?.());}get src(){return this._src;}};
w.HTMLCanvasElement.prototype.getContext=function(){const canvas=this;return new Proxy({canvas,measureText:()=>({width:80}),getImageData:()=>({data:new Uint8ClampedArray(4)}),createImageData:()=>({data:new Uint8ClampedArray(4)}),getLineDash:()=>[],createLinearGradient:()=>({addColorStop(){}}),createPattern:()=>({}),getTransform:()=>({a:1,b:0,c:0,d:1,e:0,f:0})},{get:(o,k)=>k in o?o[k]:(()=>{}),set:(o,k,v)=>(o[k]=v,true)});};
w.HTMLCanvasElement.prototype.toDataURL=()=>'';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,description){for(let i=0;i<120;i++){if(fn())return;await wait(50);}throw Error('Timed out: '+description+'\n'+w.document.body.textContent+'\n'+errors.join('\n'));}
function click(selector){const el=w.document.querySelector(selector);assert(el,selector);el.dispatchEvent(new w.MouseEvent('click',{bubbles:true}));}
function select(el,value){Object.getOwnPropertyDescriptor(w.HTMLSelectElement.prototype,'value').set.call(el,value);el.dispatchEvent(new w.Event('change',{bubbles:true}));}
function button(text){return [...w.document.querySelectorAll('button')].find(b=>b.textContent.trim()===text);}
async function api(p,o){const r=await fetch(base+'/api'+p,{...o,headers:{Authorization:'Bearer workflow-fixture-token','Content-Type':'application/json'}});if(!r.ok)throw Error(await r.text());return r.json();}
(async()=>{
 await api('/board-preferences',{method:'PUT',body:JSON.stringify({language:'en',lastBoard:record.board})});
 const style=w.document.createElement('style');style.textContent=fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/board.css'),'utf8');w.document.head.append(style);
 w.eval(fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/board.js'),'utf8'));
 await until(()=>w.document.querySelectorAll('.resource').length===2,'source and child');
 await until(()=>w.document.querySelector('.contentFields'),'selection loaded');assert(!w.document.querySelector('.contentFields').disabled);assert(!button('Update image'));assert(button('Create child'));assert(!button('Create sibling'));
 for(let i=0;i<3;i++){
  w.document.querySelectorAll('.resource')[1].click();await until(()=>button('Create sibling'),'child selected');
  click('.modeSwitch button:nth-child(2)');await until(()=>w.document.querySelector('.konvajs-content'),'canvas mount');
  w.document.querySelectorAll('.resource')[0].click();await wait(80);
  click('.modeSwitch button:first-child');await until(()=>w.document.querySelector('.comparison.currentPreview'),'source preview restored');
  assert.equal(w.document.querySelector('.selectedTitle strong').textContent,'Architecture.psd');
 }
 w.document.querySelectorAll('.resource')[1].click();await until(()=>button('Unlock editing'),'locked child');
 button('Unlock editing').click();await until(()=>!w.document.querySelector('.contentFields').disabled,'unlock');
 const preset=[...w.document.querySelectorAll('.inspector select')].find(el=>[...el.options].some(o=>o.value==='concept'));
 select(preset,'concept');await until(()=>w.document.querySelector('.resource.draft'),'yellow draft');await wait(1400);
 let b=await api('/boards/'+record.board),n=b.nodes.find(n=>n.id===record.child);assert(n.dirty);assert.equal(n.params.freedom,55);
 button('Restore task settings').click();await until(()=>w.document.querySelector('.contentFields').disabled,'rollback locked');
 b=await api('/boards/'+record.board);n=b.nodes.find(n=>n.id===record.child);assert(!n.dirty);assert.equal(n.params.freedom,15);
 button('Create sibling').click();await until(()=>w.document.querySelector('.pendingBoard'),'pending sibling board');
 b=await api('/boards/'+record.board);n=b.nodes.find(n=>n.id===b.selectedId);assert(n.pending);assert.equal(n.params.prompt,'');assert.equal(n.parentId,record.original);
 assert.equal(w.document.querySelectorAll('.resource').length,3);assert(button('Update image').disabled);
 await until(()=>w.document.querySelector('.comparison.currentPreview>img'),'draft input on right');assert.equal(w.document.querySelectorAll('.comparison.currentPreview img').length,1);assert(w.document.querySelector('.divider'));assert(!w.document.querySelector('.comparison.currentPreview canvas'));
 const blank=w.document.querySelector('.pendingBoard'),input=w.document.querySelector('.comparison.currentPreview>img');assert.equal(w.getComputedStyle(blank).backgroundColor,'rgb(255, 255, 255)');assert.equal(blank.style.clipPath,'inset(0 50% 0 0)');assert.equal(input.style.clipPath,'inset(0 0 0 50%)');
 const toggle=w.document.querySelector('.treeToggle'),toggleStyle=w.getComputedStyle(toggle);assert.equal(toggleStyle.opacity,'1');assert.equal(toggleStyle.position,'static');
 w.document.querySelector('.treeToggle').click();await until(()=>w.document.querySelectorAll('.resource').length===1,'tree collapse');
 w.document.querySelector('.treeToggle').click();await until(()=>w.document.querySelectorAll('.resource').length===3,'tree expand');
 // Synthetic metadata publication exercises the same-node draft→result transition, no model called.
 await wait(1400);const fixturePath=path.join(record.folder,'boards',record.board,'board.json'),fixture=JSON.parse(fs.readFileSync(fixturePath));
 const published=fixture.nodes.find(n=>n.id===fixture.selectedId);assert(published.pending);published.pending=false;published.locked=true;published.dirty=false;published.stage='whole';published.source={syntheticFixture:true};fixture.revision++;
 const temp=fixturePath+'.fixture';fs.writeFileSync(temp,JSON.stringify(fixture));fs.renameSync(temp,fixturePath);
 await until(()=>!w.document.querySelector('.pendingBoard')&&w.document.querySelector('.comparison.currentPreview canvas'),'same-node result preview');
 await until(()=>w.document.querySelector('.divider'),'result comparison restored');
 assert(!errors.length,errors.join('\n'));
 const report={componentHarness:true,realBrowserVisualQA:false,repeatedSelectionAndModes:true,sourceSettingsEditable:true,extensionShown:true,lockEnforced:true,draftAutosave:true,discardRestores:true,siblingWhiteboard:true,treeCollapse:true,blankLeftInputRight:true,visibleTreeControls:true,sameNodeResultTransition:true,consoleErrors:errors};
 fs.writeFileSync(path.join(record.folder,'dom-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});


