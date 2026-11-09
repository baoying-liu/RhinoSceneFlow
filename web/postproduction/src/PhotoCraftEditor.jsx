import React,{useEffect,useRef,useState} from 'react';

export default function PhotoCraftEditor({board,node,request,language,onApply,onClose}){
 const zh=language!=='en'&&(language==='zh-CN'||navigator.language.startsWith('zh'));
 const tr=(zhText,en)=>zh?zhText:en;
 const frame=useRef(),session=useRef(),opened=useRef(false),applying=useRef(false),timer=useRef(),channel=useRef(crypto.randomUUID());
 const [status,setStatus]=useState('loading'),[error,setError]=useState('');
 useEffect(()=>{
  let live=true;
  const discard=s=>fetch(`/api/boards/${board.id}/edit-reference/${s.session}`,{method:'DELETE',headers:{Authorization:'Bearer '+sessionStorage.getItem('sceneflow-post-token')}}).catch(()=>{});
  request(`/boards/${board.id}/nodes/${node.id}/edit-reference/session`,{method:'POST',body:{revision:board.revision}}).then(s=>{if(live)session.current=s;else discard(s);}).catch(e=>{if(live)setError(e.message);});
  async function receive(e){
   if(!live||e.source!==frame.current?.contentWindow||e.origin!==location.origin||e.data?.sceneflowEditor!==channel.current)return;
   const d=e.data;
   if(d.type==='ready'&&session.current&&!opened.current){
    opened.current=true;
    try{
     const r=await fetch(`/api/boards/${board.id}/edit-reference/${session.current.session}/input`,{headers:{Authorization:'Bearer '+sessionStorage.getItem('sceneflow-post-token')}});
     if(!r.ok)throw new Error(await r.text());const bytes=await r.arrayBuffer();if(!live)return;
     frame.current.contentWindow.postMessage({sceneflowEditor:channel.current,type:'open',bytes,name:session.current.name},location.origin,[bytes]);setStatus('editing');
    }catch(e){if(live)setError(e.message);}
   }
   if(d.type==='saved'&&applying.current){
    applying.current=false;clearTimeout(timer.current);setStatus('applying');
    try{
     const response=await fetch(`/api/boards/${board.id}/edit-reference/${session.current.session}/apply`,{method:'POST',headers:{Authorization:'Bearer '+sessionStorage.getItem('sceneflow-post-token'),'Content-Type':'image/vnd.adobe.photoshop'},body:d.bytes});
     const b=await response.json();if(!response.ok)throw new Error(b.detail||response.statusText);if(live)onApply(b);
    }catch(e){if(live){setError(e.message);setStatus('editing');}}
   }
   if(d.type==='error'){setError(d.message);setStatus('editing');applying.current=false;clearTimeout(timer.current);}
  }
  window.addEventListener('message',receive);
  const handshake=setInterval(()=>frame.current?.contentWindow.postMessage({sceneflowEditor:channel.current,type:'init'},location.origin),300);
  return()=>{live=false;clearInterval(handshake);clearTimeout(timer.current);window.removeEventListener('message',receive);if(session.current)discard(session.current);};
 },[]);
 function save(){setError('');setStatus('saving');applying.current=true;frame.current.contentWindow.postMessage({sceneflowEditor:channel.current,type:'save'},location.origin);timer.current=setTimeout(()=>{applying.current=false;setStatus('editing');setError(tr('尚未收到 PSD。若编辑器显示保存选项，请确认后再点击应用。','No PSD received. Confirm any Save options in the editor, then Apply again.'));},45000);}
 return <div className="photoCraftOverlay" role="dialog" aria-label="PhotoCraft"><header><div><strong>PhotoCraft · {node.name}</strong><small>{tr('单份编辑参考层 · 原图保留 · 不加入历史备份','One editable reference · original preserved · no image backups')}</small></div><span role="status">{status==='loading'?tr('正在启动本机编辑器…','Starting local editor…'):status==='saving'?tr('正在保存；如出现 PSD 选项请确认','Saving; confirm PSD options if shown'):status==='applying'?tr('正在应用参考层…','Applying reference…'):tr('编辑完成后点击应用并返回','Edit, then Apply and return')}</span><button disabled={status==='applying'} onClick={onClose}>{tr('取消编辑','Cancel')}</button><button className="primary" disabled={status!=='editing'} onClick={save}>{tr('应用并返回','Apply and return')}</button></header>{error&&<div className="error" role="alert">{error}</div>}<iframe ref={frame} title="PhotoCraft" src="/editor/photocraft/index.html?webgl" allow="clipboard-read; clipboard-write"/></div>;
}
