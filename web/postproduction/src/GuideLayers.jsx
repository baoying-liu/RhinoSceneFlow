import React from 'react';
import {instructionLayers,guideGate,editable} from './model';

function Switches({visible,enabled,onChange,locked,t,scope,id,muted=false}){return <span className={'guideSwitches'+(muted?' gated':'')}>
 <button type="button" className={scope==='appearance'?'referenceEye':undefined} data-field="visible" aria-label={t(scope==='appearance'?(visible?'hideEditingReference':'showEditingReference'):'layerVisibility')} aria-pressed={visible} title={t('referenceVisibilityHint')} onClick={()=>onChange(scope,'visible',!visible,id)}>{visible?'◉':'○'}</button>
 <label title={t('layerParticipation')}><input type="checkbox" aria-label={t('layerParticipation')} checked={enabled} disabled={locked} onChange={e=>onChange(scope,'enabled',e.target.checked,id)}/>AI</label>
 </span>;}
export default function GuideLayers({board,node,t,onChange,onSelect,selection,Thumbnail,onPreview,onUnlock,onRemove}){
 const items=instructionLayers(board,node),g=node.guideControls||{},locked=!editable(node),r=node.editReference,previews=new Map((r?.declaration?.instructions||[]).map(a=>[a.id,a.asset]));
 return <section className="guideLayers" aria-label={t('editAndInstructions')}>
 <header><strong>{t('editAndInstructions')}</strong><Switches scope="all" visible={g.visible!==false} enabled={g.enabled!==false} locked={locked} t={t} onChange={onChange}/></header>
 <p className="hint">{t('layerSwitchHint')}</p>{locked&&<p className="hint">{t('unlockParticipation')}{!node.busy&&!node.archived&&<button onClick={onUnlock}>{t('unlockTask')}</button>}</p>}
 {r&&<div className="guideLayerRow" data-guide-layer="appearance"><button className="guideLayerName editReferencePreview" onClick={onPreview}><Thumbnail board={board.id} node={{...node,preview:r.preview,pending:false,editReference:null}}/><span>{t('appearanceLayer')}</span></button><Switches scope="appearance" visible={r.visible!==false} enabled={r.enabled!==false} muted={!guideGate(node,'visible')||!guideGate(node,'enabled')} locked={locked} t={t} onChange={onChange}/></div>}
 {r&&<div className="guideAppearanceActions">{r.sourceAsset!==node.asset&&<small>{t('editingReferenceStale')}</small>}<button disabled={locked} onClick={onRemove}>{t('delete')}</button></div>}
 <details open><summary>{t('specialInstructions')} · {items.length}</summary><div className="guideGroupControls"><Switches scope="special" visible={g.specialVisible!==false} enabled={g.specialEnabled!==false} locked={locked} t={t} onChange={onChange}/></div>
 {items.map(item=><div key={item.id} className={'guideLayerRow'+(selection?.id===item.id?' selected':'')} data-guide-layer={item.id}>
 <button className="guideLayerName" onClick={()=>onSelect(item)}>{item.resource?<Thumbnail board={board.id} node={item.resource}/>:item.annotation.raster||previews.get(item.id)?<Thumbnail board={board.id} node={{...node,preview:item.annotation.raster||previews.get(item.id),pending:false,editReference:null}}/>:<span className="guideKind">{({pen:'✎',arrow:'↗',text:'T',label:'▣',edit:'▨',protect:'▧'})[item.kind]}</span>}<span>{item.annotation?.text||item.resource?.name||t(item.kind)}</span></button>
 <Switches scope="item" id={item.id} visible={item.visible} enabled={item.enabled} muted={!guideGate(node,'visible')||!guideGate(node,'enabled')||!guideGate(node,'specialVisible')||!guideGate(node,'specialEnabled')} locked={locked} t={t} onChange={onChange}/>
 </div>)}{!items.length&&<p className="hint">{t('noAnnotations')}</p>}
 </details></section>;
}
