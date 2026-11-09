// Component event tests in jsdom with a mocked raster context, NOT browser visual QA.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve('../..'),record=JSON.parse(fs.readFileSync(path.join(root,'artifacts/boards020-latest.json')));
const base='http://127.0.0.1:'+record.port,errors=[];
const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!String(e.message).includes('navigation'))errors.push(e.stack);});vc.on('error',(...v)=>errors.push(v.join(' ')));
const dom=new JSDOM('<!doctype html><div id="root"></div>',{url:base+'/#token=board-fixture-ui-token',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});
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
async function api(p,o){const r=await fetch(base+'/api'+p,{...o,headers:{Authorization:'Bearer board-fixture-ui-token','Content-Type':'application/json'}});if(!r.ok)throw Error(await r.text());return r.json();}
(async()=>{
 await api('/board-preferences',{method:'PUT',body:JSON.stringify({language:'en',lastBoard:record.board})});
 w.eval(fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/board.js'),'utf8'));
 await until(()=>w.document.querySelectorAll('.resource').length>=2,'resource list');
 const before=await api('/boards/'+record.board),poses=before.nodes.map(n=>n.pose);
 click('.modeSwitch button:nth-child(2)');await until(()=>w.document.querySelector('.konvajs-content'),'canvas mount');
 await wait(1400);assert(!errors.length,errors.join('\n'));
 assert(w.document.querySelector('.minimap'));assert.equal(w.document.querySelectorAll('.resource').length,before.nodes.filter(n=>!n.archived).length);
 button('Show in list').click();await until(()=>w.document.querySelector('.comparison'),'list reveal');
 await until(()=>w.document.querySelector('.divider'),'comparison divider');
 const divider=w.document.querySelector('.divider'),box=w.document.querySelector('.comparison');box.getBoundingClientRect=()=>({left:100,top:0,width:400,height:300});
 function pointer(type,x){const e=new w.MouseEvent(type,{bubbles:true,clientX:x,button:0});Object.defineProperty(e,'pointerId',{value:7});divider.dispatchEvent(e);}
 pointer('pointerdown',300);pointer('pointermove',400);await until(()=>divider.style.left==='75%','direct divider drag');pointer('pointerup',600);await until(()=>divider.style.left==='100%','divider clamped to right');assert(!divider.hasPointerCapture(7));
 divider.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Home',bubbles:true}));await until(()=>divider.style.left==='0%','keyboard Home');
 await wait(1500);const after=await api('/boards/'+record.board);assert.deepEqual(after.nodes.map(n=>n.pose),poses);
 assert.equal(after.view.mode,'list');
 click('.headerActions button:last-child');await until(()=>w.document.querySelector('[role=dialog]'),'settings dialog');
 select(w.document.querySelector('[role=dialog] select'),'zh-CN');await until(()=>w.document.body.textContent.includes('AI 渲染工作台'),'Chinese language');
 assert.equal((await api('/board-preferences')).language,'zh-CN');
 click('[role=dialog] header button');await until(()=>!w.document.querySelector('[role=dialog]'),'close settings');
 const preset=[...w.document.querySelectorAll('.inspector select')].find(el=>[...el.options].some(o=>o.value==='concept'));
 assert(preset);select(preset,'concept');await wait(1600);
 const saved=await api('/boards/'+record.board),n=saved.nodes.find(n=>n.id===saved.selectedId);
 assert.equal(n.params.detail,80);assert.equal(n.params.freedom,55);assert(!errors.length,errors.join('\n'));
 const report={jsdomComponentHarness:true,realBrowserVisualQA:false,listCanvasSwitch:true,bidirectionalReveal:true,positionsUnchanged:true,minimap:true,directDividerEvents:true,languagePersisted:true,presetDefaultsSaved:true,consoleErrors:errors};
 fs.writeFileSync(path.join(record.folder,'dom-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
