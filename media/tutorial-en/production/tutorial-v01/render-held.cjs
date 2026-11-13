// Render every animated frame; hold truly static UI/caption states unchanged.
// This is equivalent to the authored frame-driven composition, not a frame-rate reduction.
const fs=require('fs'),path=require('path');
const {bundle}=require('@remotion/bundler');const {getCompositions,renderFrames}=require('@remotion/renderer');
(async()=>{
 const out=path.resolve('out/tutorial-full-v01');const rows=JSON.parse(fs.readFileSync(path.join(out,'timeline.json')));
 const total=rows.at(-1).start+rows.at(-1).frames;let cuts=new Set([0,total]);
 for(const cue of rows){
  const add=f=>{if(f>=0&&f<cue.frames)cuts.add(cue.start+f)};
  add(0);cuts.add(cue.start+cue.frames);
  for(const f of [31,61,114,150,180,240,300,450])add(f);
  for(const c of cue.captions){add(Math.ceil(c.startMs*.03));add(Math.ceil(c.endMs*.03));}
  if(['T02-01','T10-01','T11-01'].includes(cue.id))for(let f=0;f<=6;f++)add(f);
  for(const s of cue.shots){
   const at=Math.round(s.at*30);add(at);
   if(s.menu){add(at+31);add(at+114);}
   if(s.kind==='establish')for(let f=at;f<Math.min(cue.frames,at+240);f++)add(f);
   if(s.video){
    let begin=at+Math.round((s.videoAt||0)*30);
    let end=s.kind==='web'?at+(s.video==='compare-whole.mp4'?182:122):at+Math.round((s.videoEnd||6)*30);
    for(let f=begin;f<Math.min(cue.frames,end);f++)add(f);add(end);
   }
  }
 }
 let frames=[...cuts].filter(x=>x<total).sort((a,b)=>a-b);
 fs.writeFileSync(path.join(out,'frame-hold-plan.json'),JSON.stringify({total,frames,cuts:[...cuts].sort((a,b)=>a-b)},null,2));
 const cueArg=process.argv.indexOf('--cue');if(cueArg>=0){const cue=rows.find(c=>c.id===process.argv[cueArg+1]);if(!cue)throw Error('Unknown cue');frames=frames.filter(f=>f>=cue.start&&f<cue.start+cue.frames);}
 const dir=path.join(out,'held-frames');fs.mkdirSync(dir,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),publicDir:path.resolve('public')});
 const composition=(await getCompositions(serveUrl)).find(c=>c.id==='SceneFlow-Tutorial-Full-v01');let last=-1;
 console.log('Rendering '+frames.length+' distinct frames; all motion remains 30 fps');
 await renderFrames({serveUrl,composition,frames,outputDir:null,inputProps:{},imageFormat:'jpeg',jpegQuality:95,muted:true,concurrency:4,
  onFrameBuffer:(buffer,frame)=>fs.writeFileSync(path.join(dir,String(frame).padStart(5,'0')+'.jpg'),buffer),
  onFrameUpdate:n=>{let p=Math.floor(n/frames.length*100);fs.writeFileSync(path.join(out,'held-progress.json'),JSON.stringify({rendered:n,total:frames.length,percent:p}));if(p!==last){last=p;console.log('Distinct-frame render '+p+'%');}}
 });
 const all=JSON.parse(fs.readFileSync(path.join(out,'frame-hold-plan.json'))).frames;for(const f of all)if(!fs.existsSync(path.join(dir,String(f).padStart(5,'0')+'.jpg')))throw Error('Missing held frame '+f);
 fs.writeFileSync(path.join(out,'held-complete.json'),JSON.stringify({distinctFrames:all.length,totalFrames:total,animatedFrameRate:30}));console.log('Distinct frames ready');
})().catch(e=>{console.error(e.stack);process.exitCode=1});
