import React from 'react';
import {AbsoluteFill, Img, Interactive, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';

const font="'Segoe UI', Arial, sans-serif";
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;

const Paper:React.FC<{dark?:boolean}>=({dark=false})=><AbsoluteFill style={{
  backgroundColor:dark?'#102c25':'#f6f5ee',
  backgroundImage:dark?'radial-gradient(#b9d3b322 1px, transparent 1px)':'radial-gradient(#153c2b19 1px, transparent 1px)',
  backgroundSize:'32px 32px',fontFamily:font,
}}/>;

const Enter:React.FC<{children:React.ReactNode;delay?:number;style?:React.CSSProperties}>=({children,delay=0,style})=>{
 const f=useCurrentFrame();
 return <div style={{...style,opacity:interpolate(f,[delay,delay+22],[0,1],clamp),translate:`0px ${interpolate(f,[delay,delay+30],[35,0],clamp)}px`}}>{children}</div>;
};

const Eyebrow:React.FC<{children:React.ReactNode;dark?:boolean}>=({children,dark=false})=><Interactive.Div name="Scene label" style={{
 fontFamily:font,fontSize:26,fontWeight:600,letterSpacing:5,textTransform:'uppercase',color:dark?'#bdd8ad':'#42664d',
}}>{children}</Interactive.Div>;

const Header:React.FC<{children:React.ReactNode;dark?:boolean}>=({children,dark=false})=><Interactive.Div name="Headline" style={{
 fontFamily:font,fontSize:104,lineHeight:1.05,fontWeight:600,letterSpacing:-5,color:dark?'#f6f5ee':'#15392c',whiteSpace:'pre-line',
}}>{children}</Interactive.Div>;

const Identity:React.FC=()=> <AbsoluteFill>
 <Paper dark/>
 <Enter style={{position:'absolute',left:150,top:175}}>
  <Eyebrow dark>Independent open-source project</Eyebrow>
 </Enter>
 <Enter delay={8} style={{position:'absolute',left:140,top:300}}>
  <Interactive.Div name="SceneFlow wordmark" style={{fontFamily:font,fontSize:212,fontWeight:600,letterSpacing:-12,color:'#f6f5ee'}}>SceneFlow<span style={{color:'#b9d6a3'}}>.</span></Interactive.Div>
 </Enter>
 <Enter delay={30} style={{position:'absolute',left:150,top:610,width:1450}}>
  <Interactive.Div name="Opening statement" style={{fontFamily:font,fontSize:62,color:'#c5d3c7',lineHeight:1.2}}>From a Rhino model to a reviewable image.</Interactive.Div>
 </Enter>
 <Enter delay={48} style={{position:'absolute',left:150,top:865}}>
  <Interactive.Div name="Presenter" style={{fontFamily:font,fontSize:30,color:'#9bb5a4'}}>A workflow by Baoying Liu</Interactive.Div>
 </Enter>
</AbsoluteFill>;

const FloatingCase:React.FC=()=>{
 const f=useCurrentFrame();const {durationInFrames}=useVideoConfig();
 return <div style={{position:'absolute',left:700,top:100,width:1120,height:840,background:'white',borderRadius:22,overflow:'hidden',boxShadow:'0 30px 90px #173b2b20',scale:interpolate(f,[0,durationInFrames],[.97,1.025],clamp)}}>
  <Img src={staticFile('case/before.png')} name="Actual case export" style={{width:1120,height:840,objectFit:'contain'}}/>
 </div>;
};
const Case:React.FC=()=> <AbsoluteFill>
 <Paper/>
 <Enter style={{position:'absolute',left:140,top:200,width:570}}>
  <Eyebrow>One continuous example</Eyebrow>
 </Enter>
 <Enter delay={12} style={{position:'absolute',left:140,top:300,width:570}}>
  <Header>{'One model.\nA connected\nworkflow.'}</Header>
 </Enter>
 <Enter delay={36} style={{position:'absolute',left:145,top:720,width:470}}>
  <Interactive.Div name="Case description" style={{fontFamily:font,fontSize:36,lineHeight:1.4,color:'#58705b'}}>A hillside retreat, built in Rhino and carried through to AI postproduction.</Interactive.Div>
 </Enter>
 <FloatingCase/>
 <div style={{position:'absolute',right:145,bottom:75,fontFamily:font,fontSize:24,color:'#617365'}}>Previously exported demonstration model</div>
</AbsoluteFill>;

const Wipe:React.FC=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 const x=interpolate(f,[0,2*fps,8*fps,10*fps],[.06,.06,.94,.94],clamp);
 return <div style={{position:'absolute',left:680,top:130,width:1120,height:840,background:'#fff',overflow:'hidden',borderRadius:20,boxShadow:'0 30px 80px #173b2b15'}}>
  <Img src={staticFile('case/before.png')} name="Original viewport image" style={{position:'absolute',width:1120,height:840}}/>
  <div style={{position:'absolute',inset:0,clipPath:`inset(0 ${(1-x)*100}% 0 0)`}}>
   <Img src={staticFile('case/after.png')} name="Previous AI variation" style={{position:'absolute',width:1120,height:840}}/>
  </div>
  <div style={{position:'absolute',left:x*1120,top:0,bottom:0,width:3,background:'#c5a25c'}}/>
  <div style={{position:'absolute',left:x*1120-24,top:390,width:48,height:48,borderRadius:48,background:'#15392c',color:'#fff',display:'flex',alignItems:'center',justifyContent:'center',fontSize:28}}>↔</div>
  <div style={{position:'absolute',left:30,top:26,padding:'12px 20px',fontFamily:font,fontSize:24,color:'#fff',background:'#15392c',borderRadius:8}}>AI variation</div>
  <div style={{position:'absolute',right:30,top:26,padding:'12px 20px',fontFamily:font,fontSize:24,color:'#15392c',background:'#eff1e9',borderRadius:8}}>Original export</div>
 </div>;
};
const Compare:React.FC=()=> <AbsoluteFill>
 <Paper/>
 <Enter style={{position:'absolute',left:140,top:205}}><Eyebrow>Compare before you commit</Eyebrow></Enter>
 <Enter delay={12} style={{position:'absolute',left:140,top:310,width:500}}><Header>{'Explore.\nCompare.\nRefine.'}</Header></Enter>
 <Enter delay={32} style={{position:'absolute',left:145,top:750,width:440}}><Interactive.Div name="Review message" style={{fontFamily:font,fontSize:36,lineHeight:1.4,color:'#58705b'}}>Keep the source visible. Review geometry and material changes.</Interactive.Div></Enter>
 <Wipe/>
