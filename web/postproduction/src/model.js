export const defaults={generationStage:'whole',prompt:'',preset:'detail',detail:65,freedom:15,blend:100,edgeGuard:1,tileSize:1024,overlap:128,outputSize:2048,roles:{},referencePurpose:'general'};
export const mutableNode=n=>Object.fromEntries(['id','name','pose','frame','params','annotations','hidden','archived'].map(k=>[k,n[k]]));
export function fitCamera(nodes,width,height){if(!nodes.length)return{x:40,y:60,scale:.8};const boxes=nodes.map(n=>({x:n.pose.x+n.frame.x,y:n.pose.y+n.frame.y,width:n.frame.width,height:n.frame.height}));const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y)),r=Math.max(...boxes.map(b=>b.x+b.width)),bottom=Math.max(...boxes.map(b=>b.y+b.height));const scale=Math.min(1.4,Math.max(.03,Math.min((width-100)/(r-x),(height-100)/(bottom-y))));return{x:(width-(r-x)*scale)/2-x*scale,y:(height-(bottom-y)*scale)/2-y*scale,scale};}
export function inFrame(owner,ref){const p=owner.pose,f=owner.frame,q=ref.pose;return ref.kind==='reference'&&!ref.deleted&&!ref.archived&&!ref.hidden&&q.x+q.width>p.x+f.x&&q.x<p.x+f.x+f.width&&q.y+q.height>p.y+f.y&&q.y<p.y+f.y+f.height;}
export function annotationInFrame(owner,a){if(a.enabled===false)return false;const f=owner.frame,p=a.points?.length?a.points:[[a.x||0,a.y||0,.5]];return Math.min(...p.map(q=>q[0]))<=f.x+f.width&&Math.max(...p.map(q=>q[0]))>=f.x&&Math.min(...p.map(q=>q[1]))<=f.y+f.height&&Math.max(...p.map(q=>q[1]))>=f.y;}
export function briefForPreset(p,preset){const v={faithful:[20,5],detail:[65,15],concept:[80,55]}[preset];return{...p,preset,detail:v[0],freedom:v[1]};}
export function assetPath(board,name){return '/boards/'+board+'/assets/'+name;}

export function tileEstimate(n){const p=n.params,scale=p.outputSize/Math.max(n.width,n.height),step=p.tileSize-p.overlap*2;return Math.ceil(Math.max(1,Math.round(n.width*scale))/step)*Math.ceil(Math.max(1,Math.round(n.height*scale))/step);}

export const editable=n=>!!n&&!n.locked&&!n.busy&&!n.archived;
export const nodeState=n=>n.inputChanged?'stale':n.pending||n.dirty?'draft':'clean';
export const stateColor=n=>nodeState(n)==='stale'?'#b79bea':nodeState(n)==='draft'?'#e6c362':null;
export function treeRows(nodes,collapsed,query=''){
 const ids=new Set(nodes.map(n=>n.id)),rows=[],seen=new Set();
 function visit(n,depth){if(seen.has(n.id))return;seen.add(n.id);rows.push({...n,depth});if(!collapsed.has(n.id))nodes.filter(c=>c.parentId===n.id).forEach(c=>visit(c,depth+1));}
 nodes.filter(n=>!ids.has(n.parentId)).forEach(n=>visit(n,0));return rows;
}

