import React from 'react';
import {AbsoluteFill,Img,Sequence,interpolate,staticFile,useCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';
const clean='#f4f6ee',clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const easing=(f:number,a=42,b=72)=>{const t=Math.max(0,Math.min(1,(f-a)/(b-a)));return t*t*(3-2*t)};
const src=(p:string)=>staticFile('case/'+p);
const ImagePlane:React.FC<{file:string;style?:React.CSSProperties}>=({file,style})=><Img src={src(file)} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',...style}}/>;
const a='promo-revision-v03/single-actions/material-before.png',b='promo-revision-v03/single-actions/material-after.png',p='promo-revision-v03/single-actions/plant-after.png';
export const TransitionOption:React.FC<{kind?:number}>=({kind=0})=>{
 const f=useCurrentFrame(),t=easing(f),hit=Math.sin(Math.PI*t);
 return <AbsoluteFill style={{background:'#112219',overflow:'hidden',perspective:1800}}>
 <Sequence name="Original whoosh" from={42} durationInFrames={24}><Audio src={staticFile('audio/sceneflow-whoosh.wav')} volume={kind===2?.5:.3}/></Sequence>
 {kind===0&&<><ImagePlane file={a} style={{scale:1+.19*t,transformOrigin:'54% 65%',filter:`blur(${hit*4}px)`,opacity:1-easing(f,53,65)}}/><ImagePlane file={b} style={{scale:1+.19*(1-t),transformOrigin:'54% 65%',filter:`blur(${hit*4}px)`,opacity:easing(f,53,65)}}/></>}
 {kind===1&&<><ImagePlane file={b} style={{translate:`${-t*1920}px 0`,filter:`blur(${hit*19}px)`}}/><ImagePlane file={p} style={{translate:`${(1-t)*1920}px 0`,filter:`blur(${hit*19}px)`}}/></>}
 {kind===2&&<><ImagePlane file="promo-20261112/psd/textures.png" style={{background:clean,opacity:easing(f,52,82)}}/>{[5,4,3,2,1,0].map(i=><div key={i} style={{position:'absolute',left:(270+i*145)*(1-t)+460*t,top:(170+i*47)*(1-t)+259*t,width:1000,height:562,background:i===2?clean:'#b2c4a515',border:'1px solid #c2d8ad66',boxShadow:'0 25px 55px #0005',transform:`perspective(1800px) scale(${i===2?1+2.2*t:1-.3*t}) rotateY(${-22*(1-t)}deg) rotateX(${28*(1-t)}deg) rotateZ(${-8*(1-t)}deg)`,opacity:(i===2?1:1-t)*(1-easing(f,72,95))}}><ImagePlane file={'promo-20261112/psd/'+['plants','shadow','textures','arctic','depth','colors'][i]+'.png'} style={{objectFit:'contain'}}/></div>)}</>}
 {kind===3&&<><ImagePlane file="promo-20261112/planted-summer/Promo-Human.png"/><div style={{position:'absolute',inset:0,clipPath:`polygon(0 0,${t*130-15}% 0,${t*130+5}% 100%,0 100%)`}}><ImagePlane file="promo-styles-v04/01-photoreal-daylight.png"/></div></>}
 {kind===4&&<><ImagePlane file="promo-20261112/ai/hillside-textured-architectural-collage-no-border.png"/><div style={{position:'absolute',inset:0,transformOrigin:'0% 50%',transform:`perspective(1800px) rotateY(${-t*105}deg)`,backfaceVisibility:'hidden',boxShadow:'25px 0 70px #0007',opacity:1-easing(f,68,75)}}><ImagePlane file="promo-20261112/planted-summer/Promo-Human.png"/><div style={{position:'absolute',inset:0,background:`linear-gradient(90deg,transparent 40%,rgba(0,0,0,${hit*.25}))`}}/></div></>}
 <div style={{position:'absolute',left:36,top:32,padding:'14px 20px',borderRadius:10,background:'#112219dc',color:clean,fontFamily:'Arial, sans-serif',fontSize:27,fontWeight:700}}>{['A / Match push','B / Whip slide','C / Layer fly-through','D / Angled reveal','E / Paper peel'][kind]}</div>
 <div style={{position:'absolute',right:36,bottom:30,padding:'10px 16px',background:'#112219cc',color:'#c9d7bc',fontFamily:'Arial, sans-serif',fontSize:19}}>Transition study · actual SceneFlow assets</div>
 </AbsoluteFill>
};
export const TransitionShowcase:React.FC=()=> <AbsoluteFill>
 <Sequence name="A / Match push" durationInFrames={150}><TransitionOption kind={0}/></Sequence>
 <Sequence name="B / Whip slide" from={150} durationInFrames={150}><TransitionOption kind={1}/></Sequence>
 <Sequence name="C / Layer fly-through" from={300} durationInFrames={150}><TransitionOption kind={2}/></Sequence>
 <Sequence name="D / Angled reveal" from={450} durationInFrames={150}><TransitionOption kind={3}/></Sequence>
 <Sequence name="E / Paper peel" from={600} durationInFrames={150}><TransitionOption kind={4}/></Sequence>
 <Audio src={staticFile('audio/sceneflow-film-120.wav')} volume={f=>interpolate(f,[0,15,730,749],[0,.7,.7,0],clamp)}/>
 </AbsoluteFill>;