</AbsoluteFill>;

const Step:React.FC<{number:string;label:string;detail:string;delay:number;left:number}>=({number,label,detail,delay,left})=>
 <Enter delay={delay} style={{position:'absolute',left,top:480,width:290,height:280,padding:28,border:'1px solid #95b49c55',borderRadius:16,background:'#18382e'}}>
  <div style={{fontFamily:font,fontSize:30,color:'#a7c48d',marginBottom:40}}>{number}</div>
  <div style={{fontFamily:font,fontSize:43,color:'#f6f5ee',fontWeight:600,marginBottom:18}}>{label}</div>
  <div style={{fontFamily:font,fontSize:28,lineHeight:1.3,color:'#b2c6b7'}}>{detail}</div>
 </Enter>;
const PathLine:React.FC=()=>{
 const f=useCurrentFrame();
 return <div style={{position:'absolute',left:150,top:620,height:2,width:interpolate(f,[15,120],[0,1600],clamp),background:'#b9d6a3'}}/>;
};
const Workflow:React.FC=()=> <AbsoluteFill>
 <Paper dark/>
 <Enter style={{position:'absolute',left:150,top:175}}><Eyebrow dark>The full tutorial</Eyebrow></Enter>
 <Enter delay={8} style={{position:'absolute',left:145,top:265}}><Header dark>Built around your design workflow.</Header></Enter>
 <PathLine/>
 <Step number="01" label="Materials" detail="AI assets + real-scale UV" delay={20} left={150}/>
 <Step number="02" label="Planting" detail="Editable groups + variation" delay={40} left={482}/>
 <Step number="03" label="Views" detail="Named Views + layered PSD" delay={60} left={814}/>
 <Step number="04" label="AI studio" detail="Annotations + traceable variants" delay={80} left={1146}/>
 <Enter delay={105} style={{position:'absolute',left:150,top:865}}><Interactive.Div name="Workflow outcome" style={{fontFamily:font,fontSize:34,color:'#bdd8ad'}}>An editable model. Clear inputs. Reviewable results.</Interactive.Div></Enter>
</AbsoluteFill>;

