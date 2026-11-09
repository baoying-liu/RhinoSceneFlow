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
 const scrollCalls=[];w.HTMLElement.prototype.scrollIntoView=function(options){scrollCalls.push({element:this,options});};
 w.eval(fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/board.js'),'utf8'));
 await until(()=>w.document.querySelector('.comparison'),'single preview');assert.equal((await api('/board-preferences')).listWheel,'navigate');assert.equal(button('Smooth').getAttribute('aria-pressed'),'false');
 const original=(await api('/boards/'+record.board)).nodes.map(n=>({id:n.id,asset:n.asset,preview:n.preview,params:n.params,parentId:n.parentId}));
 function wheel(y){w.document.querySelector('.viewerMat').dispatchEvent(new w.WheelEvent('wheel',{bubbles:true,deltaY:y}));}
 wheel(100);await until(()=>w.document.querySelector('.selectedTitle strong').textContent!=='Architecture.psd','next image');await wait(350);wheel(-100);await until(()=>w.document.querySelector('.selectedTitle strong').textContent==='Architecture.psd','previous image');
 button('Smooth').click();await until(()=>w.document.querySelectorAll('.feedCard').length===2,'continuous images');assert.equal(button('Smooth').getAttribute('aria-pressed'),'true');assert.equal((await api('/board-preferences')).listWheel,'scroll');
 const feed=w.document.querySelector('.continuousPreview');assert.equal(w.getComputedStyle(feed).overflowY,'auto');assert.deepEqual([...feed.querySelectorAll('header strong')].map(n=>n.textContent),[...w.document.querySelectorAll('.resource strong')].map(n=>n.textContent));
 await until(()=>feed.querySelectorAll('.feedImage canvas').length===2,'two image previews');assert.equal(feed.querySelectorAll('.divider').length,1);
 feed.scrollTop=400;feed.dispatchEvent(new w.Event('scroll',{bubbles:true}));feed.dispatchEvent(new w.WheelEvent('wheel',{bubbles:true,deltaY:100}));await wait(100);assert.equal(w.document.querySelector('.selectedTitle strong').textContent,'Architecture.psd');
 const cards=[...feed.querySelectorAll('.feedCard')];scrollCalls.length=0;cards[1].click();await until(()=>w.document.querySelector('.selectedTitle strong').textContent!=='Architecture.psd','select from feed');assert(!scrollCalls.some(c=>c.element.classList.contains('feedCard')),'feed clicks must not force scrolling');
 w.document.querySelectorAll('.resource')[0].click();await until(()=>scrollCalls.some(c=>c.element===cards[0]),'sidebar locates in feed');assert.equal(cards[0].getAttribute('aria-current'),'true');
 cards[1].querySelector('button').click();await until(()=>!w.document.querySelector('.continuousPreview')&&w.document.querySelector('.comparison'),'single compare');assert.equal((await api('/board-preferences')).listWheel,'navigate');assert.equal(button('Smooth').getAttribute('aria-pressed'),'false');
 await wait(1200);const current=(await api('/boards/'+record.board)).nodes.map(n=>({id:n.id,asset:n.asset,preview:n.preview,params:n.params,parentId:n.parentId}));assert.deepEqual(current,original);
 assert(!errors.length,errors.join('\n'));const report={componentHarness:true,realBrowserVisualQA:false,defaultWheelPreviousNext:true,smoothToolbarToggle:true,continuousVerticalImages:true,onePreviewPerCard:true,scrollDoesNotChangeEditingTarget:true,cardSelectionNoJump:true,sidebarLocatesCard:true,singleCompareReturns:true,persistedChoice:true,pixelsAndParamsUnchanged:true,consoleErrors:errors};fs.writeFileSync(path.join(record.folder,'smooth-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
