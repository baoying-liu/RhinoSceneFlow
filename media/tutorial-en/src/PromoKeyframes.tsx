import React from 'react';
import {AbsoluteFill, Img, Interactive, staticFile} from 'remotion';

const font = "'Arial', 'Segoe UI', sans-serif";
const ink = '#17251d';
const lime = '#d9ff79';
const photo = (name: string) => staticFile(`case/${name}.png`);

const Signature: React.FC<{dark?: boolean}> = ({dark = false}) => <>
  <Interactive.Div name="Brand" style={{position:'absolute', left:80, top:48, fontSize:29, fontWeight:700, letterSpacing:-1, color:dark?'#eef2e9':ink}}>SceneFlow<span style={{color:dark?lime:'#658345'}}> /</span></Interactive.Div>
  <div style={{position:'absolute', right:80, top:56, fontSize:14, letterSpacing:4, color:dark?'#97a69b':'#718071'}}>FROM RHINO. FOR POSSIBILITY.</div>
</>;

export const PromoOpening: React.FC = () => <AbsoluteFill style={{background:'#f7f8f4', fontFamily:font, overflow:'hidden'}}>
  <Img name="Full-screen architectural close-up" src={photo('hero-hd')} style={{position:'absolute', width:2240, height:1680, left:90, top:-405, mixBlendMode:'multiply'}}/>
  <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg, #f7f8f4 0%, #f7f8f4e8 15%, transparent 56%)'}}/>
  <Signature/>
  <Interactive.Div name="Opening headline" style={{position:'absolute',left:74,top:195,fontSize:190,lineHeight:.88,fontWeight:800,letterSpacing:-13,color:ink}}>Make<br/>it real<span style={{color:'#7b9a42'}}>.</span></Interactive.Div>
  <div style={{position:'absolute',left:86,top:647,width:70,height:5,background:ink}}/>
  <Interactive.Div name="Opening subline" style={{position:'absolute',left:85,top:682,fontSize:29,lineHeight:1.3,color:'#566456'}}>Your model.<br/>A world of possibilities.</Interactive.Div>
  <div style={{position:'absolute',left:85,bottom:58,fontSize:15,letterSpacing:3,color:'#61715f'}}>MATERIALS / PLANTS / IMAGES</div>
</AbsoluteFill>;

const Plane: React.FC<{src:string;left:number;top:number;angle:number;opacity?:number}> = ({src,left,top,angle,opacity=1}) => <div style={{position:'absolute',left,top,width:650,height:487.5,transform:`perspective(1600px) rotateY(-22deg) rotateX(38deg) rotateZ(${angle}deg)`,transformOrigin:'center',opacity}}>
  <div style={{position:'absolute',inset:0,background:'#e6eddf18',boxShadow:'0 36px 70px #0007',border:'1px solid #a6b59b55'}}/>
  <Img src={photo(src)} name={`Export plane: ${src}`} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
</div>;

