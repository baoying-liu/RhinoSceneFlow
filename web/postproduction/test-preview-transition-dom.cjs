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
 await api('/board-preferences',{method:'PUT',body:JSON.stringify({language:'en',lastBoard:record.board,listWheel:'navigate'})});
 const boardBefore=await api('/boards/'+record.board),child=boardBefore.nodes.find(n=>n.id===record.child),nativeFetch=w.fetch;let release;
 w.fetch=(url,options)=>String(url).includes('/assets/'+child.preview)&&!String(url).includes('?thumb=')?new Promise(resolve=>{release=()=>nativeFetch(url,options).then(resolve);}):nativeFetch(url,options);
 let measureCount=0;w.ResizeObserver=class{constructor(cb){this.cb=cb;}observe(el){if(el.classList.contains('viewerMat'))measureCount++;this.cb([{contentRect:{width:1400,height:900}}]);}disconnect(){}};
 const style=w.document.createElement('style');style.textContent=fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/board.css'),'utf8');w.document.head.append(style);
 w.eval(fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/board.js'),'utf8'));
 await until(()=>w.document.querySelector('.currentPreview')?.dataset.node===record.original,'source preview');const viewport=w.document.querySelector('.viewerMat'),slot=w.document.querySelector('.comparisonSlot');assert.equal(slot.style.width,'1400px');assert.equal(w.document.querySelector('.currentPreview').style.width,'1200px');
 w.document.querySelectorAll('.resource')[1].click();await until(()=>release,'child load requested');await wait(60);assert.strictEqual(w.document.querySelector('.viewerMat'),viewport);assert.equal(w.document.querySelector('.currentPreview').dataset.node,record.original,'keep old image while decoding');assert.equal(w.document.querySelector('.currentPreview').style.width,'1200px');assert.equal(measureCount,1);
 // A late response cannot replace a newer selected preview.
 w.document.querySelectorAll('.resource')[0].click();await wait(30);release();await wait(220);assert.equal(w.document.querySelector('.currentPreview').dataset.node,record.original);
 w.document.querySelectorAll('.resource')[1].click();await until(()=>w.document.querySelector('.currentPreview')?.dataset.node===record.child,'child ready');assert.strictEqual(w.document.querySelector('.viewerMat'),viewport);assert.equal(measureCount,1);assert.equal(w.document.querySelector('.currentPreview').style.width,'1200px');assert(w.document.querySelector('.outgoingPreview'));assert(w.document.querySelector('.currentPreview').classList.contains('previewFade'));
 const animation=w.getComputedStyle(w.document.querySelector('.previewFade')).animation;assert(/(?:140ms|0?\.14s)/.test(animation),animation);assert(!animation.includes('scale'));await wait(220);assert(!w.document.querySelector('.outgoingPreview'));assert.equal(w.document.querySelector('.currentPreview').style.width,'1200px');
 button('Smooth').click();await until(()=>w.document.querySelectorAll('.feedCard').length===2,'smooth cards');const cards=[...w.document.querySelectorAll('.feedCard')];assert(!cards[0].querySelector('.divider'));const feed=cards[1].querySelector('.feedImage');await until(()=>feed.querySelector('.feedInput')&&feed.querySelector('canvas'),'generated comparison images');const divider=feed.querySelector('.divider');assert(divider,'generated children must have a wipe');assert.equal(feed.querySelector('canvas').style.clipPath,'inset(0 50% 0 0)');assert.equal(feed.querySelector('.feedInput').style.clipPath,'inset(0 0 0 50%)');feed.getBoundingClientRect=()=>({left:100,top:0,width:400,height:300});
 function pointer(type,x){const e=new w.MouseEvent(type,{bubbles:true,clientX:x,button:0});Object.defineProperty(e,'pointerId',{value:7});divider.dispatchEvent(e);}
 pointer('pointerdown',300);pointer('pointermove',200);pointer('pointerup',200);await until(()=>divider.style.left==='25%','smooth generated wipe');assert.equal(feed.querySelector('canvas').style.clipPath,'inset(0 75% 0 0)');assert.equal(feed.querySelector('.feedInput').style.clipPath,'inset(0 0 0 25%)');
 const after=await api('/boards/'+record.board);assert.deepEqual(after.nodes,boardBefore.nodes);assert(!errors.length,errors.join('\n'));const report={jsdomComponentHarness:true,realBrowserVisualQA:false,persistentViewport:true,measuredOnce:true,noFallbackSizeOnSwitch:true,decodeBeforeSwap:true,lateResponseIgnored:true,fadeMilliseconds:140,outgoingRemoved:true,generatedFeedWipe:true,feedWipeDrag:true,sourceWithoutParentHasNoWipe:true,nodeDataUnchanged:true,consoleErrors:errors};fs.writeFileSync(path.join(record.folder,'preview-transition-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
