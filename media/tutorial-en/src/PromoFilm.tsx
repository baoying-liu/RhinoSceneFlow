import React from 'react';
import {AbsoluteFill, Img, Interactive, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import assets from './filmAssets.json';

const paper='#f4f6ee',ink='#15241b',lime='#d9ff7b',muted='#a2b69f';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const path=(p:string)=>staticFile('case/promo-20261112/'+p);
const ease=(f:number,a:number,b:number)=>{const t=Math.max(0,Math.min(1,(f-a)/(b-a)));return t*t*(3-2*t);};
const phases=['summer','autumn','winter','summer'] as const;

const Photo:React.FC<{src:string;style?:React.CSSProperties;name?:string}>=({src,style,name})=><Img name={name} src={path(src)} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',...style}}/>;
const Tag:React.FC<{children:React.ReactNode;dark?:boolean}>=({children,dark=false})=><div style={{position:'absolute',left:70,bottom:54,color:dark?'#e7f1df':ink,fontSize:22,fontWeight:600,letterSpacing:3,textTransform:'uppercase'}}>{children}</div>;
const Head:React.FC<{children:React.ReactNode;dark?:boolean;size?:number;top?:number}>=({children,dark=false,size=128,top=80})=>{const f=useCurrentFrame();return <Interactive.Div name="Scene headline" style={{position:'absolute',left:66,top,fontSize:size,fontWeight:850,letterSpacing:-size*.065,lineHeight:.91,color:dark?paper:ink,opacity:ease(f,0,12),transform:`translateY(${(1-ease(f,0,20))*30}px)`}}>{children}</Interactive.Div>;};
const Cursor:React.FC<{x:number;y:number;press?:boolean}>=({x,y,press=false})=><div style={{position:'absolute',left:x,top:y,filter:'drop-shadow(0 3px 3px #0005)',zIndex:30,transform:`scale(${press ? 0.88 : 1})`}}><svg width="42" height="52" viewBox="0 0 42 52"><path d="M4 3 L34 30 L21 32 L15 46 Z" fill={paper} stroke={ink} strokeWidth="2"/></svg>{press&&<div style={{position:'absolute',left:-14,top:-14,width:38,height:38,border:'2px solid #c9ef70',borderRadius:'50%'}}/>}</div>;
const Button:React.FC<{children:React.ReactNode;active?:boolean}>=({children,active=true})=><span style={{display:'inline-flex',padding:'13px 22px',borderRadius:11,background:active?lime:'#24392c',color:active?ink:paper,fontSize:25,fontWeight:700}}>{children}</span>;
const Note:React.FC<{children:React.ReactNode}>=({children})=><div style={{position:'absolute',right:45,bottom:25,fontSize:13,letterSpacing:2,color:'#729079',textTransform:'uppercase'}}>{children}</div>;

const Orbit:React.FC<{phase?:string;start?:number;speed?:number;overhead?:boolean}>=({phase='summer',start=0,speed=.2,overhead=false})=>{
 const f=useCurrentFrame();const k=overhead?Math.min(119,start+f*speed):((start+f*speed)%120+120)%120;const n=Math.floor(k);const next=overhead?Math.min(119,n+1):(n+1)%120;
 const url=(i:number)=>staticFile(`case/promo-film-v02/orbit/${phase}/frame-${String(i).padStart(3,'0')}.jpg`);
 return <AbsoluteFill><Img name="Native Rhino camera frame" src={url(n)} style={{width:'100%',height:'100%'}}/>{k-n>.001&&<Img name="Camera frame interpolation" src={url(next)} style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:k-n}}/>}</AbsoluteFill>;
};
const Opening:React.FC=()=>{
 const f=useCurrentFrame();return <AbsoluteFill style={{background:paper}}><Orbit phase="white" speed={.16}/><div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,#f4f6eedc,transparent 65%)'}}/><Head top={145}>Ideas.<br/>Into place<span style={{color:'#779e3e'}}>.</span></Head><div style={{position:'absolute',left:75,bottom:65,fontSize:38,fontWeight:750}}>SceneFlow <span style={{fontWeight:400,fontSize:25,marginLeft:15}}>for Rhino</span></div><div style={{position:'absolute',inset:0,background:paper,opacity:1-ease(f,0,18)}}/></AbsoluteFill>;
};
const Chat:React.FC<{kind:'material'|'plants'}>=({kind})=>{
 const f=useCurrentFrame();const isPlant=kind==='plants';const message=isPlant?'Birch and maple. A natural hillside mix.':'Warm cedar, pale mineral roofs, real scale.';const typing=message.slice(0,Math.floor(Math.max(0,f-25)/2.3));const sent=f>145;const applied=f>245;
 return <AbsoluteFill style={{background:paper}}>
   <Orbit phase={applied?(isPlant?'summer':'cedar'):(isPlant?'cedar':'white')} start={isPlant?12:0} speed={.07}/>
   <Head size={116}>{isPlant?'Grow your scene.':'Just ask.'}</Head>
   <Interactive.Div name="AI interaction panel" style={{position:'absolute',right:65,top:210,width:565,height:665,borderRadius:24,background:'#14291ff5',color:paper,padding:34,boxShadow:'0 22px 80px #10201735',transform:`translateX(${(1-ease(f,0,24))*90}px)`}}>
    <div style={{fontSize:22,color:muted,letterSpacing:2}}>SCENEFLOW / AI ASSETS</div>
    <div style={{marginTop:40,minHeight:128,padding:23,background:'#304535',borderRadius:17,fontSize:29,lineHeight:1.4}}>{typing}{!sent&&<span style={{opacity:Math.floor(f/12)%2}}>|</span>}</div>
    {sent&&<div style={{marginTop:25,opacity:ease(f,145,165)}}>{isPlant?<div style={{display:'flex',gap:20}}>{[assets['river-birch'],assets['red-maple']].map((p,i)=><div key={p} style={{width:218,height:240,background:'#eef1e7',borderRadius:14,padding:12,color:ink}}><Img src={staticFile(p)} style={{width:'100%',height:185,objectFit:'contain'}}/><div style={{fontSize:18,marginTop:5}}>{i?'Acer rubrum':'Betula nigra'}</div></div>)}</div>:<div style={{height:230,background:'#c3ac8c',borderRadius:15,overflow:'hidden'}}><Photo src="materials-cedar/Promo-Human.png" style={{position:'relative',height:230}}/><div style={{position:'absolute',background:'#183021e8',padding:12,fontSize:22,bottom:145}}>Real-world scale</div></div>}</div>}
    <div style={{position:'absolute',left:34,right:34,bottom:38,display:'flex',justifyContent:'space-between',alignItems:'center'}}><span style={{fontSize:22,color:muted}}>{isPlant?'Mixed palette':'UV ready'}</span><Button>{applied?(isPlant?'Planted ✓':'Applied ✓'):(isPlant?'Plant on surface':'Apply to object')}</Button></div>
   </Interactive.Div>
   {f>210&&<Cursor x={interpolate(f,[210,235],[1720,1695],clamp)} y={interpolate(f,[210,235],[920,780],clamp)} press={f>235&&f<250}/>}
   <Tag>{isPlant?'Generate. Reuse. Place.':'AI material → physical UV → object'}</Tag><Note>Interaction visualization · actual SceneFlow outputs</Note>
 </AbsoluteFill>;
};
const Camera:React.FC=()=>{
 const f=useCurrentFrame();const top=f<180;return <AbsoluteFill style={{background:paper}}>{top?<Orbit phase="overhead" overhead start={0} speed={.67}/>:<Photo src="planted-summer/Promo-Human.png" style={{transform:`scale(${1.03+.0001*(f-180)})`}}/>}<Head size={110}>{top?'Every angle.':'Get closer.'}</Head><Tag>{top?(f<120?'Z-axis → camera-facing':'Automatic crown plan'):'Human perspective'}</Tag><div style={{position:'absolute',right:80,bottom:65,display:'flex',gap:14}}><Button active={!top}>Human</Button><Button active={top}>Top</Button></div></AbsoluteFill>;
};
const PlantRules:React.FC=()=>{
 const f=useCurrentFrame();const random=f>60&&f<150;const individual=f>=150;return <AbsoluteFill style={{background:paper}}><Photo src={individual?'plant-individual-edit/Promo-Axon.png':random?'plant-randomized/Promo-Axon.png':'planted-summer/Promo-Axon.png'} style={{transform:`scale(${1+ease(f,0,225)*.075})`,transformOrigin:'45% 65%'}}/><Head size={105}>{individual?'One plant. Your call.':'A little randomness.'}</Head>
 <Interactive.Div name="Plant parameter gesture" style={{position:'absolute',right:70,top:275,width:420,padding:30,borderRadius:20,background:'#14291ff5',color:paper}}>
  <div style={{fontSize:25,marginBottom:35}}>{individual?'Individual edit':'Plant group'}</div>
  {[['Density',random?'0.018':'0.012'],['Layout seed',random?'811':'2312'],['Size range',random?'0.60 — 1.65':'0.80 — 1.25']].map(([label,val],i)=><div key={label} style={{margin:'28px 0'}}><div style={{display:'flex',justifyContent:'space-between',fontSize:22}}><span>{label}</span><b>{individual&&i===2?'1.45 ×':val}</b></div><div style={{height:5,background:'#52654b',marginTop:16,position:'relative'}}><div style={{height:5,width:`${30+(random?25:0)+i*12}%`,background:lime}}/><span style={{position:'absolute',left:`${30+(random?25:0)+i*12}%`,top:-6,width:17,height:17,borderRadius:'50%',background:lime}}/></div></div>)}
  <div style={{fontSize:22,marginTop:30}}>Mirror <span style={{float:'right',color:lime}}>On ✓</span></div>
 </Interactive.Div><Cursor x={interpolate(f,[15,80,170],[1660,1710,1580],clamp)} y={interpolate(f,[15,80,170],[465,465,640],clamp)} press={f>50&&f<68}/><Tag>{individual?'Custom size · species · mirror':'Independent seeds. Stable control.'}</Tag><Note>Time compressed · actual parameter variants</Note></AbsoluteFill>;
};
const Seasons:React.FC=()=>{
 const f=useCurrentFrame();const index=Math.min(3,Math.floor(f/90));const phase=phases[index];return <AbsoluteFill style={{background:paper}}><Orbit phase={phase} start={f*.45} speed={0}/><Head size={122}>{['Summer.','Autumn.','Winter.','Your season.'][index]}</Head><div style={{position:'absolute',left:75,bottom:68,display:'flex',gap:18}}>{['Summer','Autumn','Winter'].map((s,i)=><div key={s} style={{padding:'13px 20px',borderRadius:25,background:i===index%3?ink:'#ffffffb0',color:i===index%3?paper:ink,fontSize:24}}>{s}</div>)}</div><Note>Native Rhino orbit · seasonal assets</Note></AbsoluteFill>;
};
const ExportView:React.FC=()=>{
 const f=useCurrentFrame();const late=f>110;return <AbsoluteFill style={{background:paper}}><Photo src={late?'sun-high/Promo-Axon.png':'sun-low/Promo-Axon.png'}/><Head size={110}>Light.<br/>Then deliver.</Head><Interactive.Div name="View export controls" style={{position:'absolute',right:70,top:210,width:490,padding:32,borderRadius:22,background:'#14291ff5',color:paper}}><div style={{fontSize:27}}>Hillside / Axon</div><div style={{fontSize:21,color:muted,margin:'32px 0 15px'}}>Sun altitude</div><div style={{height:5,background:'#53644a',position:'relative'}}><div style={{width:late?'68%':'24%',background:lime,height:5}}/></div><div style={{textAlign:'right',marginTop:12,fontSize:28}}>{late?'48°':'16°'}</div><div style={{display:'flex',gap:12,margin:'30px 0'}}>{['1K','2K','4K','8K'].map((s,i)=><span key={s} style={{padding:'12px 17px',borderRadius:8,fontSize:24,background:(f>155?i===2:i===1)?lime:'#304535',color:(f>155?i===2:i===1)?ink:paper}}>{s}</span>)}</div><div style={{fontSize:21,lineHeight:1.9,color:'#d7e3ce'}}>✓ Plants & shadows<br/>✓ Materials & textures<br/>✓ Arctic & depth</div><div style={{marginTop:25}}><Button>Export PSD</Button></div></Interactive.Div><Cursor x={1680} y={f>155?f>200?766:459:335} press={f>195&&f<220}/><Tag>Named views. Your output stack.</Tag><Note>Interaction visualization</Note></AbsoluteFill>;
};
const channels=[['plants','Plants'],['shadow','Shadows'],['textures','Materials'],['arctic','Arctic'],['depth','Depth'],['colors','Material ID']];
const Layers:React.FC=()=>{
 const f=useCurrentFrame();const index=Math.min(5,Math.floor(f/60));const moving=f%60;return <AbsoluteFill style={{background:'#0d1913',color:paper}}><div style={{height:48,background:'#1e3026',padding:'12px 25px',fontSize:19}}>Hillside.psd <span style={{float:'right',color:muted}}>Layers / six ways to work</span></div><Head dark top={82} size={112}>{channels[index][1]}<span style={{color:lime}}>.</span></Head>
 <div style={{position:'absolute',left:50,top:210,width:1640,height:650,background:'#e9ede3',overflow:'hidden',borderRadius:4}}><Photo src={'psd/'+channels[index][0]+'.png'} style={{objectFit:'contain',transform:`translate(${interpolate(moving,[0,59],[-25,20],clamp)}px,${interpolate(moving,[0,59],[10,-10],clamp)}px) scale(1.03)`}}/></div>
 <div style={{position:'absolute',right:25,top:230,width:200,fontSize:19,lineHeight:2.7,color:muted}}>{channels.map(([key,label],i)=><div key={key} style={{paddingLeft:15,background:i===index?'#3d5730':'transparent',color:i===index?paper:muted}}>◉ {label}</div>)}</div>
 <div style={{position:'absolute',left:125,right:220,bottom:48,height:145,display:'flex',gap:20,alignItems:'flex-end',justifyContent:'center'}}>{channels.map(([key,label],i)=><div key={key} style={{width:i===index?260:170,transform:`translateY(${i===index?-20:0}px)`,transformOrigin:'bottom',borderRadius:12,background:i===index?'#496133':'#23342a',padding:9,border:i===index?'2px solid #d9ff7b':'1px solid #53664d'}}><Img src={path('psd/'+key+'.png')} style={{height:i===index?120:86,width:'100%',objectFit:'contain'}}/><div style={{fontSize:18,textAlign:'center',color:i===index?lime:paper}}>{label}</div></div>)}</div><Note>Concept layer workspace · actual PSD channels</Note></AbsoluteFill>;
};
const styleImages=['hillside-textured-architectural-collage-no-border','monet','starry-night','hillside-magenta-cobalt','hillside-coral-gold','hillside-turquoise-oil','animated-film'];
const AiStyles:React.FC=()=>{
 const f=useCurrentFrame();const montage=f>150;const n=Math.floor(Math.max(0,f-150)/30)%styleImages.length;return <AbsoluteFill style={{background:ink}}>{montage?<Photo src={'ai/'+styleImages[n]+'.png'} style={{transform:`scale(${1.03+(f%30)*.0005})`}}/>:<Photo src="planted-summer/Promo-Human.png"/>}
 {!montage&&<Interactive.Div name="Short brief interaction" style={{position:'absolute',left:110,right:110,bottom:100,padding:28,borderRadius:22,background:'#14291ff5',color:paper,display:'flex',justifyContent:'space-between',fontSize:34}}><span>{'Warm, textured architectural collage.'.slice(0,Math.floor(f/2))}<span style={{opacity:f%30<15?1:0}}>|</span></span><Button>{f>95?'Expand brief ✓':'Generate'}</Button></Interactive.Div>}
 {!montage&&f>95&&<div style={{position:'absolute',left:110,right:110,bottom:225,padding:24,borderRadius:18,background:'#14291ff0',color:paper,fontSize:27,lineHeight:1.5}}>Warm mineral walls. Tactile grain. Quiet daylight.<br/><span style={{color:lime}}>Arctic / form · Depth / space · Shadow / light</span></div>}{montage&&<div style={{position:'absolute',left:50,top:50,padding:'14px 22px',background:'#102018cc',color:paper,fontSize:30,fontWeight:700}}>One model. Many possibilities.</div>}<Note>Actual SceneFlow AI outputs · time compressed</Note></AbsoluteFill>;
};
const LocalEdit:React.FC=()=>{
 const f=useCurrentFrame();const after=f>180;const z=1+ease(f,100,280)*1.25;return <AbsoluteFill style={{background:paper,overflow:'hidden'}}><div style={{position:'absolute',inset:0,transform:`scale(${z})`,transformOrigin:'51% 63%'}}><Photo src={after?'ai/monet-local-edit.png':'ai/monet.png'}/>{!after&&<svg viewBox="0 0 1280 720" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}><rect x="570" y="402" width="144" height="96" fill="#ebad3b22" stroke="#946700" strokeWidth="3" opacity={ease(f,15,40)}/><path d="M1000 218 L656 446" fill="none" stroke="#946700" strokeWidth="4" strokeDasharray="500" strokeDashoffset={500*(1-ease(f,40,90))}/><path d="M660 425 L656 446 L677 441" fill="none" stroke="#946700" strokeWidth="4" opacity={ease(f,80,95)}/><text x="900" y="130" fill="#754d00" fontSize="22" opacity={ease(f,90,110)}>Deep teal timber.</text></svg>}</div><Head size={100}>{after?'Precisely there.':'Point. Describe.'}</Head><Tag>{after?'Outside the edit mask: unchanged':'Mark an area. Add your intent.'}</Tag><div style={{position:'absolute',right:65,bottom:60}}><Button>{after?'Updated ✓':'Update image'}</Button></div><Note>Actual local edit · annotation gesture visualized</Note></AbsoluteFill>;
};
const Hd:React.FC=()=>{
 const f=useCurrentFrame();const complete=f>155;return <AbsoluteFill style={{background:ink}}><Photo src="ai/monet-4k.png" style={{transform:`scale(${interpolate(f,[0,100,299],[1,1,2.1],clamp)})`,transformOrigin:'56% 61%'}}/>{!complete&&<div style={{position:'absolute',inset:0,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gridTemplateRows:'repeat(2,1fr)'}}>{Array.from({length:6},(_,i)=><div key={i} style={{border:'1px solid #a6c66d99',background:i<Math.floor(f/25)?'#9dbd5518':'transparent'}}/>)}</div>}<div style={{position:'absolute',left:64,top:65,color:ink,fontSize:120,fontWeight:850,lineHeight:.9,letterSpacing:-7}}>{complete?'Every detail.':'Go 4K.'}</div>{!complete&&<div style={{position:'absolute',right:65,bottom:70,display:'flex',gap:18,padding:20,borderRadius:16,background:'#14291ff5',alignItems:'center',color:paper,fontSize:28}}><span>Output</span><Button>4096 × 2304</Button></div>}<Tag>{complete?'Actual 4096 × 2304 output':'Approved whole image → six detail tiles'}</Tag><Note>{complete?'Actual 4K image':'Refinement time compressed'}</Note></AbsoluteFill>;
};
const Finale:React.FC=()=>{
 const f=useCurrentFrame();const closing=f>150;const shots=['white/Promo-Axon.png','materials-cedar/Promo-Axon.png','planted-summer/Promo-Axon.png','ai/monet.png','ai/hillside-magenta-cobalt.png'];return <AbsoluteFill style={{background:ink,color:paper}}>{!closing?<><Photo src={shots[Math.min(4,Math.floor(f/30))]}/><div style={{position:'absolute',left:60,bottom:55,fontSize:37,fontWeight:750,color:f<90?ink:paper,background:f<90?'#eef4e9b0':'#102018b0',padding:'12px 20px'}}>From model to possibility.</div></>:<><div style={{position:'absolute',left:95,top:180,fontSize:210,fontWeight:850,letterSpacing:-14,opacity:ease(f,150,165)}}>SceneFlow<span style={{color:lime}}>/</span></div><div style={{position:'absolute',left:109,top:440,fontSize:52,color:'#bcd1ad'}}>Think it. Place it. Make it.</div><div style={{position:'absolute',left:110,bottom:105,fontSize:29,color:muted}}>Rhino → PSD → AI</div><div style={{position:'absolute',right:110,bottom:105,fontSize:24,color:muted}}>github.com/baoying-liu/RhinoSceneFlow</div></>}</AbsoluteFill>;
};

