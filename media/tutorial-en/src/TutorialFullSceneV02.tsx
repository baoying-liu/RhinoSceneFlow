import React from 'react';
import {AbsoluteFill,Img,OffthreadVideo,Sequence,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
type Point={at:number;x:number;y:number;label?:string;space?:string;click?:boolean};
type Shot={at:number;kind:string;left?:string;right?:string;image?:string;scroll?:number;focus?:number;full?:boolean;pan?:number[][];divider?:number[][];nav?:{previous:string;row:number}|null;note?:string;video?:string|null;videoAt?:number;videoEnd?:number;step?:number};
type Props={id:string;chapter:string;title:string;shots:Shot[];cursor:Point[]};
const old=(n:string)=>staticFile('case/tutorial-full-v01/'+n);
const fresh=(n:string)=>staticFile('case/tutorial-full-v02/'+n);
const newer=new Set(['web-overview.png','web-source.png','web-child-blank.png','web-child-description.png','web-whole-params.png','web-whole-canvas.png','web-local-blank.png','web-local-applied.png','web-arrow-tool.png','web-arrow-drawn.png','web-text-drawn.png','web-reference-added.png','web-hd-settings.png','web-tiles-review.png','web-whole-end.png','web-local-end.png']);
const webAsset=(n:string)=>newer.has(n)?fresh(n):old(n);
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const L={x:36,y:100,w:690,h:850},R={x:768,y:100,w:1116,h:850};
const smooth=(v:number)=>v*v*(3-2*v);
const panAt=(s:Shot,t:number)=>{let y=s.scroll??s.focus??0;for(const p of s.pan??[]){if(t<p[0])break;const q=smooth(Math.max(0,Math.min(1,(t-p[0])/.65)));y=y+(p[1]-y)*q;}return y;};
const Cursor:React.FC<{x:number;y:number;label?:string;click?:boolean;age:number}>=({x,y,label,click,age})=><div style={{position:'absolute',left:x-3,top:y-3,pointerEvents:'none',zIndex:20}}>
 {click&&age>=0&&age<.45?<svg width={74} height={74} style={{position:'absolute',left:-33,top:-33}}><circle cx={37} cy={37} r={12+age*40} fill="none" stroke="#efc45b" strokeWidth={3} opacity={1-age/.45}/></svg>:null}
 <svg width={37} height={49} style={{filter:'drop-shadow(0 2px 2px #000c)'}}><path d="M3 3 L3 35 L11 28 L19 45 L25 42 L17 26 L31 25 Z" fill="white" stroke="#112a21" strokeWidth={2.2}/></svg>
 {label?<div style={{position:'absolute',top:y>825?-34:42,left:x>1510?-240:22,maxWidth:365,background:'#112a21f0',color:'#f4f3e8',border:'1px solid #9bbda8',borderRadius:5,padding:'6px 11px',font:'19px Arial',whiteSpace:'nowrap'}}>{label}</div>:null}
</div>;
const NativePanel:React.FC<{s:Shot;t:number}>=({s,t})=>{
 const nav=s.nav&&t<3.5;const src=nav?s.nav!.previous:s.left!;const y=nav?0:panAt(s,t);
 return <div style={{position:'absolute',...{left:L.x,top:L.y,width:L.w,height:L.h},background:'#19382b',overflow:'hidden',borderRadius:8}}>
  <Img src={fresh(src+'-header.jpg')} style={{position:'absolute',left:0,top:15,width:690,height:68}}/>
  <div style={{position:'absolute',left:50,top:113,width:630,height:737,overflow:'hidden'}}><Img src={fresh(src+'-body.jpg')} style={{position:'absolute',left:0,top:-y,width:630,height:1815}}/></div>
  {nav&&t>=.8?<Img src={old('tool-menu.png')} style={{position:'absolute',left:44,top:69,width:507,height:312}}/>:null}
 </div>;
};
const Web:React.FC<{s:Shot;t:number;id:string}>=({s,t,id})=>{
 const focus=panAt(s,t);const url=webAsset(s.image!);const z=R.w/1342;
 if(s.full)return <Img src={url} style={{position:'absolute',left:36,top:100,width:1848,height:850,objectFit:'contain',background:'#10221a'}}/>;
 return <>
 <div style={{position:'absolute',left:L.x,top:L.y,width:L.w,height:L.h,overflow:'hidden',borderRadius:8,background:'#192a20'}}>
  <svg width={690} height={850} viewBox={`1594 ${focus} 326 600`} preserveAspectRatio="xMidYMid meet"><defs><clipPath id={'i'+id}><rect x={1594} y={focus} width={326} height={600}/></clipPath></defs><image href={url} width={1920} height={1080} clipPath={`url(#i${id})`}/></svg>
 </div>
 <div style={{position:'absolute',left:R.x,top:R.y,width:R.w,height:R.h,overflow:'hidden',borderRadius:8,background:'#101b14'}}>
  <svg width={R.w} height={R.h} viewBox="252 72 1342 975" preserveAspectRatio="xMidYMid meet"><defs><clipPath id={'m'+id}><rect x={252} y={72} width={1342} height={975}/></clipPath></defs><image href={url} width={1920} height={1080} clipPath={`url(#m${id})`}/></svg>
  {s.video&&t>=(s.videoAt??0)&&t<(s.videoAt??0)+(s.video==='compare-whole.mp4'?6.06:4.06)?<Sequence from={Math.round((s.videoAt??0)*30)} layout="none"><div style={{position:'absolute',left:0,top:(850-975*z)/2,width:R.w,height:975*z,overflow:'hidden'}}><OffthreadVideo muted src={old(s.video)} style={{position:'absolute',left:-252*z,top:-72*z,width:1920*z,height:1080*z}}/></div></Sequence>:null}
 </div></>;
};
const Visual:React.FC<{s:Shot;t:number;id:string}>=({s,t,id})=>{
 const {fps}=useVideoConfig();
 if(s.kind==='web')return <Web s={s} t={t} id={id}/>;
 if(['native','plants','photo'].includes(s.kind))return <><NativePanel s={s} t={t}/><div style={{position:'absolute',left:R.x,top:R.y,width:R.w,height:R.h,background:s.kind==='photo'?'#242424':'white',overflow:'hidden',borderRadius:8}}>
 {s.kind==='plants'?<div style={{display:'flex',height:850,alignItems:'center',justifyContent:'center',gap:15}}>{['plant-elevation.png','plant-plan.png'].map((n,i)=><div key={n} style={{width:470,textAlign:'center',color:'#10251d',fontSize:25}}><Img src={old(n)} style={{width:450,height:650,objectFit:'contain'}}/>{i?'Separate plan canopy':'Transparent elevation'}</div>)}</div>:<Img src={old(s.right!)} style={{width:'100%',height:'100%',objectFit:'contain'}}/>}
 {s.video&&t>=(s.videoAt??0)&&t<(s.videoEnd??6)?<Sequence from={Math.round((s.videoAt??0)*fps)} layout="none"><OffthreadVideo muted src={old(s.video)} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/></Sequence>:null}
 </div></>;
 if(s.kind==='establish'){const q=interpolate(t,[3.7,6.1],[0,1],clamp);return <><Img src={old(s.image!)} style={{position:'absolute',left:0,top:15,width:1920,height:1049,opacity:1-q}}/>{[{x:95,y:137,w:321,h:905,end:L,src:'white-model-top.jpg'},{x:418,y:137,w:1276,h:889,end:R,src:'white-model-view.jpg'}].map((b,i)=><div key={i} style={{position:'absolute',left:b.x+(b.end.x-b.x)*q,top:b.y+(b.end.y-b.y)*q,width:b.w+(b.end.w-b.w)*q,height:b.h+(b.end.h-b.h)*q,outline:'2px solid #d7b477',overflow:'hidden',opacity:t>2?1:0,background:'#19382b'}}><Img src={old(b.src)} style={{width:'100%',height:'100%',objectFit:'contain',opacity:q}}/></div>)}</>;}
 if(s.kind==='github')return <><Img src={old(s.image!)} style={{position:'absolute',left:36,top:100,width:1050,height:850,objectFit:'contain',background:'white'}}/><div style={{position:'absolute',left:1126,top:180,fontSize:32,lineHeight:1.6}}>Releases → Assets<br/>Download the Windows EXE<div style={{fontSize:22,marginTop:20}}>github.com/baoying-liu/RhinoSceneFlow/releases</div></div><svg style={{position:'absolute',left:1126,top:460,width:730,height:410,background:'white'}} viewBox="45 0 800 380"><image href={old('github-assets-actual.png')} width={1050} height={440}/></svg></>;
 if(s.kind==='setup')return <div style={{position:'absolute',left:165,top:140,width:1590,height:720,border:'1px solid #668779',borderRadius:14,background:'#1b3026'}}><div style={{padding:30,background:'#243e31',fontSize:28}}>SceneFlow Setup <span style={{float:'right',color:'#d7b477'}}>Illustrative setup</span></div><div style={{padding:70,fontSize:48}}>{['Save your work and close Rhino','Check required components','Reopen Rhino and SceneFlow'][s.step??0]}</div><div style={{padding:'0 70px',fontSize:29,lineHeight:1.7}}>Follow the actual installer prompts.<br/>Check the detected Rhino installation and required components.<br/>The remaining chapters use real software captures.</div></div>;
 return <><Img src={old(s.image!)} style={{position:'absolute',left:660,top:150,width:1190,height:720,objectFit:'contain',background:'white'}}/><div style={{position:'absolute',left:65,top:215,width:540,color:'#ecf1e7',fontSize:69,lineHeight:1.05,fontWeight:650}}>From Rhino<br/>to a finished<br/>AI image.</div><div style={{position:'absolute',left:68,top:530,fontSize:28,lineHeight:1.7,color:'#b6cbbc'}}>Materials → Plants<br/>Layered PSD → AI<br/>Traceable revisions → 4K</div></>;
};
function project(p:Point,s:Shot,t:number):[number,number]{
 if(p.space==='body')return [L.x+50+p.x,L.y+113+p.y-panAt(s,t)];
 if(p.space==='webLeft'){const z=850/600;return [L.x+(690-326*z)/2+(p.x-1594)*z,L.y+(p.y-panAt(s,t))*z];}
 if(p.space==='webMain'){const z=R.w/1342;return [R.x+(p.x-252)*z,R.y+(850-975*z)/2+(p.y-72)*z];}
 if(s.kind==='web'&&s.full){const z=850/1080;return [36+(1848-1920*z)/2+p.x*z,100+p.y*z];}
 return [p.x,p.y];
}
export const TutorialSceneV02:React.FC<Props>=({id,chapter,title,shots,cursor})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),t=frame/fps;
 const s=shots.reduce((a,v)=>v.at<=t?v:a,shots[0]);const local=t-s.at;
 const p=cursor.reduce((a,v)=>v.at<=t?v:a,cursor[0]);const i=cursor.indexOf(p);const before=cursor[Math.max(0,i-1)];
 const [tx,ty]=project(p,s,local),[px,py]=project(before,s,local);const travel=i?smooth(Math.min(1,Math.max(0,(t-p.at)/.5))):1;
 let x=px+(tx-px)*travel,y=py+(ty-py)*travel,label=p.label;
 if(travel<1)label=before.label;
 if(s.divider&&local>=(s.videoAt??0)&&local<((s.videoAt??0)+s.divider.length/15)){
  const v=s.divider[Math.min(s.divider.length-1,Math.floor((local-(s.videoAt??0))*15))];
  [x,y]=project({at:t,x:v[1],y:v[2],space:'webMain'},s,local);label='Drag to compare · result / parent';
 }
 if(s.nav&&local<3.5){if(local<.8){x=520;y=150;label='Open tool dropdown';}else{const q=smooth(Math.min(1,(local-.8)/.6));x=520+(275-520)*q;y=150+(100+69+17+s.nav.row*34.7-150)*q;label='Select tool';}}
 return <AbsoluteFill style={{background:'#10251d',fontFamily:'Arial,sans-serif',color:'#ecf1e7'}}><Visual s={s} t={local} id={id}/>
 <Cursor x={x} y={y} label={label} click={Boolean(p.click)&&travel===1} age={t-p.at-.5}/>
 <div style={{position:'absolute',left:36,top:28,color:'#a8c2ae',fontSize:19,letterSpacing:2}}>SCENEFLOW / {chapter.replace('T','').padStart(2,'0')}</div><div style={{position:'absolute',left:290,top:24,fontSize:31,fontWeight:600}}>{title}</div>
 <div style={{position:'absolute',right:36,top:39,color:'#89a392',fontSize:15}}>Real UI captures · guided cursor · edited demonstration</div>
 {s.note?<div style={{position:'absolute',left:38,top:957,fontSize:20,color:'#d7b477'}}>{s.note}</div>:null}
 <div style={{position:'absolute',left:36,top:983,color:'#71917d',fontSize:14}}>SceneFlow · preview v0.23.3 · tutorial visual revision 02</div>
 </AbsoluteFill>;
};