const Layer:React.FC<{label:string;image:string;top:number;delay:number;muted?:boolean}>=({label,image,top,delay,muted=false})=>
 <Enter delay={delay} style={{position:'absolute',left:760,top,width:980,height:108,borderRadius:14,background:muted?'#e9eee5':'#fff',border:'1px solid #bdcabb',boxShadow:'0 12px 30px #173b2b10',display:'flex',alignItems:'center',padding:'0 24px',gap:34}}>
  <div style={{width:140,height:86,background:'white',borderRadius:8,overflow:'hidden'}}><Img src={staticFile('case/'+image+'.png')} style={{width:140,height:86,objectFit:'contain'}}/></div>
  <div style={{fontFamily:font,fontSize:38,color:'#15392c',fontWeight:500}}>{label}</div>
  {muted?<div style={{marginLeft:'auto',fontFamily:font,fontSize:24,color:'#6b7b67'}}>Optional guide</div>:null}
 </Enter>;
const Layers:React.FC=()=> <AbsoluteFill>
 <Paper/>
 <Enter style={{position:'absolute',left:140,top:190}}><Eyebrow>From Rhino to PSD</Eyebrow></Enter>
 <Enter delay={10} style={{position:'absolute',left:140,top:310,width:570}}><Header>{'Keep useful\ninformation\nseparate.'}</Header></Enter>
 <Enter delay={30} style={{position:'absolute',left:145,top:745,width:500}}><Interactive.Div name="PSD explanation" style={{fontFamily:font,fontSize:34,lineHeight:1.4,color:'#58705b'}}>Control visibility, grouping and which layers inform the AI.</Interactive.Div></Enter>
 <Layer label="Plants" image="plants" top={140} delay={12}/>
 <Layer label="Shadow" image="shadow" top={265} delay={24}/>
 <Layer label="Material textures" image="textures" top={390} delay={36}/>
 <Layer label="Arctic" image="arctic" top={515} delay={48}/>
 <Layer label="Depth" image="depth" top={640} delay={60} muted/>
 <Layer label="Material colors" image="colors" top={765} delay={72} muted/>
</AbsoluteFill>;

const Ending:React.FC=()=> <AbsoluteFill>
 <Paper dark/>
 <Enter style={{position:'absolute',left:150,top:175}}><Eyebrow dark>SceneFlow · complete walkthrough</Eyebrow></Enter>
 <Enter delay={10} style={{position:'absolute',left:145,top:310,width:1500}}><Header dark>{'Let’s build the\nwhole workflow.'}</Header></Enter>
 <Enter delay={38} style={{position:'absolute',left:150,top:660,width:1250}}><Interactive.Div name="Tutorial promise" style={{fontFamily:font,fontSize:48,color:'#bfd0c1',lineHeight:1.35}}>Materials and UV. Editable planting. Layered export. AI postproduction.</Interactive.Div></Enter>
 <Enter delay={65} style={{position:'absolute',left:150,top:880}}><Interactive.Div name="Preview disclosure" style={{fontFamily:font,fontSize:27,color:'#9bb5a4'}}>Preview software · AI account and model access required</Interactive.Div></Enter>
</AbsoluteFill>;

export const Intro:React.FC<{showDraftLabel:boolean}>=({showDraftLabel})=><AbsoluteFill>
 <TransitionSeries>
  <TransitionSeries.Sequence name="Identity" durationInFrames={180}><Identity/></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames:18})}/>
  <TransitionSeries.Sequence name="The real case" durationInFrames={450}><Case/></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames:18})}/>
  <TransitionSeries.Sequence name="Before and after" durationInFrames={390}><Compare/></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames:18})}/>
  <TransitionSeries.Sequence name="Workflow" durationInFrames={450}><Workflow/></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames:18})}/>
  <TransitionSeries.Sequence name="PSD layer channels" durationInFrames={390}><Layers/></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames:18})}/>
  <TransitionSeries.Sequence name="Tutorial invitation" durationInFrames={390}><Ending/></TransitionSeries.Sequence>
 </TransitionSeries>
 {showDraftLabel?<div style={{position:'absolute',right:44,top:28,fontFamily:font,fontSize:19,letterSpacing:2,color:'#708477',background:'#eef3e8ee',padding:'9px 14px',borderRadius:7}}>STYLE STUDY · SILENT PREVIEW</div>:null}
</AbsoluteFill>;
