import React from 'react';

export function guideKind(row,rows){
 const byId=new Map(rows.map(r=>[r.id,r])),seen=new Set();let current=row;
 while(current&&!seen.has(current.id)){
  seen.add(current.id);const name=current.name.toLowerCase();
  for(const [kind,words] of [['depth',['depth','深度']],['form',['arctic','极地']],['color',['material color','material colour','材质颜色','材质色','color channel','colour channel']],['shadow',['shadow','阴影']]])if(words.some(w=>name.includes(w)))return kind;
  current=byId.get(current.parent);
 }
 return null;
}
export function layerRole(row,rows,params){const kind=guideKind(row,rows);return params.roles?.[row.id]||(kind?(kind==='shadow'?'reference':'structure'):row.role||'generate');}
export function layerEnabled(row,rows,params){const byId=new Map(rows.map(r=>[r.id,r])),seen=new Set();let current=row;while(current&&!seen.has(current.id)){seen.add(current.id);if(!(params.layerParticipation?.[current.id]??current.effectiveVisible??current.visible??true))return false;current=byId.get(current.parent);}return true;}

export default function PsdLayers({layers,params,patch,t}){
 const children=id=>layers.filter(r=>{let p=r.parent;const seen=new Set();while(p&&!seen.has(p)){if(p===id)return true;seen.add(p);p=layers.find(x=>x.id===p)?.parent;}return false;});
 function toggle(row,value){const participation={...params.layerParticipation,[row.id]:value};if(row.group)for(const child of children(row.id))participation[child.id]=value;if(value){let p=row.parent;while(p){participation[p]=true;p=layers.find(x=>x.id===p)?.parent;}}patch({layerParticipation:participation});}
 const leaves=layers.filter(l=>!l.group),count=leaves.filter(l=>layerEnabled(l,layers,params)&&layerRole(l,layers,params)!=='exclude').length;
 return <details className="psdParticipation"><summary>PSD · {t('psdParticipation')} <small>{count} / {leaves.length}</small></summary>
  <p className="hint">{t('psdParticipationHint')}</p>
  <div className="psdLayerActions"><button onClick={()=>patch({layerParticipation:Object.fromEntries(layers.map(l=>[l.id,true]))})}>{t('psdAll')}</button><button onClick={()=>patch({layerParticipation:Object.fromEntries(layers.map(l=>[l.id,false]))})}>{t('psdNone')}</button><button onClick={()=>patch({layerParticipation:{},roles:{}})}>{t('psdDefaults')}</button></div>
  <div className="psdLayerList">{layers.map(l=>{let depth=0,p=l.parent;const seen=new Set();while(p&&!seen.has(p)){seen.add(p);depth++;p=layers.find(x=>x.id===p)?.parent;}const active=layerEnabled(l,layers,params),kind=guideKind(l,layers);return <div className={'psdLayer'+(l.group?' isGroup':'')+(!active?' inactive':'')} key={l.id} style={{paddingInlineStart:Math.min(40,depth*10)}}>
   <label className="psdLayerToggle"><input type="checkbox" checked={active} onChange={e=>toggle(l,e.target.checked)} aria-label={t('psdUse')+': '+l.name}/><span><strong title={l.name}>{l.name}</strong><small>{t(l.effectiveVisible?'psdVisible':'psdHidden')}{kind?' · '+t('guide'+kind):''}</small></span></label>
   {!l.group&&<select aria-label={t('psdUsage')+': '+l.name} disabled={!active} value={layerRole(l,layers,params)} onChange={e=>patch({roles:{...params.roles,[l.id]:e.target.value}})}>{['generate','structure','reference','preserve','exclude'].map(k=><option key={k} value={k}>{t('role'+k[0].toUpperCase()+k.slice(1))}</option>)}</select>}
  </div>;})}</div>
 </details>;
}
