/* SceneFlow adapter for the unmodified, pinned PhotoCraft 0.21.0 Web release.
 * The supported browser file-drop and PSD Save/download paths are the boundary.
 * No Wasm memory access, upstream UI coordinates or external service calls. */
(() => {
  const host=window.parent, origin=location.origin;
  let channel=null, started=false;
  const send=(type,extra={},transfer=[])=>channel&&host.postMessage({sceneflowEditor:channel,type,...extra},origin,transfer);
  // A PSD compatibility composite is required when applying. Never guess from a thumbnail.
  try {
    const p=JSON.parse(localStorage.getItem('photocraft.preferences')||'{}');
    p.fileHandling={...p.fileHandling,maximizePsdCompatibility:'always'};
    localStorage.setItem('photocraft.preferences',JSON.stringify(p));
  } catch (_) { /* The host still validates every returned full-size PSD. */ }
  const click=HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click=function(){
    if(channel&&this.href.startsWith('blob:')&&this.download.toLowerCase().endsWith('.psd')){
      fetch(this.href).then(r=>r.arrayBuffer()).then(bytes=>send('saved',{bytes},[bytes])).catch(e=>send('error',{message:String(e)}));
      return;
    }
    return click.call(this);
  };
  window.addEventListener('message',e=>{
    if(e.source!==host||e.origin!==origin)return;
    const d=e.data;
    if(d?.type==='init'&&typeof d.sceneflowEditor==='string'&&!channel){channel=d.sceneflowEditor;send('connected');return;}
    if(!channel||d?.sceneflowEditor!==channel)return;
    if(d.type==='open'&&!started){
      started=true;
      const dt=new DataTransfer();dt.items.add(new File([d.bytes],d.name||'reference.psd',{type:'image/vnd.adobe.photoshop'}));
      const canvas=document.getElementById('photocraft_canvas');canvas.focus();
      canvas.dispatchEvent(new DragEvent('drop',{dataTransfer:dt,bubbles:true,cancelable:true,clientX:0,clientY:0}));
      send('opened');
    }
    if(d.type==='save'){
      const canvas=document.getElementById('photocraft_canvas');canvas.focus();
      for(const type of ['keydown','keyup'])canvas.dispatchEvent(new KeyboardEvent(type,{key:'s',code:'KeyS',ctrlKey:true,bubbles:true,cancelable:true}));
    }
  });
  const check=()=>{
    if(!document.getElementById('photocraft_loading')&&document.getElementById('photocraft_canvas'))send('ready');
    const stopped=document.getElementById('photocraft_stopped');
    if(stopped&&!stopped.hidden)send('error',{message:stopped.innerText});
  };
  setInterval(check,500);
  // The parent owns Apply/Cancel; discarding this iframe is an explicit Cancel action.
  window.addEventListener('beforeunload',e=>e.stopImmediatePropagation(),true);
})();
