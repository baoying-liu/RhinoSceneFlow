const esbuild=require('esbuild');const path=require('node:path');
esbuild.buildSync({entryPoints:['src/main.jsx'],bundle:true,minify:true,target:['chrome110','edge110'],outfile:path.resolve('../../src/RhinoSceneFlow.Plugin/PostProduction/board.js'),legalComments:'linked',define:{'process.env.NODE_ENV':'"production"'}});

const fs=require('node:fs'),lock=require('./package-lock.json');let notices='SceneFlow Studio — bundled production dependencies\n\n';
for(const [relative,info] of Object.entries(lock.packages)){if(!relative||info.dev)continue;const dir=path.resolve(relative);if(!fs.existsSync(path.join(dir,'package.json')))continue;const pkg=JSON.parse(fs.readFileSync(path.join(dir,'package.json'),'utf8'));notices+=pkg.name+' '+pkg.version+' — '+(pkg.license||'see license')+'\n';for(const file of ['LICENSE','LICENSE.txt','LICENSE.md','license','license.txt']){if(fs.existsSync(path.join(dir,file))){notices+=fs.readFileSync(path.join(dir,file),'utf8')+'\n';break;}}notices+='\n';}
fs.writeFileSync(path.resolve('../../src/RhinoSceneFlow.Plugin/PostProduction/board-LICENSES.txt'),notices);
