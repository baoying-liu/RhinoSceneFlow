import React from 'react';
import {AbsoluteFill,Audio,Easing,Img,Sequence,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import type {Caption} from '@remotion/captions';
import captions from './data/tutorial-rhino-sample-v01.json';

const file=(name:string)=>staticFile(`case/tutorial-rhino-sample-v02/${name}`);
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const smooth={...clamp,easing:Easing.bezier(.42,0,.25,1)};
type Box={x:number;y:number;w:number;h:number};
const blend=(a:Box,b:Box,q:number):Box=>({x:a.x+(b.x-a.x)*q,y:a.y+(b.y-a.y)*q,w:a.w+(b.w-a.w)*q,h:a.h+(b.h-a.h)*q});
const keyframes=[
 {t:0,x:470,y:310,sy:0,z:1.05},
 {t:5.8,x:272,y:655,sy:0,z:1.05},
 {t:7.2,x:630,y:744,sy:470,z:1.38},
 {t:10.2,x:630,y:744,sy:470,z:1.38},
 {t:12,x:348,y:699,sy:470,z:1.38},
 {t:15.5,x:272,y:891,sy:470,z:1.38},
 {t:16.4,x:272,y:759,sy:650,z:1.38},
 {t:17,x:540,y:952,sy:740,z:1.38},
 {t:27.5,x:354,y:952,sy:740,z:1.38},
 {t:33,x:392,y:952,sy:740,z:1.38},
 {t:38,x:392,y:952,sy:740,z:1.38},
 {t:41.6,x:354,y:948,sy:530,z:1.38},
 {t:45,x:392,y:948,sy:530,z:1.38},
 {t:49.5,x:392,y:948,sy:530,z:1.38},
];

const SoftwareFraming:React.FC=()=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),t=f/fps,lesson=Math.max(0,t-6);
 const enter=interpolate(t,[4.2,6.4],[0,1],smooth);
 const leave=interpolate(t,[53,55.1],[0,1],smooth);
 const split=enter*(1-leave);
 const initialLeft={x:95.45,y:136.63,w:321.16,h:905.33};
 const initialRight={x:417.61,y:136.63,w:1275.70,h:889.06};
 const left=blend(initialLeft,{x:36,y:94,w:850,h:850},split);
 const right=blend(initialRight,{x:914,y:94,w:970,h:850},split);
 const a=keyframes.reduce((v,k)=>k.t<=lesson?k:v,keyframes[0]);
 const b=keyframes.find(k=>k.t>a.t)??a;
 const q=interpolate(lesson,[Math.max(a.t,b.t-.7),b.t===a.t?a.t+.01:b.t],[0,1],smooth);
 const mix=(k:'x'|'y'|'sy'|'z')=>a[k]+(b[k]-a[k])*q;
 const z=initialLeft.w/646+(mix('z')-initialLeft.w/646)*split;
 const sy=mix('sy')*split;
 const state=lesson<7?'01':lesson<10.2?'02':lesson<16.4?'03':lesson<41.6?'04':'05';
 const crop=blend({x:840,y:244,w:2566,h:1788},{x:960,y:560,w:2330,h:1340},split);
 const outline=interpolate(t,[2.5,3.1,6.5,7.1],[0,1,1,0],clamp)*(1-leave);
 const cursorOpacity=interpolate(t,[7,7.3,52,52.4],[0,1,1,0],clamp);
 const mouseX=left.x+(mix('x')-180)*z;
 const mouseY=left.y+(mix('y')-sy)*z;
 const pulse=[6.9,10.2,16.4].map(v=>Math.abs(lesson-v)).reduce((x,y)=>Math.min(x,y),99);
 return <AbsoluteFill style={{background:'#10251d'}}>
  <Img src={file('rhino-full.png')} style={{position:'absolute',width:1920,height:1049,top:15,opacity:1-split}}/>
  <Sequence name="Settings region to close-up" layout="none">
   <div style={{position:'absolute',left:left.x,top:left.y,width:left.w,height:left.h,overflow:'hidden',background:'#19382b',borderRadius:split*8}}>
    {['01','02','03','04','05'].map(s=><Img key={s} src={file(`dock-${s}.png`)} style={{position:'absolute',width:826,height:1821,left:-180*z,top:-sy*z,transform:`scale(${z})`,transformOrigin:'0 0',visibility:s===(split<.05?'01':state)?'visible':'hidden'}}/>)}
   </div>
  </Sequence>
  <Sequence name="Model viewport region" layout="none">
   <svg style={{position:'absolute',left:right.x,top:right.y,width:right.w,height:right.h,borderRadius:split*8,overflow:'hidden',background:'white'}} viewBox={`${crop.x} ${crop.y} ${crop.w} ${crop.h}`} preserveAspectRatio="xMidYMid meet"><defs><clipPath id="native-viewport-crop"><rect x={crop.x} y={crop.y} width={crop.w} height={crop.h}/></clipPath></defs><image href={file('rhino-full.png')} width={3862} height={2110} clipPath="url(#native-viewport-crop)"/></svg>
  </Sequence>
  <div style={{position:'absolute',left:left.x,top:left.y,width:left.w,height:left.h,outline:'3px solid #e9bb73',outlineOffset:3,opacity:outline,pointerEvents:'none'}}/>
  <div style={{position:'absolute',left:right.x,top:right.y,width:right.w,height:right.h,outline:'3px solid #aad6ca',outlineOffset:3,opacity:outline,pointerEvents:'none'}}/>
  <div style={{position:'absolute',left:38,top:34,color:'#e8eee7',fontFamily:'Arial',fontSize:25,opacity:split}}>PSD export settings</div>
  <div style={{position:'absolute',left:916,top:34,color:'#e8eee7',fontFamily:'Arial',fontSize:25,opacity:split}}>Rhino model view</div>
  <svg width={1920} height={1080} style={{position:'absolute',pointerEvents:'none',opacity:cursorOpacity}}>
   {pulse<.4?<circle cx={mouseX} cy={mouseY} r={12+pulse*65} fill="none" stroke="#edb864" strokeWidth={4} opacity={1-pulse/.4}/>:null}
   <g transform={`translate(${mouseX},${mouseY})`}><path d="M0 0 L0 34 L9 26 L17 43 L24 40 L16 24 L29 23 Z" fill="white" stroke="#10251d" strokeWidth={2.5}/></g>
  </svg>
 </AbsoluteFill>;
};

const EnglishSubtitles:React.FC=()=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig();
 const cap=(captions as Caption[]).find(c=>f/fps*1000>=c.startMs&&f/fps*1000<c.endMs);
 return cap?<div style={{position:'absolute',bottom:27,left:140,right:140,textAlign:'center',fontFamily:'Arial'}}><span style={{display:'inline-block',background:'rgba(5,13,9,.94)',color:'#f0f5ed',borderRadius:7,padding:'12px 25px',fontSize:36,lineHeight:1.25}}>{cap.text}</span></div>:null;
};

export const TutorialRhinoSampleV02:React.FC=()=>{
 const {fps}=useVideoConfig();
 return <AbsoluteFill>
  <SoftwareFraming/>
  <Sequence from={6*fps} name="Verified voice and English subtitles">
   <Audio src={file('narration.wav')}/>
   <EnglishSubtitles/>
  </Sequence>
 </AbsoluteFill>;
};
