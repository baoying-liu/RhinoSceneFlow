// Real browser regression for restoring legacy task metadata and keyboard scope.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),cp=require('node:child_process');
const root=path.resolve(__dirname,'../..'),{chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
const f=JSON.parse(fs.readFileSync(path.join(root,'artifacts/workflow021-http-latest.json'))),prefix='/boards/'+f.board,base=`http://127.0.0.1:${f.port}`;
async function api(p){const r=await fetch(base+'/api'+p,{headers:{Authorization:'Bearer workflow-fixture-token'}});assert(r.ok);return r.json()}
(async()=>{
// Only an isolated fixture may seed an old saved configuration. No real image publication.
assert(f.folder.includes('artifacts')&&f.folder.includes('workflow021-http'));
cp.execFileSync(path.join(process.env.LOCALAPPDATA,'RhinoSceneFlow/chatkit-runtime/Scripts/python.exe'),['-X','utf8','-c',`import sys,json,uuid
sys.path.insert(0,${JSON.stringify(path.join(root,'src/RhinoSceneFlow.Plugin/PostProduction'))})
from board_store import Store
s=Store(${JSON.stringify(f.folder)});b=s.read(${JSON.stringify(f.board)});n=next(x for x in b['nodes'] if x['id']==${JSON.stringify(f.child)})
n['annotations']=[dict(id=uuid.uuid4().hex,kind='text',text='Keep this saved guidance',x=30,y=30,size=16,color='#123456',points=[],enabled=True,visible=True)];n['guideControls']=dict(enabled=True,specialEnabled=True);n['baseline']=s.configuration(b,n);n['baseline']['params'].pop('editScope',None);n['dirty']=False;n['locked']=True;b['selectedId']=n['id'];s.commit(b)
`]);
 const before=await api(prefix),browser=await chromium.launch({channel:'msedge',headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/#token=workflow-fixture-token');await page.locator('.guideLayers').waitFor();
 await page.locator('.guideLayers').getByRole('button',{name:'Unlock and redo this task',exact:true}).click();
 await page.locator('.guideLayers>header').getByRole('checkbox').click();await page.waitForFunction(()=>document.querySelector('.guideLayers>header input')?.checked===false);await page.locator('.guideGroupControls').getByRole('checkbox').click();await page.waitForFunction(()=>document.querySelector('.guideGroupControls input')?.checked===false);await page.locator('.guideLayers>header').getByRole('button').click();await page.waitForFunction(()=>document.querySelector('.guideLayers>header button')?.getAttribute('aria-pressed')==='false');
 await page.locator('.workflowManagement>summary').click();await page.getByRole('button',{name:'Restore task settings',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.contentFields')?.disabled);let b=await api(prefix),n=b.nodes.find(x=>x.id===f.child);
 assert.equal(n.guideControls.enabled,true);assert.equal(n.guideControls.specialEnabled,true);assert.equal(n.guideControls.visible,false);assert.equal(n.locked,true);assert.equal(n.dirty,false);assert.equal(n.params.editScope,'auto');
 await page.getByRole('button',{name:'▦ Canvas',exact:true}).click();await page.locator('.konvajs-content').waitFor();await page.waitForTimeout(1400);assert.equal(await page.getByRole('alert').count(),0,'Restoring legacy parameters must not break the next layout autosave');
 await page.getByRole('button',{name:'▤ List',exact:true}).click();await page.locator('.resource').first().click();const input=page.locator('.contentFields textarea');await input.focus();
 const key=await input.evaluate(el=>{const e=new KeyboardEvent('keydown',{key:'r',ctrlKey:true,bubbles:true,cancelable:true});el.dispatchEvent(e);return e.defaultPrevented});assert.equal(key,false,'Board redo must not capture text editing shortcuts');
 b=await api(prefix);for(const old of before.nodes){const fresh=b.nodes.find(n=>n.id===old.id);assert.equal(fresh.asset,old.asset);assert.equal(fresh.versionId,old.versionId)}assert.deepEqual(errors,[]);
 await page.screenshot({path:path.join(f.folder,'task-restoration-browser.png')});const report={realHeadlessEdge:true,legacyRestoreThenCanvasSave:true,groupGatesRestored:true,eyesUnchanged:true,noFalsePendingState:true,textRedoNotIntercepted:true,sourceUnchanged:true,modelCalls:0};fs.writeFileSync(path.join(f.folder,'task-restoration-browser-verified.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
