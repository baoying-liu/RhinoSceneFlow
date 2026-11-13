const fs=require('fs'),path=require('path');
const {bundle}=require('@remotion/bundler');
const {getCompositions,renderMedia,renderStill}=require('@remotion/renderer');
(async()=>{
 const output=path.resolve('out/tutorial-full-v01');fs.mkdirSync(output,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),publicDir:path.resolve('public')});
 const composition=(await getCompositions(serveUrl)).find(c=>c.id==='SceneFlow-Tutorial-Full-v01');
 const timeline=JSON.parse(fs.readFileSync(path.join(output,'timeline.json')));
 if(process.argv.includes('qa')){
  for(const id of ['T02-01','T03-01','T04-01','T05-05','T06-01','T07-04','T08-03','T10-02','T11-04','T12-02','T13-03']){
   const cue=timeline.find(c=>c.id===id);await renderStill({serveUrl,composition,frame:cue.start+Math.min(cue.frames-1,270),output:path.join(output,'QA-'+id+'.png')});
  }
  console.log('QA frames ready');return;
 }
 let last=-1;
 await renderMedia({serveUrl,composition,codec:'h264',outputLocation:path.join(output,'SceneFlow-Tutorial-15min-v01.mp4'),crf:18,concurrency:4,imageFormat:'jpeg',jpegQuality:93,isProduction:false,onProgress:p=>{
  fs.writeFileSync(path.join(output,'render-progress.json'),JSON.stringify(p));let percent=Math.floor(p.progress*100);if(percent!==last){last=percent;console.log('Render '+percent+'%');}
 }});
 console.log('Full tutorial rendered');
})().catch(e=>{console.error(e.stack);process.exitCode=1});