export const shownVersion=n=>n?.versions?.find(v=>v.versionId===n.checkout)||n;
// Visibility is presentation only; enabled remains the independent AI reference switch.
export const visibleEditReference=n=>n?.editReference&&n.editReference.visible!==false&&n.editReference.sourceAsset===n.asset&&!n.checkout&&!blankResult(n)?n.editReference:null;
export const frameBox=n=>({x:n.pose.x+n.frame.x,y:n.pose.y+n.frame.y,width:n.frame.width,height:n.frame.height});
export const overlaps=(a,b,gap=40)=>a.x<b.x+b.width+gap&&b.x<a.x+a.width+gap&&a.y<b.y+b.height+gap&&b.y<a.y+a.height+gap;
export function canvasGraph(nodes,collapsed=[]){
 const all=new Map(nodes.map(n=>[n.id,n])),images=nodes.filter(n=>n.kind==='image'&&!n.deleted&&!n.hidden&&!n.archived),live=new Set(images.map(n=>n.id)),parents=new Map();
 for(const n of images){let p=all.get(n.parentId),seen=new Set();while(p&&!live.has(p.id)&&!seen.has(p.id)){seen.add(p.id);p=all.get(p.parentId);}parents.set(n.id,p&&live.has(p.id)?p.id:null);}
 const blocked=new Set(collapsed),byid=new Map(images.map(n=>[n.id,n]));
 const visible=images.filter(n=>{let p=n;const seen=new Set();while(p){if(blocked.has(p.id)||seen.has(p.id))return false;seen.add(p.id);p=byid.get(parents.get(p.id));}return true;});
 return{images,parents,visible};
}
export function placeNodes(nodes,positions){return nodes.map(n=>{const pos=positions.get(n.id);let next=pos?{...n,pose:{...n.pose,...pos}}:{...n};if(!pos&&n.kind==='reference'){const id=contextOwner(nodes,n.pose),old=nodes.find(v=>v.id===id),q=positions.get(id);if(old&&q)next={...n,pose:{...n.pose,x:n.pose.x+q.x-old.pose.x,y:n.pose.y+q.y-old.pose.y}};}next.annotations=(n.annotations||[]).map(a=>{const world=transformAnnotation(a,{x:n.pose.x,y:n.pose.y}),id=contextOwner(nodes,annotationBounds(world)),old=nodes.find(v=>v.id===id),q=positions.get(id),dx=q&&old?q.x-old.pose.x:0,dy=q&&old?q.y-old.pose.y:0;return transformAnnotation(a,{x:dx-(next.pose.x-n.pose.x),y:dy-(next.pose.y-n.pose.y)});});return next;});}
export function arrangeNodes(nodes,collapsed=[]){
 const {visible,parents}=canvasGraph(nodes,collapsed);if(!visible.length)return nodes;
 const live=new Set(visible.map(n=>n.id)),children=new Map(visible.map(n=>[n.id,visible.filter(c=>parents.get(c.id)===n.id)])),roots=visible.filter(n=>!live.has(parents.get(n.id))),depth=new Map(),heights=new Map(),widths=new Map(),columns=new Map([[0,0]]),positions=new Map();
 function measure(n,d){depth.set(n.id,d);const cs=children.get(n.id),height=Math.max(n.frame.height,cs.reduce((s,c)=>s+measure(c,d+1),0)+90*Math.max(0,cs.length-1));heights.set(n.id,height);return height;}
 roots.forEach(n=>measure(n,0));visible.forEach(n=>widths.set(depth.get(n.id),Math.max(widths.get(depth.get(n.id))||0,n.frame.width)));
 for(let d=1;d<=Math.max(...widths.keys());d++)columns.set(d,columns.get(d-1)+widths.get(d-1)+140);
 function place(n,y){const cs=children.get(n.id);positions.set(n.id,{x:columns.get(depth.get(n.id))-n.frame.x,y:y+(heights.get(n.id)-n.frame.height)/2-n.frame.y});const total=cs.reduce((s,c)=>s+heights.get(c.id),0)+90*Math.max(0,cs.length-1);let cy=y+(heights.get(n.id)-total)/2;for(const c of cs){place(c,cy);cy+=heights.get(c.id)+90;}}
 let y=0;for(const n of roots){place(n,y);y+=heights.get(n.id)+90;}return placeNodes(nodes,positions);
}
export function avoidNodes(nodes,anchor,collapsed=[]){
 const {visible}=canvasGraph(nodes,collapsed),fixed=visible.find(n=>n.id===anchor);if(!fixed)return nodes;
 const placed=[frameBox(fixed)],positions=new Map([[anchor,{x:fixed.pose.x,y:fixed.pose.y}]]);
 const others=visible.filter(n=>n.id!==anchor).sort((a,b)=>frameBox(a).y-frameBox(b).y||frameBox(a).x-frameBox(b).x||a.id.localeCompare(b.id));
 for(const n of others){const b=frameBox(n);for(let i=0;i<=placed.length;i++){const hits=placed.filter(r=>overlaps(b,r));if(!hits.length)break;b.y=Math.max(...hits.map(r=>r.y+r.height+90));}positions.set(n.id,{x:b.x-n.frame.x,y:b.y-n.frame.y});placed.push(b);}return placeNodes(nodes,positions);
}
export function branchPorts(nodes,collapsed=[]){
 const {images,parents,visible}=canvasGraph(nodes,collapsed),live=new Set(visible.map(n=>n.id)),closed=new Set(collapsed),ports=[];
 for(const parent of visible){const children=images.filter(n=>parents.get(n.id)===parent.id),a=frameBox(parent);children.forEach((child,i)=>{const b=frameBox(child);ports.push({parent:parent.id,child:child.id,x:a.x+a.width,y:a.y+a.height*(i+1)/(children.length+1),endX:b.x,endY:b.y+b.height/2,collapsed:closed.has(child.id),connected:live.has(child.id)});});}return ports;
}