export const PromoFilm:React.FC=()=>{
 const {fps}=useVideoConfig();return <AbsoluteFill style={{fontFamily:"Arial, 'Segoe UI', sans-serif",background:ink}}>
  <Sequence name="01 / White model opening" durationInFrames={6*fps}><Opening/></Sequence>
  <Sequence name="02 / Material interaction" from={6*fps} durationInFrames={12*fps}><Chat kind="material"/></Sequence>
  <Sequence name="03 / Plant interaction" from={18*fps} durationInFrames={12*fps}><Chat kind="plants"/></Sequence>
  <Sequence name="04 / Camera and crown plan" from={30*fps} durationInFrames={10*fps}><Camera/></Sequence>
  <Sequence name="05 / Randomness and individual edit" from={40*fps} durationInFrames={8*fps}><PlantRules/></Sequence>
  <Sequence name="06 / Seasonal orbit montage" from={48*fps} durationInFrames={12*fps}><Seasons/></Sequence>
  <Sequence name="07 / Light and export settings" from={60*fps} durationInFrames={8*fps}><ExportView/></Sequence>
  <Sequence name="08 / Layer dock" from={68*fps} durationInFrames={14*fps}><Layers/></Sequence>
  <Sequence name="09 / Brief and style worlds" from={82*fps} durationInFrames={10*fps}><AiStyles/></Sequence>
  <Sequence name="10 / Spatial annotation edit" from={92*fps} durationInFrames={10*fps}><LocalEdit/></Sequence>
  <Sequence name="11 / Four K detail" from={102*fps} durationInFrames={10*fps}><Hd/></Sequence>
  <Sequence name="12 / From model to result" from={112*fps} durationInFrames={8*fps}><Finale/></Sequence>
  <Audio name="Original SceneFlow score" src={staticFile('audio/sceneflow-film-120.wav')} volume={.8}/>
 </AbsoluteFill>;
};

