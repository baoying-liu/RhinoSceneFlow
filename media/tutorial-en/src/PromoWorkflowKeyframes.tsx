import React from 'react';
import {AbsoluteFill, Img, Interactive, staticFile} from 'remotion';

const ink='#17251d', paper='#f7f8f4', lime='#d9ff79';
const image=(path:string)=>staticFile(`case/promo-20261112/${path}`);
const Frame:React.FC<{children:React.ReactNode;dark?:boolean;concept?:boolean}>=({children,dark=false,concept=false})=><AbsoluteFill style={{background:dark?'#111913':paper,fontFamily:'Arial, sans-serif',overflow:'hidden'}}>
 {children}
 <div style={{position:'absolute',left:80,top:48,fontSize:28,fontWeight:700,letterSpacing:-1,color:dark?paper:ink}}>SceneFlow /</div>
 {concept&&<div style={{position:'absolute',right:80,bottom:40,fontSize:12,letterSpacing:2,color:dark?'#a9b69d':'#64745e'}}>INTERACTION CONCEPT · ACTUAL OUTPUT</div>}
</AbsoluteFill>;
const Heading:React.FC<{children:React.ReactNode;dark?:boolean}>=({children,dark=false})=><Interactive.Div name="Main message" style={{position:'absolute',left:75,top:125,fontSize:132,fontWeight:800,letterSpacing:-8,lineHeight:.94,color:dark?paper:ink}}>{children}</Interactive.Div>;
const Hero:React.FC<{path:string}>=({path})=><Img name="Actual Rhino capture" src={image(path)} style={{position:'absolute',width:1920,height:1080,left:300,top:35,mixBlendMode:'multiply'}}/>;

export const WorkflowMaterial:React.FC=()=><Frame concept>
 <Hero path="materials-terracotta/Promo-Human.png"/>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,#f7f8f4 0%,#f7f8f4d9 25%,transparent 53%)'}}/>
 <Heading>Type.<br/>Create.</Heading>
 <div style={{position:'absolute',left:82,top:440,width:500,padding:28,background:'#fff',border:'1px solid #d9dfd2',borderRadius:20,boxShadow:'0 25px 70px #18342015'}}>
  <div style={{fontSize:21,fontWeight:700,color:ink,marginBottom:25}}>Asset chat</div>
  <div style={{marginLeft:42,padding:20,borderRadius:'18px 18px 2px 18px',background:'#e9efdf',fontSize:27,lineHeight:1.3,color:ink}}>Pale terracotta.<br/>Matte. 200 mm tiles.</div>
  <div style={{marginTop:25,fontSize:23,lineHeight:1.4,color:'#506348'}}>Material ready.<br/>1.6 × 1.6 m · Physical scale</div>
  <div style={{marginTop:25,padding:'16px 20px',borderRadius:8,background:ink,color:lime,fontSize:24,fontWeight:600}}>Apply to object ↗</div>
 </div>
</Frame>;

export const WorkflowPlantRules:React.FC=()=><Frame concept>
 <Hero path="plant-randomized/Promo-Axon.png"/>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,#f7f8f4 0%,#f7f8f4df 22%,transparent 49%)'}}/>
 <Heading>Your rules.</Heading>
 <div style={{position:'absolute',left:84,top:365,width:475,padding:'30px 32px',borderRadius:18,background:'#fff',border:'1px solid #d9dfd2',boxShadow:'0 25px 70px #18342015',color:ink}}>
  <div style={{fontSize:22,marginBottom:28,fontWeight:700}}>Birch + Maple</div>
  {[["Density","0.018 / m²"],["Layout seed","811"],["Size range","0.60 — 1.65"],["Mirror seed","813"]].map(([label,value])=><div key={label} style={{margin:'22px 0'}}><div style={{display:'flex',justifyContent:'space-between',fontSize:23}}><span style={{color:'#62725b'}}>{label}</span><strong>{value}</strong></div><div style={{height:4,background:'#e2e9d9',marginTop:16}}><div style={{width:label==='Size range'?'76%':'58%',height:'100%',background:'#8ca85a'}}/></div></div>)}
  <div style={{fontSize:26,fontWeight:700,marginTop:36}}>23 plants. One group.</div>
 </div>
</Frame>;

export const WorkflowCamera:React.FC=()=><Frame>
 <Img name="Actual human camera" src={image('planted-summer/Promo-Human.png')} style={{position:'absolute',width:1920,height:1080,mixBlendMode:'multiply'}}/>
 <div style={{position:'absolute',inset:0,clipPath:'polygon(61% 0,100% 0,100% 100%,41% 100%)',background:paper}}><Img name="Actual top camera with plan plants" src={image('planted-summer/Promo-Top.png')} style={{position:'absolute',width:1920,height:1080,mixBlendMode:'multiply'}}/></div>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f7f8f4 0%,#f7f8f490 18%,transparent 46%)'}}/>
 <Heading>Every angle.</Heading>
 <div style={{position:'absolute',left:82,bottom:70,fontSize:30,fontWeight:700,color:ink}}>Human / Elevation</div>
 <div style={{position:'absolute',right:82,bottom:70,fontSize:30,fontWeight:700,color:ink}}>Top / Crown plan</div>
