const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),esbuild=require('esbuild');
const root=path.resolve(__dirname,'../..'),r=JSON.parse(fs.readFileSync(path.join(root,'artifacts/layout022-latest.json'))),fixture=JSON.parse(fs.readFileSync(path.join(r.folder,'parity.json')));
const code=esbuild.transformSync(fs.readFileSync(path.join(__dirname,'src/model.js'),'utf8'),{format:'cjs'}).code;
const moduleObject={exports:{}};new Function('module','exports',code)(moduleObject,moduleObject.exports);const m=moduleObject.exports;
assert.deepEqual(m.arrangeNodes(fixture.nodes),fixture.arranged);assert.deepEqual(m.avoidNodes(fixture.trial,fixture.anchor),fixture.avoided);
const ports=m.branchPorts(fixture.arranged),first=ports[0],parent=fixture.arranged.find(n=>n.id===first.parent),child=fixture.arranged.find(n=>n.id===first.child);
assert.equal(first.x,m.frameBox(parent).x+parent.frame.width);assert.equal(first.endX,m.frameBox(child).x);
const closed=m.canvasGraph(fixture.arranged,[first.child]);assert(!closed.visible.some(n=>n.id===first.child));
const reduced=m.arrangeNodes(fixture.arranged,[first.child]);assert(m.branchPorts(reduced,[first.child]).find(p=>p.child===first.child).collapsed);
const moved=m.placeNodes(fixture.arranged,new Map([[parent.id,{x:parent.pose.x+37,y:parent.pose.y-21}]])),live=m.branchPorts(moved).find(p=>p.child===first.child);assert.equal(live.x,first.x+37);assert.equal(live.y,first.y-21);
// Frames, not image rectangles, are the collision units. Repeated drag samples remain collision-free.
for(let i=0;i<12;i++){const nodes=m.avoidNodes(m.placeNodes(fixture.arranged,new Map([[child.id,{x:i*110,y:i*55}]])),child.id);const visible=m.canvasGraph(nodes).visible;for(let a=0;a<visible.length;a++)for(let b=a+1;b<visible.length;b++)assert(!m.overlaps(m.frameBox(visible[a]),m.frameBox(visible[b])));}
const result={pythonJsParity:true,nodes:80,framePorts:true,perChildFold:true,liveEndpoints:true,dragSamplesNoOverlap:12};fs.writeFileSync(path.join(r.folder,'js-verified.json'),JSON.stringify(result));console.log(JSON.stringify(result));
