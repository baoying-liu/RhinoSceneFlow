const fragment = new URLSearchParams(location.hash.slice(1));
if(fragment.has('token')) sessionStorage.setItem('sceneflow-post-token',fragment.get('token'));
const initialProject=fragment.get('project');
history.replaceState(null,'',location.pathname);
const token=sessionStorage.getItem('sceneflow-post-token')||'';
const $=id=>document.getElementById(id);
let project=null, plan=null, preview=null, urls=[], jobId=null, selectedTile=null, polling=false;
let runs=[], currentRun=null, resultImage=null, maskImage=null, styleImage=null, baseImage=null, runUrls=[], loadedRunKey='';
async function api(path, options={}){
  const headers={Authorization:'Bearer '+token,...options.headers};
  if(options.body && !(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body);}
  const response=await fetch('/api'+path,{...options,headers});
  if(!response.ok){let error;try{error=(await response.json()).detail;}catch{error=response.statusText;}throw Error(typeof error==='string'?error:JSON.stringify(error));}
  return response;
}
async function json(path,options){return (await api(path,options)).json();}
function notice(text,error=false){$('notice').textContent=text;$('notice').className=error?'error':'';}
function run(action){return async()=>{try{await action();}catch(error){notice(error.message,true);}};}
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
async function refreshProjects(select){const entries=await json('/projects');$('projects').replaceChildren(new Option('选择项目',''),...entries.map(p=>new Option(p.name+' · '+({ready:'就绪',importing:'导入中',failed:'失败',cancelled:'已取消',interrupted:'已中断'}[p.status]||p.status),p.id)));$('projects').value=select||project?.id||'';}
async function blobUrl(path){const blob=await (await api(path)).blob();const url=URL.createObjectURL(blob);urls.push(url);return url;}
function revoke(){for(const url of urls)URL.revokeObjectURL(url);urls=[];}
async function openProject(id,runId=null){
  const state=await json('/projects/'+id);if(project?.id!==id){currentRun=null;loadedRunKey='';resultImage=null;maskImage=null;styleImage=null;baseImage=null;for(const url of runUrls)URL.revokeObjectURL(url);runUrls=[];}project=state;preview=null;plan=null;revoke();
  $('projectName').textContent=state.name;$('message').value='';$('layers').replaceChildren();$('messages').replaceChildren();
  $('prompt').value=state.settings.prompt;$('size').value=state.settings.size;$('overlap').value=state.settings.overlap;
  if(state.context)$('documentInfo').textContent='来自 Rhino · '+(state.context.documentName||state.context.documentPath||'未命名文档');else $('documentInfo').textContent='独立导入';
  renderMessages();
  if(state.status!=='ready'){notice(state.error||'PSD 正在导入…');draw();return;}
  notice('预览由 PSD 合成。先测试一个分块，确认效果后再处理整图；输出为完整 PNG。');$('documentInfo').textContent+=' · '+state.document.width+' × '+state.document.height;
  $('layerCount').textContent=state.document.layers.length;
  const ordered=[];function visit(parent){for(const layer of state.document.layers.filter(l=>l.parent===parent).reverse()){ordered.push(layer);if(layer.group)visit(layer.id);}}visit(null);
  for(const layer of ordered){
    // Depth is derived from the original hierarchy, not from reversed presentation order.
    let depth=0,parent=layer.parent;while(parent){depth++;parent=state.document.layers.find(l=>l.id===parent)?.parent;}
    const row=element('div',undefined,'layer');row.style.paddingLeft=(depth*12)+'px';
    const top=element('div',undefined,'layerTop');
    if(layer.thumbnail){const img=element('img');img.alt='';img.src=await blobUrl('/projects/'+id+'/media/'+layer.thumbnail);top.append(img);}
    const title=element('div',undefined,'layerName');title.append(element('div',(layer.group?'▾ ':'')+layer.name),element('small',(layer.effectiveVisible?'可见':'隐藏')+' · '+Math.round(layer.opacity/255*100)+'% · '+layer.blend));top.append(title);row.append(top);
    const role=element('select');role.dataset.layer=layer.id;role.setAttribute('aria-label',layer.name+'的用途');
    for(const [value,label] of Object.entries({generate:'可修改',reference:'仅作参考',preserve:'保持原样',exclude:'排除'}))role.add(new Option(label,value));
    role.value=state.settings.roles[layer.id]||layer.role;
    if(layer.group)role.onchange=()=>{const descendants=new Set([layer.id]);for(const child of state.document.layers)if(descendants.has(child.parent))descendants.add(child.id);for(const control of document.querySelectorAll('[data-layer]'))if(descendants.has(control.dataset.layer))control.value=role.value;};
    row.append(role);$('layers').append(row);
  }
  preview=new Image();preview.src=await blobUrl('/projects/'+id+'/media/preview.png');await preview.decode();
  plan=await json('/projects/'+id+'/plan');selectedTile=null;await refreshRuns(runId||state.latestRun);draw();
}
function renderMessages(){
  $('messages').replaceChildren();
  for(const message of project.messages){
    const bubble=element('div',message.text,'bubble '+message.role);
    if(message.prompt){const use=element('button','采用这份描述');use.onclick=()=>{if(message.revision!==project.revision){notice('图层或参数已变动。可先检查建议，再保存当前描述。');}$('prompt').value=message.prompt;document.querySelector('.advanced').open=true;};bubble.append(use);}
    $('messages').append(bubble);
  }
  $('messages').scrollTop=$('messages').scrollHeight;
}
function draw(){
  const canvas=$('canvas'),ctx=canvas.getContext('2d');
  if(!preview){ctx.clearRect(0,0,canvas.width,canvas.height);$('emptyCanvas').hidden=false;return;}
  const mode=$('viewMode').value;
  let original=baseImage||preview,shown=mode==='mask'&&maskImage?maskImage:mode==='style'&&styleImage?styleImage:mode==='result'&&resultImage?resultImage:original;
  $('emptyCanvas').hidden=true;canvas.width=shown.width;canvas.height=shown.height;ctx.drawImage(shown,0,0);
  if(mode==='compare'&&resultImage){ctx.save();ctx.beginPath();ctx.rect(0,0,canvas.width*Number($('wipe').value)/100,canvas.height);ctx.clip();ctx.drawImage(resultImage,0,0,canvas.width,canvas.height);ctx.restore();ctx.strokeStyle='#e5ba64';ctx.beginPath();ctx.moveTo(canvas.width*Number($('wipe').value)/100,0);ctx.lineTo(canvas.width*Number($('wipe').value)/100,canvas.height);ctx.stroke();}
  const sx=shown.width/project.document.width,sy=shown.height/project.document.height;
  const visibleTiles=mode!=='original'&&currentRun?currentRun.tiles:(plan?.tiles||[]);
  if($('grid').checked&&plan&&mode!=='style'){
    ctx.lineWidth=1.4;ctx.font=Math.max(12,preview.width/90)+'px Segoe UI';
    for(const tile of visibleTiles){const [x,y,r,b]=tile.core;ctx.strokeStyle='#638b39';ctx.strokeRect(x*sx,y*sy,(r-x)*sx,(b-y)*sy);ctx.fillStyle='#102c19';ctx.fillText(String(tile.id),x*sx+6,y*sy+18);}
    if(selectedTile){const [x,y,r,b]=selectedTile.context;ctx.strokeStyle='#e39c3e';ctx.lineWidth=3;ctx.strokeRect(x*sx,y*sy,(r-x)*sx,(b-y)*sy);}
  }
  $('tileInfo').textContent=selectedTile?'分块 '+selectedTile.id+' · 回填区域 ['+selectedTile.core.join(', ')+'] · 上下文 ['+selectedTile.context.join(', ')+']':visibleTiles.length+' 个分块 · 点击查看回填区域和上下文';
  $('requestEstimate').textContent=plan?'整图最多 '+(plan.tiles.length+1)+' 次生图；可复用图块与空白区域会减少请求。':'';
  const entry=currentRun?.tiles.find(t=>t.id===selectedTile?.id);
  $('inspectTile').disabled=!entry?.image;$('acceptTile').disabled=polling||entry?.status!=='review';$('retryTile').disabled=polling||!['review','failed'].includes(entry?.status);$('testTile').disabled=polling||!selectedTile;
  if(['result','compare'].includes(mode)&&!resultImage)$('resultInfo').textContent='尚无已合并结果，当前显示底图。';
}
async function save(){
  if(!project||project.status!=='ready')throw Error('请先选择已解析的 PSD。');
  const roles={};for(const control of document.querySelectorAll('[data-layer]'))roles[control.dataset.layer]=control.value;
  const state=await json('/projects/'+project.id+'/settings',{method:'PUT',body:{revision:project.revision,size:Number($('size').value),overlap:Number($('overlap').value),roles,prompt:$('prompt').value}});
  project={...project,...state};plan=await json('/projects/'+project.id+'/plan');selectedTile=null;draw();
}
async function pollJob(id,runId=null){
  jobId=id;polling=true;$('cancel').hidden=false;$('stopGeneration').hidden=!runId;$('send').disabled=true;$('projects').disabled=true;$('testTile').disabled=true;$('generateAll').disabled=true;
  try{
    while(true){
      const job=await json('/jobs/'+id);$('jobStatus').textContent=job.stage+' · 已用 '+Math.max(0,Math.floor(Date.now()/1000-job.started))+' 秒';$('chatStatus').textContent=job.kind==='chat'?job.stage:'';
      if(job.kind==='generation'){runId=runId||currentRun?.id;await refreshRuns(runId);$('runStatus').textContent=job.stage;}
      if(!['queued','running'].includes(job.status)){
        await openProject(job.project,runId);await refreshProjects(job.project);
        if(job.status==='failed')notice(job.stage,true);else if(job.status==='cancelled')notice('任务已取消，可以重试。');
        break;
      }
      await new Promise(resolve=>setTimeout(resolve,1000));
    }
  }finally{polling=false;jobId=null;$('cancel').hidden=true;$('stopGeneration').hidden=true;$('send').disabled=false;$('projects').disabled=false;$('generateAll').disabled=false;draw();}
}
const labels={pending:'待处理',running:'生成中',completed:'已完成',failed:'失败',review:'待检查',skipped:'空白跳过',queued:'排队',partial:'部分完成',cancelled:'已取消',interrupted:'已中断'};
async function loadRunImage(kind){try{const response=await api('/projects/'+project.id+'/runs/'+currentRun.id+'/image/'+kind);const url=URL.createObjectURL(await response.blob());runUrls.push(url);const image=new Image();image.src=url;await image.decode();return image;}catch{return null;}}
async function refreshRuns(prefer){
  runs=await json('/projects/'+project.id+'/runs');const selected=prefer||currentRun?.id||runs[0]?.id;
  $('runs').replaceChildren(...(runs.length?runs.map(r=>new Option(new Date(r.created*1000).toLocaleTimeString()+' · '+(r.mode==='tile'?'单块测试':'整图')+' · '+(labels[r.status]||r.status),r.id)):[new Option('尚无处理版本','')]));
  currentRun=runs.find(r=>r.id===selected)||runs[0]||null;$('runs').value=currentRun?.id||'';
  const key=(currentRun?.id||'')+'|'+(currentRun?.output?.image||'')+'|'+!!currentRun?.style;
  if(key!==loadedRunKey){for(const url of runUrls)URL.revokeObjectURL(url);runUrls=[];loadedRunKey=key;resultImage=null;maskImage=null;styleImage=null;baseImage=null;
    if(currentRun)[baseImage,maskImage,styleImage,resultImage]=await Promise.all(['base','mask','style','result'].map(loadRunImage));}
  $('tileStates').replaceChildren();
  if(currentRun){for(const tile of currentRun.tiles){const button=element('button',tile.id+' · '+(labels[tile.status]||tile.status)+(tile.reusedFrom?' ↺':''),'tileState '+tile.status);button.title=tile.error||tile.quality?.note||'';button.onclick=()=>{selectedTile=tile;draw();$('runStatus').textContent='图块 '+tile.id+' · '+(tile.error||tile.quality?.note||labels[tile.status]);};$('tileStates').append(button);}
    $('runStatus').textContent=currentRun.stage;
    $('resultInfo').textContent=(currentRun.mode==='tile'?'单块测试；其他区域保留底图':'整图版本')+' · '+currentRun.tiles.filter(t=>t.status==='completed').length+'/'+currentRun.tiles.length+' 块完成'+(currentRun.revision!==project.revision?' · 来自历史配置':'');
  }else{$('resultInfo').textContent='';$('runStatus').textContent='先采用或填写整体处理描述，再测试一个分块。';}
  $('downloadPng').disabled=!currentRun?.output;$('resumeRun').disabled=!currentRun||polling&&!currentRun?.output;
  draw();
}
async function generate(mode){
  if(polling)throw Error('请先完成或取消当前任务。');const selected=selectedTile;await save();
  if(mode==='tile'&&(!selected||!plan.tiles.some(t=>t.id===selected.id&&JSON.stringify(t.context)===JSON.stringify(selected.context))))throw Error('请先保存分块设置，再点击一个分块进行测试。');
  const result=await json('/projects/'+project.id+'/generate',{method:'POST',body:{revision:project.revision,mode,tileId:selected?.id,styleRunId:$('reuseStyle').checked?currentRun?.id:null,edgeGuard:Number($('edgeGuard').value),colorMatch:$('colorMatch').checked}});
  $('viewMode').value='compare';await pollJob(result.job,result.run);
}
$('projects').onchange=run(async()=>{if($('projects').value)await openProject($('projects').value);});
$('refreshProjects').onclick=run(async()=>{await refreshProjects();if(project)await openProject(project.id);});
$('upload').onchange=run(async()=>{if(polling)throw Error('请先完成当前任务。');const file=$('upload').files[0];if(!file)return;const data=new FormData();data.append('file',file);notice('正在上传 PSD 到本机工作台…');const result=await json('/upload',{method:'POST',body:data});await openProject(result.project);await refreshProjects(result.project);await pollJob(result.job);$('upload').value='';});
$('importPath').onclick=run(async()=>{if(polling)throw Error('请先完成当前任务。');const result=await json('/import',{method:'POST',body:{path:$('path').value}});await openProject(result.project);await refreshProjects(result.project);await pollJob(result.job);});
$('save').onclick=run(async()=>{await save();notice('配置已保存，分块已更新。');});
$('download').onclick=run(async()=>{await save();const url=await blobUrl('/projects/'+project.id+'/download');const link=element('a');link.href=url;link.download='SceneFlow-processing-plan.json';link.click();});
$('send').onclick=run(async()=>{const message=$('message').value.trim();if(!message)return;await save();const job=await json('/projects/'+project.id+'/chat',{method:'POST',body:{message,includePreview:$('includePreview').checked}});project.messages.push({role:'user',text:message});renderMessages();$('message').value='';await pollJob(job.id);});
$('cancel').onclick=run(async()=>{if(jobId)await json('/jobs/'+jobId+'/cancel',{method:'POST'});});
$('stopGeneration').onclick=$('cancel').onclick;
$('testTile').onclick=run(()=>generate('tile'));$('generateAll').onclick=run(()=>generate('all'));
$('runs').onchange=run(()=>refreshRuns($('runs').value));
$('viewMode').onchange=draw;$('wipe').oninput=draw;
$('resumeRun').onclick=run(async()=>{if(!currentRun||polling)return;const r=await json('/projects/'+project.id+'/runs/'+currentRun.id+'/resume',{method:'POST'});await pollJob(r.job,r.run);});
$('downloadPng').onclick=run(async()=>{if(!currentRun?.output)throw Error('还没有可下载的结果。');const response=await api('/projects/'+project.id+'/runs/'+currentRun.id+'/image/download');const url=URL.createObjectURL(await response.blob());const link=element('a');link.href=url;link.download=project.name+(currentRun.mode==='tile'?'-单块测试':'-AI结果')+'.png';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);});
$('inspectTile').onclick=run(async()=>{if(!currentRun||!selectedTile)throw Error('请先选择一个有结果的图块。');const tile=currentRun.tiles.find(t=>t.id===selectedTile.id);if(!tile?.image)throw Error('此分块还没有生成结果。');$('tileImage').src=await blobUrl('/projects/'+project.id+'/runs/'+currentRun.id+'/tile/'+tile.id);$('tileDetails').textContent='图块 '+tile.id+' · 原始 AI 图块，合并时会按蒙版恢复保留区域。'+(tile.quality?.generatedSize?'实际生成 '+tile.quality.generatedSize.join('×')+' → 回填 '+tile.quality.normalizedSize.join('×')+'。':'')+(tile.quality?.edgeDistanceP90!==null&&tile.quality?.edgeDistanceP90!==undefined?'轮廓距离 P90：'+tile.quality.edgeDistanceP90.toFixed(1)+' px。':'')+(tile.quality?.note||'');$('tileDialog').showModal();});
$('closeTile').onclick=()=>$('tileDialog').close();
$('acceptTile').onclick=run(async()=>{if(!currentRun||!selectedTile)throw Error('请选择待检查的分块。');const r=await json('/projects/'+project.id+'/runs/'+currentRun.id+'/accept/'+selectedTile.id,{method:'POST'});await pollJob(r.job,r.run);});
$('retryTile').onclick=run(async()=>{if(!currentRun||!selectedTile)throw Error('请选择失败或待检查的分块。');const r=await json('/projects/'+project.id+'/runs/'+currentRun.id+'/retry/'+selectedTile.id,{method:'POST'});await pollJob(r.job,r.run);});
$('grid').onchange=draw;
$('canvas').onclick=event=>{if(!plan||!preview||$('viewMode').value==='style')return;const visibleTiles=$('viewMode').value!=='original'&&currentRun?currentRun.tiles:plan.tiles;const rect=$('canvas').getBoundingClientRect(),x=(event.clientX-rect.left)/rect.width*project.document.width,y=(event.clientY-rect.top)/rect.height*project.document.height;selectedTile=visibleTiles.find(t=>x>=t.core[0]&&x<t.core[2]&&y>=t.core[1]&&y<t.core[3]);draw();};
$('shutdown').onclick=run(async()=>{await json('/shutdown',{method:'POST'});$('connection').textContent='服务已关闭';notice('项目已保存在本机，可从 Rhino 重新打开。');});
window.addEventListener('resize',draw);
run(async()=>{const status=await json('/status');$('connection').textContent='本机工作台 · '+status.version+(status.codexAvailable?' · Codex 可用':' · 未找到 Codex');await refreshProjects(initialProject);if(initialProject)await openProject(initialProject);else if($('projects').options.length>1){$('projects').selectedIndex=1;await openProject($('projects').value);}if(project?.activeJobs?.length){const active=await json('/jobs/'+project.activeJobs[0]);await pollJob(active.id,currentRun?.id);}})();
