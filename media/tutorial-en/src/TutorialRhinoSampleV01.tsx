import React from 'react';
import {AbsoluteFill,Audio,Img,Sequence,interpolate,staticFile,useCurrentFrame} from 'remotion';
import type {Caption} from '@remotion/captions';
import captions from './data/tutorial-rhino-sample-v01.json';

const asset=(s:string)=>staticFile(`case/tutorial-rhino-sample-v01/${s}`);
const keyframes=[
 {t:0,x:300,y:230,sy:0,z:1.35},
 {t:5.8,x:27,y:377,sy:0,z:1.35},
 {t:7.2,x:400,y:436,sy:270,z:1.5},
 {t:10.2,x:400,y:436,sy:270,z:1.5},
 {t:12,x:80,y:408,sy:270,z:1.5},
 {t:15.5,x:28,y:535,sy:270,z:1.5},
 {t:17,x:240,y:559,sy:385,z:1.5},
 {t:27.5,x:81,y:559,sy:385,z:1.5},
 {t:33,x:106,y:559,sy:385,z:1.5},
 {t:38,x:95,y:655,sy:385,z:1.5},
 {t:41.6,x:81,y:525,sy:100,z:1.5},
 {t:45,x:106,y:525,sy:100,z:1.5},
 {t:49.5,x:106,y:525,sy:100,z:1.5},
];
export const TutorialRhinoSampleV01:React.FC=()=>{
 const f=useCurrentFrame(),t=f/30;
 const a=keyframes.reduce((v,k)=>k.t<=t?k:v,keyframes[0]);
 const b=keyframes.find(k=>k.t>a.t)??a;
 const q=interpolate(t,[Math.max(a.t,b.t-.7),b.t===a.t?a.t+.01:b.t],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const ease=q*q*(3-2*q);
 const mix=(k:'x'|'y'|'sy'|'z')=>a[k]+(b[k]-a[k])*ease;
 // Camera movement anticipates the next action only during its short approach.
 const z=mix('z'),sy=mix('sy');
 const state=t<7?'01':t<10.2?'02':t<16.4?'03':t<41.6?'04':'05';
 const cap=(captions as Caption[]).find(c=>t*1000>=c.startMs&&t*1000<c.endMs);
 const pulse=[6.9,10.2,16.4].map(v=>Math.abs(t-v)).reduce((x,y)=>Math.min(x,y),99);
 const mouseX=50+mix('x')*z,mouseY=112+(mix('y')-sy)*z;
 const fade=interpolate(f,[0,12,1465,1485],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 return <AbsoluteFill style={{background:'#141c1c',color:'#f2f6f1',fontFamily:'Arial',opacity:fade}}>
  <Audio src={asset('narration.wav')}/>
  <div style={{position:'absolute',left:44,top:28,fontSize:27,fontWeight:600}}>SceneFlow <span style={{fontWeight:400,color:'#a9bbb5'}}> / Named view → layered PSD</span></div>
  <div style={{position:'absolute',right:44,top:34,fontSize:18,color:'#a9bbb5'}}>Rhino 8 · tutorial sample</div>
  <div style={{position:'absolute',left:38,top:92,width:900,height:850,border:'1px solid #4a5955',borderRadius:12,overflow:'hidden',background:'#eee'}}>
   {['01','02','03','04','05'].map(s=><Img key={s} src={asset(`state-${s}.jpg`)} style={{position:'absolute',left:12,top:20,width:600,height:1040,transformOrigin:'0 0',transform:`translateY(${-sy*z}px) scale(${z})`,visibility:s===state?'visible':'hidden'}}/>)}
  </div>
  <div style={{position:'absolute',left:963,top:180,width:920,height:690,background:'white',borderRadius:10,overflow:'hidden'}}>
   <Img src={asset('viewport.png')} style={{width:'100%',height:'100%',objectFit:'contain'}}/>
  </div>
  <div style={{position:'absolute',left:968,top:890,color:'#a9bbb5',fontSize:18}}>01 Hillside Axon · native Rhino view</div>
  <svg width={1920} height={1080} style={{position:'absolute',pointerEvents:'none'}}>
   {pulse<.4?<circle cx={mouseX} cy={mouseY} r={12+pulse*65} fill="none" stroke="#edb864" strokeWidth={4} opacity={1-pulse/.4}/>:null}
   <g transform={`translate(${mouseX},${mouseY})`}><path d="M0 0 L0 34 L9 26 L17 43 L24 40 L16 24 L29 23 Z" fill="white" stroke="#141c1c" strokeWidth={2.5}/></g>
  </svg>
  {cap?<Sequence name="English subtitles" layout="none"><div style={{position:'absolute',bottom:32,left:200,right:200,textAlign:'center'}}><span style={{display:'inline-block',background:'rgba(5,10,10,.92)',borderRadius:7,padding:'13px 28px',fontSize:36,lineHeight:1.25}}>{cap.text}</span></div></Sequence>:null}
 </AbsoluteFill>;
};


