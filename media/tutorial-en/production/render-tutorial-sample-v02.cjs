const fs=require('fs'),path=require('path');const {bundle}=require('@remotion/bundler'),{getCompositions,renderMedia,renderStill}=require('@remotion/renderer');
(async()=>{const output=path.resolve(process.argv[3]||'out/tutorial-rhino-sample-v02/SceneFlow-Tutorial-Rhino-Sample-v02.mp4');fs.mkdirSync(path.dirname(output),{recursive:true});const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),publicDir:path.resolve(process.argv[2]||'public')});const composition=(await getCompositions(serveUrl)).find(c=>c.id==='SceneFlow-Tutorial-Rhino-Sample-v02');for(const frame of [90,165,300,1080,1470]){await renderStill({serveUrl,composition,frame,output:path.join(path.dirname(output),'frame-'+frame+'.png')});}let last=-1;await renderMedia({serveUrl,composition,codec:'h264',outputLocation:output,crf:16,concurrency:4,imageFormat:'jpeg',jpegQuality:95,isProduction:false,onProgress:p=>{fs.writeFileSync(path.join(path.dirname(output),'render-progress.json'),JSON.stringify(p));const t=Math.floor(p.progress*20);if(t!==last){last=t;console.log('Render '+Math.round(p.progress*100)+'%');}}});console.log('Completed '+output);})().catch(e=>{console.error(e.message);process.exitCode=1});




