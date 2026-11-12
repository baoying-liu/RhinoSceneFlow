import React from 'react';
import {AbsoluteFill, Img, Interactive, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';

const font = "Arial, 'Segoe UI', sans-serif";
const ink = '#17251d';
const lime = '#d9ff79';
const clamp = {extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const photo = (name:string) => staticFile(`case/${name}.png`);

const Title:React.FC<{children:React.ReactNode;light?:boolean;top?:number}> = ({children,light=false,top=120}) => {
  const f=useCurrentFrame();
  return <Interactive.Div name="Beat headline" style={{position:'absolute',left:80,top,fontFamily:font,fontSize:145,fontWeight:800,lineHeight:.91,letterSpacing:-9,color:light?'#f4f6ed':ink,translate:interpolate(f,[0,9],['0px 35px','0px 0px'],clamp),opacity:interpolate(f,[0,5],[0,1],clamp)}}>{children}</Interactive.Div>;
};

const Opening:React.FC=()=>{
  const f=useCurrentFrame();
  return <AbsoluteFill style={{background:'#f7f8f4',overflow:'hidden'}}>
    <Img name="Architectural camera push" src={photo('hero-hd')} style={{position:'absolute',width:2300,height:1725,left:-60,top:-445,mixBlendMode:'multiply',transformOrigin:'68% 51%',scale:interpolate(f,[0,17,85,119],[1.4,1.13,1.02,1.08],clamp),translate:interpolate(f,[0,119],['80px 20px','-40px -10px'],clamp)}}/>
    <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,#f7f8f4ee 0%,#f7f8f460 34%,transparent 65%)'}}/>
    <Sequence from={15}><Title top={190}>Make<br/>it real<span style={{color:'#7c9b42'}}>.</span></Title></Sequence>
    <Interactive.Div name="SceneFlow signature" style={{position:'absolute',left:84,bottom:66,color:ink,fontSize:33,fontFamily:font,fontWeight:700}}>SceneFlow /</Interactive.Div>
    <div style={{position:'absolute',inset:0,background:'#fff',opacity:interpolate(f,[0,4],[.85,0],clamp)}}/>
  </AbsoluteFill>;
};

const Materials:React.FC=()=>{
  const f=useCurrentFrame();
  const stage=Math.floor(f/30);
  const asset=['promo-arctic','promo-textures','before','hero-hd'][Math.min(stage,3)];
  return <AbsoluteFill style={{background:'#f7f8f4',overflow:'hidden'}}>
    <Img name="Material matched cut" src={photo(asset)} style={{position:'absolute',width:2120,height:1590,left:-90,top:-280,mixBlendMode:'multiply',scale:interpolate(f%30,[0,29],[1.035,1],clamp)}}/>
    <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f7f8f4 0%,transparent 47%)'}}/>
    <Title top={98}>{stage===0?'Start simple.':'Make it yours.'}</Title>
    <div style={{position:'absolute',left:85,bottom:70,padding:'13px 22px',background:ink,color:'#eef4df',fontFamily:font,fontSize:25,fontWeight:600}}>{['WHITE MODEL','MATERIALS','PLANTING','DETAIL'][Math.min(stage,3)]}</div>
    <div style={{position:'absolute',inset:0,background:'#fff',opacity:interpolate(f%30,[0,3],[.28,0],clamp)}}/>
  </AbsoluteFill>;
};

const Planting:React.FC=()=>{
 const f=useCurrentFrame();
 return <AbsoluteFill style={{background:'#f7f8f4',overflow:'hidden'}}>
   <div style={{position:'absolute',inset:0,transformOrigin:'53% 61%',scale:interpolate(f,[0,89],[1.12,1.02],clamp),translate:interpolate(f,[0,89],['-55px 0px','30px -20px'],clamp)}}>
     <Img name="Terrain and material base" src={photo('promo-textures')} style={{position:'absolute',width:1920,height:1440,top:-250,left:0,mixBlendMode:'multiply'}}/>
     <div style={{position:'absolute',inset:0,clipPath:`inset(0 ${interpolate(f,[0,12,30,42],[100,65,65,0],clamp)}% 0 0)`}}>
       <Img name="Plants appear on beat" src={photo('promo-plants')} style={{position:'absolute',width:1920,height:1440,top:-250,left:0}}/>
     </div>
   </div>
   <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f7f8f4 0%,transparent 47%)'}}/>
   <Title top={105}>Bring it<br/>to life<span style={{color:'#7c9b42'}}>.</span></Title>
   <div style={{position:'absolute',right:84,bottom:65,color:ink,fontFamily:font,fontSize:25}}>Plants. In place.</div>
 </AbsoluteFill>;
};

const LayerPlane:React.FC<{src:string;index:number;name:string}>=({src,index,name})=>{
 const f=useCurrentFrame();
 const spread=interpolate(f,[0,30,70,119],[0,1,1,.22],clamp);
 return <div style={{position:'absolute',left:430+(index-2.5)*130*spread,top:310+index*30*spread,width:800,height:600,transform:`perspective(1700px) rotateY(${-18*spread}deg) rotateX(${32*spread}deg) rotateZ(${-8*spread}deg)`,opacity:interpolate(f,[0,8],[.6,1],clamp)}}>
   <div style={{position:'absolute',inset:0,background:'#ecf3df0d',border:'1px solid #d0e7bb77',boxShadow:'0 20px 50px #0004'}}/>
   <Img name={name} src={photo(src)} style={{width:'100%',height:'100%',objectFit:'contain'}}/>
 </div>;
};