// Bake annotation transforms into the schema consumed by the raster worker (no extra transform fields).
export function transformAnnotation(a,{x=0,y=0,scaleX=1,scaleY=1}){return{...a,x:(a.x||0)*scaleX+x,y:(a.y||0)*scaleY+y,points:(a.points||[]).map(([px,py,pressure])=>[px*scaleX+x,py*scaleY+y,pressure]),size:Math.min(100,Math.max(1,a.size*Math.sqrt(Math.abs(scaleX*scaleY))))};}

export const blankResult=n=>!!n?.pending&&!n.draftBaseApplied;
export function annotationBounds(a){const p=a.points||[],s=a.size||5;if(p.length)return{x:Math.min(...p.map(q=>q[0]))-s/2,y:Math.min(...p.map(q=>q[1]))-s/2,width:Math.max(...p.map(q=>q[0]))-Math.min(...p.map(q=>q[0]))+s,height:Math.max(...p.map(q=>q[1]))-Math.min(...p.map(q=>q[1]))+s};const lines=(a.text||' ').split('\n'),pad=a.kind==='label'?14:0;return{x:a.x||0,y:a.y||0,width:Math.max(...lines.map(l=>[...l].reduce((v,c)=>v+(c.charCodeAt(0)>255?1:.65),0)))*s+pad+1,height:lines.length*s+pad};}
export const intersectionArea=(a,b)=>Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));
export function contextOwner(nodes,box){return nodes.filter(n=>n.kind==='image'&&!n.deleted&&!n.hidden&&!n.archived).map(n=>({id:n.id,area:intersectionArea(frameBox(n),box)})).filter(n=>n.area>0).sort((a,b)=>b.area-a.area||b.id.localeCompare(a.id))[0]?.id;}
export function followMarks(before,after,marks=[]){return marks.map(a=>{const target=contextOwner(before,annotationBounds(a)),p=before.find(n=>n.id===target),q=after.find(n=>n.id===target);return p&&q?transformAnnotation(a,{x:q.pose.x-p.pose.x,y:q.pose.y-p.pose.y}):a;});}
export function scopedAnnotations(board,n){const f=frameBox(n),result=[];for(const a of board.marks||[])if(a.enabled!==false&&intersectionArea(annotationBounds(a),f)>0)result.push(transformAnnotation(a,{x:-n.pose.x,y:-n.pose.y}));for(const source of board.nodes)if(!source.deleted&&!source.hidden&&!source.archived)for(const a of source.annotations){const world=transformAnnotation(a,{x:source.pose.x,y:source.pose.y});if(a.enabled!==false&&intersectionArea(annotationBounds(world),f)>0)result.push(transformAnnotation(world,{x:-n.pose.x,y:-n.pose.y}));}return result;}
