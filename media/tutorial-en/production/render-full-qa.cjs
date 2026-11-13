const fs=require('fs'),path=require('path');const {bundle}=require('@remotion/bundler'),{getCompositions,renderStill}=require('@remotion/renderer');
(async()=>{const out=path.resolve('out/promo-final-v06/qa');fs.mkdirSync(out,{recursive:true});const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),publicDir:path.resolve(process.argv.includes('--lean')?'../../artifacts/promo-final-v06/public':'public')});const c=(await getCompositions(serveUrl)).find(x=>x.id==='SceneFlow-Introduction-v06');for(const sec of (process.argv.includes("--corrections")?[89,182,227,231]:[3,20,28,37,55,64,76,89,101,114,123,134,147,155,162,168,182,192,199,204,215,222,231,245,250])){await renderStill({serveUrl,composition:c,output:path.join(out,'frame-'+sec+'.jpg'),imageFormat:'jpeg',frame:sec*30,jpegQuality:92});console.log('Checked frame '+sec+'s');}})().catch(e=>{console.error(e.message);process.exitCode=1});



