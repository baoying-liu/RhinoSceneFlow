import React from 'react';
import {AbsoluteFill,Easing,Img,Interactive,OffthreadVideo,Sequence,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';

type Shot={at:number;kind:string;left?:string;right?:string;image?:string;focus?:number;menu?:boolean;note?:string;video?:string|null;videoAt?:number;videoEnd?:number;step?:number};
type Props={id:string;chapter:string;title:string;shots:Shot[]};
const asset=(s:string)=>staticFile('case/tutorial-full-v01/'+s);
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const bg='#10251d',ink='#ecf1e7',accent='#d7b477';
const left={x:36,y:100,w:690,h:850},right={x:768,y:100,w:1116,h:850};

const Cursor:React.FC<{x:number;y:number;label?:string}>=({x,y,label})=><div style={{position:'absolute',left:x,top:y,pointerEvents:'none'}}>
 <svg width={42} height={54} style={{filter:'drop-shadow(0 2px 3px #0009)'}}><path d="M3 3 L3 38 L12 30 L20 49 L27 46 L19 28 L34 27 Z" fill="white" stroke="#10251d" strokeWidth={2.5}/></svg>
 {label?<div style={{position:'absolute',top:38,left:26,background:'#10251df0',color:ink,border:'1px solid #91b4a2',padding:'6px 12px',fontSize:20,whiteSpace:'nowrap'}}>{label}</div>:null}
</div>;

const NativePanel:React.FC<{src:string;menu?:boolean;t:number}>=({src,menu,t})=><div style={{position:'absolute',left:left.x,top:left.y,width:left.w,height:left.h,background:'#19382b',overflow:'hidden',borderRadius:8}}>
 <Img src={asset(src)} style={{width:690,height:850}}/>
 {menu&&t>1&&t<3.8?<><Img src={asset('tool-menu.png')} style={{position:'absolute',left:44,top:69,width:507,height:312}}/><Cursor x={485} y={52}/></>:null}
</div>;

const Visual:React.FC<{shot:Shot;t:number;id:string}>=({shot,t,id})=>{
 const {fps}=useVideoConfig();
 if(shot.kind==='intro'||shot.kind==='outro')return <>
  <Img src={asset(shot.image!)} style={{position:'absolute',left:660,top:150,width:1190,height:720,objectFit:'contain',background:'white',borderRadius:10}}/>
  <Interactive.Div name="Workflow title" style={{position:'absolute',left:65,top:215,width:540,color:ink,fontSize:69,lineHeight:1.05,fontWeight:650}}>From Rhino<br/>to a finished<br/>AI image.</Interactive.Div>
  <div style={{position:'absolute',left:68,top:510,color:'#b6cbbc',fontSize:28,lineHeight:1.65}}>Materials → Plants<br/>Layered PSD → AI<br/>Traceable revisions → 4K</div>
  <div style={{position:'absolute',left:68,top:800,color:accent,fontSize:23}}>{shot.kind==='outro'?'Keep the model. Keep the source. Keep exploring.':'One practical case · a complete workflow'}</div>
 </>;
 if(shot.kind==='setup')return <>
  <div style={{position:'absolute',left:165,top:140,width:1590,height:720,border:'1px solid #668779',borderRadius:14,background:'#1b3026',overflow:'hidden'}}>
   <div style={{padding:'26px 36px',background:'#243e31',fontSize:27}}>SceneFlow Setup <span style={{float:'right',color:accent}}>Illustrative setup</span></div>
   <div style={{display:'flex',height:625}}>
    <div style={{width:380,padding:45,borderRight:'1px solid #496052',fontSize:27,lineHeight:2.4,color:'#a9c1b0'}}>1. Close Rhino<br/>2. Check components<br/>3. Install SceneFlow<br/>4. Reopen Rhino</div>
    <div style={{padding:55,flex:1}}>
     <div style={{fontSize:49,marginBottom:28}}>{['Before installation','Check required components','Ready to open Rhino'][shot.step??0]}</div>
     <div style={{fontSize:29,lineHeight:1.65,maxWidth:850,color:'#d2ddd0'}}>{['Save open files and close Rhino. Download the Windows EXE from the release assets.','Follow the actual setup prompts. Review the detected Rhino installation and required runtime / MCP components.','Open SceneFlow in Rhino. Use Settings to check the environment and AI sign-in before generating assets.'][shot.step??0]}</div>
     <div style={{marginTop:65,color:accent,fontSize:24}}>Installation flow illustrated here; actual software follows.</div>
    </div>
   </div>
  </div>
 </>;
 if(shot.kind==='github')return <>
  <Img src={asset(shot.image!)} style={{position:'absolute',left:36,top:100,width:1050,height:850,objectFit:'contain',background:'#fff',borderRadius:8}}/>
  <div style={{position:'absolute',left:1126,top:180,width:730,fontSize:31,lineHeight:1.7}}>Releases → Assets<br/><span style={{color:accent}}>Download the Windows EXE</span><div style={{fontSize:23,lineHeight:1.5,marginTop:20,color:'#b6cbbc'}}>github.com/baoying-liu/RhinoSceneFlow/releases</div><div style={{fontSize:24,marginTop:20}}>Preview v0.23.3 · actual release assets</div></div>
  <svg style={{position:'absolute',left:1126,top:460,width:730,height:410,background:'white',borderRadius:8}} viewBox="45 0 800 380"><defs><clipPath id="release-assets-clip"><rect x={45} y={0} width={800} height={380}/></clipPath></defs><image href={asset('github-assets-actual.png')} width={1050} height={440} clipPath="url(#release-assets-clip)"/></svg>
  <Cursor x={1280} y={565} label="Windows EXE installer"/>
 </>;
 if(shot.kind==='establish'){
  const q=interpolate(t,[3.7,6.1],[0,1],{...clamp,easing:Easing.bezier(.42,0,.25,1)});
  return <><Img src={asset(shot.image!)} style={{position:'absolute',left:0,top:15,width:1920,height:1049,opacity:1-q}}/>
   {[{x:95,y:137,w:321,h:905,end:left,src:'white-model-top.jpg'},{x:418,y:137,w:1276,h:889,end:right,src:'white-model-view.jpg'}].map((b,i)=><div key={i} style={{position:'absolute',left:b.x+(b.end.x-b.x)*q,top:b.y+(b.end.y-b.y)*q,width:b.w+(b.end.w-b.w)*q,height:b.h+(b.end.h-b.h)*q,overflow:'hidden',outline:`2px solid ${i? '#9dc7b6':accent}`,borderRadius:8,background:i?'white':'#19382b',opacity:t>2?1:0}}><Img src={asset(b.src)} style={{width:'100%',height:'100%',objectFit:'contain',opacity:q}}/></div>)}
   </>;
 }
 if(['native','photo','plants'].includes(shot.kind))return <>
  <NativePanel src={shot.left!} menu={shot.menu} t={t}/>
  <div style={{position:'absolute',left:right.x,top:right.y,width:right.w,height:right.h,borderRadius:8,overflow:'hidden',background:shot.kind==='photo'?'#242424':'white'}}>
   {shot.kind==='plants'?<><div style={{display:'flex',alignItems:'center',justifyContent:'center',height:760,gap:25}}><div style={{width:420,textAlign:'center',color:bg,fontSize:24}}><Img src={asset('plant-elevation.png')} style={{width:390,height:620,objectFit:'contain'}}/>Elevation</div><div style={{width:420,textAlign:'center',color:bg,fontSize:24}}><Img src={asset('plant-plan.png')} style={{width:390,height:620,objectFit:'contain'}}/>Plan · actual canopy asset</div></div></>:<Img src={asset(shot.right!)} style={{width:'100%',height:'100%',objectFit:'contain'}}/>}
   {shot.video&&t>=(shot.videoAt??0)&&t<(shot.videoEnd??6)?<Sequence from={Math.round((shot.videoAt??0)*fps)} layout="none"><OffthreadVideo muted src={asset(shot.video)} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/></Sequence>:null}
  </div>
 </>;
 if(shot.kind==='web'){
  const focus=shot.focus??120;const videoLength=shot.video==='compare-whole.mp4'?6.06:4.06;const z=right.w/1342;
  return <>
   <div style={{position:'absolute',left:left.x,top:left.y,width:left.w,height:left.h,overflow:'hidden',borderRadius:8,background:'#192a20'}}>
    <svg width={690} height={850} viewBox={`1594 ${focus} 326 600`} preserveAspectRatio="xMidYMid meet"><defs><clipPath id={`settings-${id}`}><rect x={1594} y={focus} width={326} height={600}/></clipPath></defs><image href={asset(shot.image!)} width={1920} height={1080} clipPath={`url(#settings-${id})`}/></svg>
   </div>
   <div style={{position:'absolute',left:right.x,top:right.y,width:right.w,height:right.h,overflow:'hidden',borderRadius:8,background:'#101b14'}}>
    <svg width={right.w} height={right.h} viewBox="252 80 1342 967" preserveAspectRatio="xMidYMid meet"><defs><clipPath id={`main-${id}`}><rect x={252} y={80} width={1342} height={967}/></clipPath></defs><image href={asset(shot.image!)} width={1920} height={1080} clipPath={`url(#main-${id})`}/></svg>
    {shot.video&&t<videoLength?<div style={{position:'absolute',left:0,top:(850-967*z)/2,width:right.w,height:967*z,overflow:'hidden'}}><OffthreadVideo muted src={asset(shot.video)} style={{position:'absolute',left:-252*z,top:-80*z,width:1920*z,height:1080*z}}/></div>:null}
   </div>
  </>;
 }
 return null;
};

export const TutorialScene:React.FC<Props>=({id,chapter,title,shots})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig();const t=frame/fps;
 const shot=shots.reduce((a,s)=>s.at<=t?s:a,shots[0]);const local=t-shot.at;
 const fade=['T02-01','T10-01','T11-01'].includes(id)?interpolate(t,[0,.18],[0,1],clamp):1;
 const pointer= t>2&&t<15?({
  'T03-01':[395,563,'Check environment and sign-in'],
  'T03-02':[395,746,'Original Rhino MCP guide'],
  'T05-03':[109,266,'Reuse existing assets'],
  'T05-05':[370,t<8?758:810,t<8?'Application scope':'Apply selected material'],
  'T06-01':[350,705,'Physical texture dimensions'],
  'T10-01':[1560,606,'Plant group visibility'],
  'T10-02':[1560,t<5?702:t<10?734:766,'Inspect the real layers'],
  'T12-02':[t<6?885:912,140,t<6?'Arrow tool':'Text tool'],
 } as Record<string,[number,number,string]>)[id]:undefined;
 return <AbsoluteFill style={{background:bg,fontFamily:'Arial, sans-serif',color:ink}}>
  <div style={{position:'absolute',inset:0,opacity:fade}}><Visual shot={shot} t={local} id={id}/></div>
  {pointer?<Cursor x={pointer[0]} y={pointer[1]} label={pointer[2]}/>:null}
  <div style={{position:'absolute',left:36,top:28,color:'#a8c2ae',fontSize:19,letterSpacing:2}}>SCENEFLOW / {chapter.replace('T','').padStart(2,'0')}</div>
  <Interactive.Div name="Chapter heading" style={{position:'absolute',left:290,top:24,fontSize:31,fontWeight:600,color:ink}}>{title}</Interactive.Div>
  {shot.note?<Interactive.Div name="Context note" style={{position:'absolute',left:38,top:957,fontSize:20,color:accent}}>{shot.note}</Interactive.Div>:null}
  <div style={{position:'absolute',right:36,top:39,color:'#89a392',fontSize:15}}>Real UI captures · edited demonstration</div>
  <div style={{position:'absolute',left:36,top:983,color:'#71917d',fontSize:14}}>SceneFlow · preview v0.23.3</div>
 </AbsoluteFill>;
};
