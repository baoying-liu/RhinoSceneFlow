// Event/geometry regression harness, not a real browser or a generated-image test.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..'),elements=new Map(),clips=[];
let canvasRect={left:330,top:120,width:600,height:450},resize;
function element(id){
  if(elements.has(id))return elements.get(id);
  const captures=new Set(),e={value:'',hidden:false,checked:false,style:{},attributes:{},clientLeft:1,clientTop:1,
    setAttribute(k,v){this.attributes[k]=String(v);},focus(){},
    hasPointerCapture(p){return captures.has(p);},setPointerCapture(p){captures.add(p);},
    releasePointerCapture(p){captures.delete(p);this.onlostpointercapture?.({pointerId:p});}};
  elements.set(id,e);return e;
}
const ctx=new Proxy({rect(x,y,w,h){clips.push(w);}}, {get:(o,k)=>o[k]||(()=>{})});
element('canvas').getContext=()=>ctx;element('canvas').getBoundingClientRect=()=>canvasRect;
element('viewport').getBoundingClientRect=()=>({left:100,top:100,width:1100,height:500});
element('wipe').value='50';element('viewMode').value='compare';
const sandbox={console,URLSearchParams,location:{hash:'',pathname:'/'},sessionStorage:{getItem(){return '';},setItem(){}},history:{replaceState(){}},
  document:{getElementById:element},window:{addEventListener(){}},ResizeObserver:class{constructor(cb){resize=cb;}observe(){}},
  setTimeout,clearTimeout};
vm.createContext(sandbox);
let source=fs.readFileSync(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction/app.js'),'utf8');
const start=source.indexOf("run(async()=>{const status=await json('/status');");assert(start>0);
vm.runInContext(source.slice(0,start),sandbox);
const run=s=>vm.runInContext(s,sandbox);
run("preview={width:1200,height:900};resultImage={width:1200,height:900};project={document:{width:1200,height:900}};plan={tiles:[]};draw();");
const handle=element('compareHandle'),wipe=element('wipe');
assert.equal(handle.hidden,false);assert.equal(handle.style.left,'529px');assert.equal(handle.style.top,'19px');assert.equal(handle.style.height,'450px');assert.equal(clips.at(-1),600);
function pointer(pointerId,clientX,button=0){return {pointerId,clientX,button,preventDefault(){},stopPropagation(){}};}
handle.onpointerdown(pointer(1,630));assert(handle.hasPointerCapture(1));
handle.onpointermove(pointer(1,780));assert.equal(+wipe.value,75);assert.equal(clips.at(-1),900);assert.equal(handle.style.left,'679px');
handle.onpointermove(pointer(2,480));assert.equal(+wipe.value,75);
handle.onpointermove(pointer(1,2000));assert.equal(+wipe.value,100);
handle.onpointermove(pointer(1,0));assert.equal(+wipe.value,0);
handle.onpointerup(pointer(1,480));assert.equal(+wipe.value,25);assert(!handle.hasPointerCapture(1));assert.equal(run('selectedTile'),null);
handle.onpointerdown(pointer(3,900,2));assert(!handle.hasPointerCapture(3));assert.equal(+wipe.value,25);
handle.onkeydown({key:'ArrowRight',preventDefault(){}});assert.equal(+wipe.value,26);
handle.onkeydown({key:'ArrowRight',shiftKey:true,preventDefault(){}});assert.equal(+wipe.value,36);
handle.onkeydown({key:'End',preventDefault(){}});assert.equal(+wipe.value,100);
handle.onkeydown({key:'Home',preventDefault(){}});assert.equal(+wipe.value,0);
wipe.value='50';wipe.oninput();canvasRect={left:450,top:140,width:300,height:225};resize();
assert.equal(handle.style.left,'499px');assert.equal(handle.style.height,'225px');assert.equal(handle.attributes['aria-valuenow'],'50');
handle.onpointerdown(pointer(4,600));handle.onpointercancel(pointer(4,600));assert(!handle.hasPointerCapture(4));
handle.onpointerdown(pointer(5,600));element('viewMode').value='original';element('viewMode').onchange();assert(handle.hidden);assert(wipe.disabled);assert(!handle.hasPointerCapture(5));
element('viewMode').value='compare';run('resultImage=null;draw();');assert(handle.hidden);assert(wipe.disabled);
const result={eventHarness:true,browserVerified:false,dragBothDirections:true,clampsOutsideImage:true,captureReleased:true,tileSelectionUnchanged:true,keyboard:true,letterboxAndResize:true,noResultHidden:true};
const output=path.join(root,'artifacts/compare0191');fs.mkdirSync(output,{recursive:true});fs.writeFileSync(path.join(output,'interaction-verified.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
