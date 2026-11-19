const fs=require('fs'),path=require('path');
const {bundle}=require('@remotion/bundler');const {getCompositions,renderFrames}=require('@remotion/renderer');
(async()=>{
const O=path.resolve('out/tutorial-full-v02');const rows=JSON.parse(fs.readFileSync(path.join(O,'timeline.json')));
const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),publicDir:path.resolve('public')});
const composition=(await getCompositions(serveUrl)).find(c=>c.id==='SceneFlow-Tutorial-Full-v02');
const checks=[];for(const c of rows)for(const t of [4.2,9,15])checks.push({id:c.id,t,frame:c.start+Math.min(c.frames-1,Math.round(t*30))});
fs.writeFileSync(path.join(O,'qa-frames.json'),JSON.stringify(checks));
await renderFrames({serveUrl,composition,frames:checks.filter(x=>!process.argv.includes("--cue")||x.id===process.argv[process.argv.indexOf("--cue")+1]).map(x=>x.frame),outputDir:null,imageFormat:'jpeg',jpegQuality:92,muted:true,concurrency:4,onFrameBuffer:(b,f)=>{const c=checks.find(x=>x.frame===f);fs.writeFileSync(path.join(O,`QA-${c.id}-${c.t}.jpg`),b);},onFrameUpdate:n=>{if(n%15===0)console.log('QA '+n+'/'+checks.length)}});console.log('All cue QA ready');
})().catch(e=>{console.error(e);process.exitCode=1});
