import React from 'react';
export default function GenerationInput({input,node,t,onLocate,onInspect,onUseInput,board,Thumbnail}){
 const changed=!node.original&&input&&(node.input?.id!==input.id||node.input?.versionId!==input.versionId);
 return <section className="generationInput" aria-label={t('generationInput')}>
  <span>{t(node.original?'templateInput':'generationInput')}</span>
  {input?<><div className="inputSourceRow"><button className="inputSourceThumb" aria-label={input.name} onClick={()=>onLocate(input.id)}><Thumbnail board={board} node={{...input,editReference:null,pending:false}}/></button><div><button className="inputSourceLink" onClick={()=>onLocate(input.id)}>{input.name}</button><small>{t('inputVersion')} · {input.versionId?.slice(0,8)}</small></div></div></>:<p role="alert">{t('missingInput')}</p>}
  {changed&&<p className="inputVersionChanged">{t('nextInputChanged')}</p>}
  {!!input?.skipped?.length&&<small>{t('skippedSteps')} · {input.skipped.length}</small>}
  <button className="inputInspect" onClick={onInspect}>{t(node.original?'input':'checkGenerationInput')}</button>
  {node.pending&&!node.draftBaseApplied&&<button className="inputInspect" title={t('applyParentHint')} onClick={onUseInput}>{t('traceInput')}</button>}
 </section>;
}
