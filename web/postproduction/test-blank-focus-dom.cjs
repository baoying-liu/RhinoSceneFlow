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
 await until(()=>button('Create child'),'source selected');button('Create child').click();await until(()=>w.document.querySelector('.pendingBoard'),'blank draft');await wait(100);
 let b=await api('/boards/'+record.board);const draft=b.nodes.find(n=>n.id===b.selectedId),draftId=draft.id;assert(draft.pending);
 const before=draft.asset,blank=w.document.querySelector('.pendingBoard'),input=w.document.querySelector('.comparison.currentPreview>img');assert(input);assert.equal(w.getComputedStyle(blank).backgroundColor,'rgb(255, 255, 255)');assert.equal(blank.style.clipPath,'inset(0 50% 0 0)');assert.equal(input.style.clipPath,'inset(0 0 0 50%)');assert.equal(w.document.querySelectorAll('.comparison.currentPreview canvas').length,0);assert(w.document.querySelector('.blankThumb'));
 const divider=w.document.querySelector('.divider'),bounds=w.document.querySelector('.comparison.currentPreview');bounds.getBoundingClientRect=()=>({left:100,top:0,width:400,height:300});
 function pointer(type,x){const e=new w.MouseEvent(type,{bubbles:true,clientX:x,button:0});Object.defineProperty(e,'pointerId',{value:7});divider.dispatchEvent(e);}
 pointer('pointerdown',300);pointer('pointermove',400);pointer('pointerup',400);await until(()=>divider.style.left==='75%','blank wipe drag');assert.equal(blank.style.clipPath,'inset(0 25% 0 0)');assert.equal(input.style.clipPath,'inset(0 0 0 75%)');
 click('.modeSwitch button:nth-child(2)');await until(()=>w.Konva?.stages.length,'canvas');let stage=w.Konva.stages[0];let group=stage.findOne('.image-node-'+draftId);assert.equal(group.findOne('.result-surface').fill(),'#ffffff');assert.equal(group.find('Image').length,0);
 // The left-hand checkbox controls sidebar focus, while direct canvas clicks never zoom.
 const checkbox=w.document.querySelector('.resourceOptions input');assert(checkbox.checked);checkbox.click();await until(()=>!w.document.querySelector('.resourceOptions input').checked,'auto locate off');assert.equal((await api('/board-preferences')).autoLocate,false);await wait(1300);
 let camera=(await api('/boards/'+record.board)).view.camera;w.document.querySelectorAll('.resource')[0].click();await wait(1200);assert.deepEqual((await api('/boards/'+record.board)).view.camera,camera);
 checkbox.click();await until(()=>w.document.querySelector('.resourceOptions input').checked,'auto locate on');w.document.querySelectorAll('.resource')[0].click();await wait(1300);assert.notDeepEqual((await api('/boards/'+record.board)).view.camera,camera);
 // Hide a canvas branch, then select its still-visible sidebar row: reveal and focus it.
 stage.findOne('.branch-port-'+draftId).fire('click',{evt:new w.MouseEvent('click')},true);await wait(250);assert((await api('/boards/'+record.board)).view.canvasCollapsed.includes(draftId));
 w.document.querySelectorAll('.resource')[2].click();await until(()=>stage.findOne('.image-node-'+draftId),'sidebar reveals collapsed branch');await wait(1300);b=await api('/boards/'+record.board);assert(!b.view.canvasCollapsed.includes(draftId));
 camera=b.view.camera;stage.findOne('.image-node-'+record.original).fire('click',{evt:new w.MouseEvent('click')},true);await wait(1200);assert.deepEqual((await api('/boards/'+record.board)).view.camera,camera);
 // Real CSS cascade: fold toggle is visible/static, distinct from hover-only locate buttons.
 const toggle=w.document.querySelector('.treeToggle'),computed=w.getComputedStyle(toggle);assert.equal(computed.position,'static');assert.equal(computed.opacity,'1');toggle.click();await until(()=>w.document.querySelectorAll('.resource').length===1,'list branch collapsed');assert.equal(toggle.textContent,'+');assert(stage.findOne('.image-node-'+draftId),'list collapse must not hide canvas branch');toggle.click();await until(()=>w.document.querySelectorAll('.resource').length===3,'list expanded');assert.equal(toggle.textContent,'−');
 click('.modeSwitch button:first-child');await until(()=>button('Smooth'),'list mode');button('Smooth').click();await until(()=>w.document.querySelectorAll('.feedCard').length===3,'smooth list');const pendingFeed=[...w.document.querySelectorAll('.feedCard')].find(el=>el.getAttribute('aria-label')===draft.name);await until(()=>pendingFeed.querySelector('.feedInput'),'smooth input');assert(pendingFeed.querySelector('.pendingBoard'));assert(pendingFeed.querySelector('.divider'));assert.equal(pendingFeed.querySelectorAll('canvas').length,0);
 b=await api('/boards/'+record.board);assert.equal(b.nodes.find(n=>n.id===draftId).asset,before);assert(!errors.length,errors.join('\n'));
 const report={jsdomKonvaAndCss:true,realBrowserVisualQA:false,blankLeftInputRight:true,blankWipeDrag:true,canvasPureWhiteNoImage:true,blankThumbnail:true,autoLocatePersisted:true,sidebarOptionControlsZoom:true,sidebarRevealsBranch:true,canvasClickNeverZooms:true,treeButtonsVisibleAndStatic:true,listFoldActuallyHidesDescendants:true,independentFold:true,smoothBlankComparison:true,inputPixelsUnchanged:true,consoleErrors:errors};fs.writeFileSync(path.join(record.folder,'blank-focus-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
