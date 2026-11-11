// Development-only SVG rasterization. Runtime uses embedded transparent PNGs.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'src/RhinoSceneFlow.Plugin/Resources/InterfaceIcons');
const {chromium}=require(path.join(root,'artifacts/browser-harness/node_modules/playwright-core'));
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const page=await browser.newPage({viewport:{width:64,height:64},deviceScaleFactor:1});
 for(const file of fs.readdirSync(dir).filter(f=>f.endsWith('.svg')&&(!process.argv[2]||f===process.argv[2]+'.svg')))for(const [theme,color] of [['light','#26332b'],['dark','#edf2ee']])for(const size of [16,20,24,32]){
 const svg=fs.readFileSync(path.join(dir,file),'utf8');
 await page.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:${size}px;height:${size}px;color:${color}}</style>${svg}`);
 await page.locator('svg').screenshot({path:path.join(dir,file.replace('.svg',`-${theme}-${size}.png`)),omitBackground:true});
 }
 console.log('Rasterized canonical SVGs, 4 sizes Ã— 2 themes.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