export const PromoLayers: React.FC = () => <AbsoluteFill style={{background:'#111913',fontFamily:font,overflow:'hidden'}}>
  <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 40% 75%, #42553655, transparent 62%)'}}/>
  <Signature dark/>
  <Interactive.Div name="PSD headline" style={{position:'absolute',left:76,top:147,fontSize:110,lineHeight:.96,fontWeight:750,letterSpacing:-6,color:'#f0f4e9'}}>Every layer.<br/><span style={{color:lime}}>Yours.</span></Interactive.Div>
  <Plane src="depth" left={845} top={555} angle={-15} opacity={.55}/>
  <Plane src="arctic" left={695} top={530} angle={-13} opacity={.72}/>
  <Plane src="colors" left={545} top={505} angle={-11} opacity={.85}/>
  <Plane src="shadow" left={395} top={480} angle={-9}/>
  <Plane src="textures" left={245} top={455} angle={-7}/>
  <Plane src="plants" left={95} top={430} angle={-5}/>
  <div style={{position:'absolute',left:1390,top:230,width:424,height:640,background:'#252b27',border:'1px solid #526048',borderRadius:14,boxShadow:'0 45px 120px #0008',overflow:'hidden'}}>
    <div style={{height:53,borderBottom:'1px solid #40483e',display:'flex',alignItems:'center',paddingLeft:25,color:'#aeb9a6',fontSize:15,letterSpacing:2}}>HILLSIDE.PSD <span style={{marginLeft:'auto',marginRight:25,color:lime}}>↓</span></div>
    <div style={{padding:'23px 25px 18px',fontSize:21,fontWeight:600,color:'#f1f4e8'}}>Layers</div>
    <div style={{padding:'0 25px 17px',fontSize:15,color:'#a4b09c'}}>Normal <span style={{float:'right'}}>100%</span></div>
    {['Plants','Shadows','Materials','Arctic','Depth','Material ID'].map((name,i)=><div key={name} style={{height:75,display:'flex',alignItems:'center',gap:15,padding:'0 20px',borderTop:'1px solid #ffffff0b',background:i===0?'#d9ff791a':'transparent',borderLeft:i===0?`3px solid ${lime}`:'3px solid transparent'}}>
      <span style={{fontSize:19,color:i>3?'#667060':'#d2d9ca'}}>◉</span>
      <Img src={photo(['plants','shadow','textures','arctic','depth','colors'][i])} style={{width:63,height:45,objectFit:'contain',background:'#d4dbcd',borderRadius:3}}/>
      <span style={{fontSize:19,color:i===0?lime:'#d5ddce'}}>{name}</span>
    </div>)}
  </div>
  <div style={{position:'absolute',right:108,bottom:80,fontSize:14,letterSpacing:2,color:'#93a188'}}>EDITOR CONCEPT · ACTUAL PSD CHANNELS</div>
  <div style={{position:'absolute',left:80,bottom:65,fontSize:17,letterSpacing:3,color:'#a8b99d'}}>ONE EXPORT. FULL CONTROL.</div>
</AbsoluteFill>;

export const PromoPossibilities: React.FC = () => <AbsoluteFill style={{background:'#f7f8f4',fontFamily:font,overflow:'hidden'}}>
  <Img name="Whole-image AI result" src={photo('hero-hd')} style={{position:'absolute',width:2140,height:1605,left:0,top:-275,mixBlendMode:'multiply'}}/>
  <div style={{position:'absolute',inset:0,clipPath:'polygon(0 0, 29% 0, 58% 100%, 0 100%)',background:'#eef0ea'}}>
    <Img name="Source image matched to result" src={photo('before')} style={{position:'absolute',width:2140,height:1605,left:0,top:-275,mixBlendMode:'multiply'}}/>
    <div style={{position:'absolute',inset:0,background:'#eff3e72a'}}/>
  </div>
  <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f7f8f4 0%,#f7f8f4e8 9%,transparent 43%,transparent 75%,#14251ac9 100%)'}}/>
  <Signature/>
  <Interactive.Div name="AI headline" style={{position:'absolute',left:75,top:144,fontSize:184,fontWeight:800,lineHeight:.95,letterSpacing:-12,color:ink}}>What if<span style={{color:'#7b9a42'}}>?</span></Interactive.Div>
  <div style={{position:'absolute',left:80,bottom:65,fontSize:38,lineHeight:1.2,letterSpacing:-1,color:'#f7f8ef'}}>One model.<br/><strong style={{color:lime}}>More possibilities.</strong></div>
  <div style={{position:'absolute',right:80,bottom:68,color:'#e4efd6',fontSize:17,letterSpacing:3,textAlign:'right'}}>SOURCE → AI<br/><span style={{fontSize:12,lineHeight:2.7,color:'#b6c4a8'}}>MATCHED-CAMERA TRANSITION STUDY</span></div>
</AbsoluteFill>;