</Frame>;

export const WorkflowSeasons:React.FC=()=><Frame>
 {['season-spring','planted-summer','season-autumn','season-winter'].map((phase,i)=><div key={phase} style={{position:'absolute',inset:0,clipPath:`inset(0 ${75-i*25}% 0 ${i*25}%)`}}><Img name={phase} src={image(`${phase}/Promo-Axon.png`)} style={{width:1920,height:1080,mixBlendMode:'multiply'}}/></div>)}
 <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f7f8f4 0%,#f7f8f480 15%,transparent 38%)'}}/>
 <Heading>Seasons change.</Heading>
 {['Spring','Summer','Autumn','Winter'].map((s,i)=><div key={s} style={{position:'absolute',left:i*480+80,bottom:65,color:ink,fontSize:29,fontWeight:600}}>{s}</div>)}
</Frame>;

export const WorkflowPsdDock:React.FC=()=><Frame dark concept>
 <Heading dark>Every layer.<br/><span style={{color:lime}}>In reach.</span></Heading>
 <Img name="Actual exported material channel" src={image('psd/textures.png')} style={{position:'absolute',left:920,top:200,width:920,height:517.5,background:'#edf2e4',boxShadow:'0 40px 100px #0007',transform:'perspective(1600px) rotateY(-9deg) rotateZ(2deg)',border:'1px solid #748163'}}/>
 <div style={{position:'absolute',left:82,top:470,fontSize:28,color:'#b5c4a5'}}>Hillside.psd</div>
 {['plants','shadow','textures','arctic','depth','colors'].map((name,i)=><div key={name} style={{position:'absolute',left:80+i*290,top:i===2?775:850,width:250,height:142,scale:i===2?1.35:1,transformOrigin:'50% 100%',background:'#cbd7bc1c',border:i===2?`2px solid ${lime}`:'1px solid #8fa17b55',borderRadius:10,boxShadow:'0 20px 35px #0006'}}><Img src={image(`psd/${name}.png`)} style={{width:'100%',height:'100%',objectFit:'contain'}}/><div style={{color:i===2?lime:'#c9d4bc',textAlign:'center',fontSize:19,marginTop:13}}>{['Plants','Shadows','Materials','Arctic','Depth','Material ID'][i]}</div></div>)}
</Frame>;

export const WorkflowAiWorlds:React.FC=()=><Frame dark>
 <Img name="Actual starry-night generation" src={image('ai/starry-night.png')} style={{position:'absolute',inset:0,width:1920,height:1080,objectFit:'cover'}}/>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#081929af 0%,transparent 50%,#08192966 100%)'}}/>
 <Heading dark>What if?</Heading>
 <Img name="Actual impressionist generation" src={image('ai/monet.png')} style={{position:'absolute',left:935,top:660,width:430,height:242,border:'5px solid #f4f6ec',boxShadow:'0 30px 70px #0008',transform:'rotate(-7deg)'}}/>
 <Img name="Actual animated-background generation" src={image('ai/animated-film.png')} style={{position:'absolute',left:1380,top:700,width:430,height:242,border:'5px solid #f4f6ec',boxShadow:'0 30px 70px #0008',transform:'rotate(6deg)'}}/>
 <div style={{position:'absolute',left:82,bottom:90,color:paper,fontSize:43,fontWeight:600,lineHeight:1.2}}>One model.<br/><span style={{color:lime}}>Many worlds.</span></div>
</Frame>;

export const WorkflowLocalEdit:React.FC=()=><Frame dark>
 <Heading dark>Point.<br/><span style={{color:lime}}>Refine.</span></Heading>
 <Img name="Actual annotation context submitted to AI" src={image('ai/edit-context.png')} style={{position:'absolute',left:670,top:95,width:1120,height:630,objectFit:'contain',background:'#fff',border:'1px solid #77876b',transform:'rotate(-5deg)',boxShadow:'0 35px 80px #0008'}}/>
 <Img name="Actual masked edit result" src={image('ai/monet-local-edit.png')} style={{position:'absolute',left:500,top:400,width:1120,height:630,border:'1px solid #77876b',transform:'rotate(2deg)',boxShadow:'0 35px 80px #0008'}}/>
 <div style={{position:'absolute',left:1410,top:740,width:360,height:240,overflow:'hidden',border:`3px solid ${lime}`,borderRadius:10,boxShadow:'0 20px 70px #0009'}}><Img name="Real edited facade detail" src={image('ai/monet-local-edit.png')} style={{position:'absolute',width:3200,height:1800,left:-1425,top:-1005}}/></div>
 <div style={{position:'absolute',left:82,bottom:90,color:'#c8d7b9',fontSize:28}}>Mark the change.<br/>Keep the rest.</div>
</Frame>;
