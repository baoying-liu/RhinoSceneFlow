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
 await until(()=>w.document.querySelector('.contentFields'),'loaded');click('.modeSwitch button:nth-child(2)');await until(()=>w.Konva?.stages.length,'Konva canvas');
 const stage=w.Konva.stages[0],node=id=>stage.findOne('.image-node-'+id),port=()=>stage.findOne('.branch-port-'+record.child),line=()=>port().getParent().findOne('Arrow');
 await wait(1300);let b=await api('/boards/'+record.board),camera=b.view.camera;
 node(record.child).fire('click',{evt:new w.MouseEvent('click')},true);await wait(1200);assert.deepEqual((await api('/boards/'+record.board)).view.camera,camera);
 // Actual Konva drag handlers update connector endpoints BEFORE dragend, but never autosave each sample.
 const group=node(record.original),old=group.position(),before=Array.from(line().points());group.fire('dragstart',{evt:new w.MouseEvent('mousedown')},true);group.position({x:old.x+90,y:old.y+40});group.fire('dragmove',{evt:new w.MouseEvent('mousemove')},true);
 await wait(100);assert.equal(line().points()[0],before[0]+90);assert.equal(line().points()[1],before[1]+40);
 b=await api('/boards/'+record.board);assert.equal(b.nodes.find(n=>n.id===record.original).pose.x,old.x);
 group.fire('dragend',{evt:new w.MouseEvent('mouseup')},true);await until(()=>!w.document.querySelector('.errorBanner'),'drag');await wait(250);
 b=await api('/boards/'+record.board);assert.equal(b.nodes.find(n=>n.id===record.original).pose.x,old.x+90);
 // Canvas port fold is independent from the list fold.
 port().fire('click',{evt:new w.MouseEvent('click')},true);await until(()=>!node(record.child),'canvas child folded');assert.equal(w.document.querySelectorAll('.resource').length,2);
 w.document.querySelector('.treeToggle').click();await until(()=>w.document.querySelectorAll('.resource').length===1,'list folded');await wait(1200);
 port().fire('click',{evt:new w.MouseEvent('click')},true);await until(()=>node(record.child),'canvas child expanded');assert.equal(w.document.querySelectorAll('.resource').length,1);
 b=await api('/boards/'+record.board);assert.deepEqual(b.view.collapsed,[record.original]);assert.deepEqual(b.view.canvasCollapsed,[]);
 w.document.querySelector('.treeToggle').click();await until(()=>w.document.querySelectorAll('.resource').length===2,'list expanded');
 node(record.child).fire('click',{evt:new w.MouseEvent('click')},true);await until(()=>button('Unlock editing'),'child selected');button('Unlock editing').click();await until(()=>!w.document.querySelector('.contentFields').disabled,'unlocked');
 click('.tools button[aria-label="Generation frame"]');await wait(50);
 const rect=node(record.child).find(n=>n.getClassName()==='Rect'&&n.draggable())[0];assert(rect);const width=rect.width(),height=rect.height();
 rect.fire('transformstart',{evt:new w.MouseEvent('mousedown')},true);rect.scale({x:1.5,y:1.3});rect.fire('transform',{evt:new w.MouseEvent('mousemove')},true);await wait(100);assert.equal(rect.width(),width,'no transform feedback growth');
 rect.fire('transformend',{evt:new w.MouseEvent('mouseup')},true);await wait(1400);
 b=await api('/boards/'+record.board);assert.equal(b.nodes.find(n=>n.id===record.child).frame.width,width*1.5);
 function key(k){const event=new w.KeyboardEvent('keydown',{key:k,ctrlKey:true,bubbles:true,cancelable:true});w.dispatchEvent(event);assert(event.defaultPrevented);}
 key('z');await wait(250);b=await api('/boards/'+record.board);assert.equal(b.nodes.find(n=>n.id===record.child).frame.width,width);
 key('r');await wait(250);b=await api('/boards/'+record.board);assert.equal(b.nodes.find(n=>n.id===record.child).frame.width,width*1.5);
 // Explicit zoom button; selection itself remains stable.
 const beforeZoom=b.view.camera;button('Fit selected').click();await wait(1300);assert.notDeepEqual((await api('/boards/'+record.board)).view.camera,beforeZoom);
 // Right-button drag uses capture, changes only camera, and suppresses the context menu after movement.
 const host=w.document.querySelector('.canvasHost');let snapshot=await api('/boards/'+record.board);const cameraBeforePan=snapshot.view.camera,posesBeforePan=snapshot.nodes.map(n=>n.pose),historyBeforePan=snapshot.historyState.undo;
 function pointer(type,x,y){const event=new w.MouseEvent(type,{bubbles:true,cancelable:true,button:2,buttons:type==='pointerup'?0:2,clientX:x,clientY:y});Object.defineProperty(event,'pointerId',{value:77});host.dispatchEvent(event);}
 pointer('pointerdown',100,100);pointer('pointermove',220,155);await wait(60);pointer('pointerup',220,155);await wait(1300);
 snapshot=await api('/boards/'+record.board);assert.equal(snapshot.view.camera.x,cameraBeforePan.x+120);assert.equal(snapshot.view.camera.y,cameraBeforePan.y+55);assert.deepEqual(snapshot.nodes.map(n=>n.pose),posesBeforePan);assert.equal(snapshot.historyState.undo,historyBeforePan);assert(!w.document.querySelector('.contextMenu'));assert(!host.classList.contains('rightPanning'));
 // A right click without movement still opens the node menu.
 const hit=stage.getIntersection;stage.getIntersection=()=>node(record.original).findOne('Rect');pointer('pointerdown',100,100);pointer('pointerup',100,100);await until(()=>w.document.querySelector('.contextMenu'),'right-click menu preserved');stage.getIntersection=hit;click('.workToolbar');
 // List preview can scroll vertically; alternate wheel navigation is a persisted preference.
 click('.modeSwitch button:first-child');await until(()=>button('Smooth'),'smooth control');button('Smooth').click();await until(()=>w.document.querySelector('.previewScrollable'),'scrollable preview');const mat=w.document.querySelector('.previewScrollable');assert.equal(w.getComputedStyle(mat).overflowY,'auto');assert.equal(w.getComputedStyle(w.document.querySelector('.resourceList')).overflowY,'auto');
 click('.headerActions button:last-child');await until(()=>w.document.querySelector('[role=dialog]'),'settings');const wheelSelect=[...w.document.querySelectorAll('[role=dialog] select')].find(el=>[...el.options].some(o=>o.value==='navigate'));assert(wheelSelect);select(wheelSelect,'navigate');await until(()=>!w.document.querySelector('.previewScrollable'),'wheel mode persisted');assert.equal((await api('/board-preferences')).listWheel,'navigate');click('[role=dialog] header button');
 const previewMat=w.document.querySelector('.viewerMat');previewMat.dispatchEvent(new w.WheelEvent('wheel',{bubbles:true,deltaY:100}));await until(()=>button('Unlock editing')||button('Restore task settings'),'wheel selected next image');assert(w.document.querySelector('.selectedTitle strong').textContent!== 'Architecture.psd');
 click('.modeSwitch button:nth-child(2)');await until(()=>w.Konva.stages[0],'canvas restored');
 w.Konva.stages[0].findOne('.image-node-'+record.original).fire('click',{evt:new w.MouseEvent('click')},true);await wait(50);button('Delete').click();await until(()=>w.document.querySelector('[role=dialog]'),'delete confirmation');click('[role=dialog] .primary');await until(()=>w.document.querySelectorAll('.resource').length===0,'branch deleted');
 key('z');await until(()=>w.document.querySelectorAll('.resource').length===2,'delete undo');key('r');await until(()=>w.document.querySelectorAll('.resource').length===0,'delete redo');key('z');await until(()=>w.document.querySelectorAll('.resource').length===2,'restore');
 assert(!errors.length,errors.join('\n'));const report={jsdomKonvaEvents:true,realBrowserVisualQA:false,noZoomOnSelection:true,explicitFitSelected:true,liveConnectorDuringDrag:true,noAutosaveDuringDrag:true,independentFold:true,transformStable:true,ctrlZUndo:true,ctrlRRedo:true,deleteSubtreeUndoRedo:true,rightDragCameraOnly:true,rightClickMenu:true,listScroll:true,wheelNavigationSetting:true,consoleErrors:errors};
 fs.writeFileSync(path.join(record.folder,'layout-dom-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