const Layers:React.FC=()=>{
 const f=useCurrentFrame();
 const selected=Math.min(5,Math.floor(f/15));
 return <AbsoluteFill style={{background:'#111913',fontFamily:font,overflow:'hidden'}}>
   <Title light top={95}>Every layer.<br/><span style={{color:lime}}>Yours.</span></Title>
   <LayerPlane src="depth" index={5} name="Depth layer"/>
   <LayerPlane src="promo-arctic" index={4} name="Arctic layer"/>
   <LayerPlane src="colors" index={3} name="Material ID layer"/>
   <LayerPlane src="promo-shadow" index={2} name="Shadow layer"/>
   <LayerPlane src="promo-textures" index={1} name="Material texture layer"/>
   <LayerPlane src="promo-plants" index={0} name="Plant layer"/>
   <div style={{position:'absolute',right:80,top:240,width:345,padding:'23px 0',background:'#252d25',border:'1px solid #657454',borderRadius:12,boxShadow:'0 35px 90px #0006'}}>
     <div style={{fontSize:22,color:'#dbe6cd',padding:'0 24px 20px'}}>Hillside.psd</div>
     {['Plants','Shadows','Materials','Arctic','Depth','Material ID'].map((name,i)=><div key={name} style={{padding:'17px 24px',fontSize:23,color:i===selected?lime:'#c5cfbc',background:i===selected?'#d9ff791a':'transparent',borderLeft:i===selected?`3px solid ${lime}`:'3px solid transparent'}}>◉ <span style={{marginLeft:15}}>{name}</span></div>)}
   </div>
   <div style={{position:'absolute',right:85,bottom:60,fontSize:14,letterSpacing:2,color:'#9eae90'}}>CONCEPT EDITOR · ACTUAL EXPORT</div>
 </AbsoluteFill>;
};

const Ai:React.FC=()=>{
 const f=useCurrentFrame();
 const x=interpolate(f,[0,15,44,60,89,105,119],[0,0,100,100,0,100,100],clamp);
 return <AbsoluteFill style={{background:'#f7f8f4',overflow:'hidden'}}>
   <div style={{position:'absolute',inset:0,transformOrigin:'63% 58%',scale:interpolate(f,[0,119],[1.02,1.23],clamp)}}>
     <Img name="Original AI input" src={photo('before')} style={{position:'absolute',width:2050,height:1537.5,left:-50,top:-265,mixBlendMode:'multiply'}}/>
     <div style={{position:'absolute',inset:0,clipPath:`inset(0 ${100-x}% 0 0)`}}><Img name="Actual previous AI result" src={photo('hero-hd')} style={{position:'absolute',width:2050,height:1537.5,left:-50,top:-265,mixBlendMode:'multiply'}}/></div>
   </div>
   <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f7f8f4 0%,#f7f8f480 24%,transparent 55%)'}}/>
   <Title top={100}>What if<span style={{color:'#7c9b42'}}>?</span></Title>
   <div style={{position:'absolute',left:85,bottom:62,color:ink,fontFamily:font,fontSize:30,fontWeight:600}}>One model. More possibilities.</div>
 </AbsoluteFill>;
};

const Ending:React.FC=()=>{
 const f=useCurrentFrame();
 return <AbsoluteFill style={{background:ink,fontFamily:font,display:'flex',alignItems:'center',justifyContent:'center',overflow:'hidden'}}>
   <Interactive.Div name="Final wordmark" style={{color:'#f2f6e9',fontWeight:800,fontSize:220,letterSpacing:-13,scale:interpolate(f,[0,7,29],[1.09,1,1],clamp),opacity:interpolate(f,[0,4],[0,1],clamp)}}>SceneFlow<span style={{color:lime}}>.</span></Interactive.Div>
   <div style={{position:'absolute',bottom:120,color:'#a9bd98',fontSize:22,letterSpacing:5}}>FROM MODEL TO POSSIBILITY.</div>
 </AbsoluteFill>;
};

export const PromoSample:React.FC=()=> <AbsoluteFill>
 <Audio src={staticFile('audio/sceneflow-pulse-120.wav')} volume={1}/>
 <Sequence name="01 / Architectural reveal" durationInFrames={120}><Opening/></Sequence>
 <Sequence name="02 / Material match cuts" from={120} durationInFrames={120}><Materials/></Sequence>
 <Sequence name="03 / Plant reveal" from={240} durationInFrames={90}><Planting/></Sequence>
 <Sequence name="04 / PSD explosion" from={330} durationInFrames={120}><Layers/></Sequence>
 <Sequence name="05 / Source to AI" from={450} durationInFrames={120}><Ai/></Sequence>
 <Sequence name="06 / Brand impact" from={570} durationInFrames={30}><Ending/></Sequence>
</AbsoluteFill>;
