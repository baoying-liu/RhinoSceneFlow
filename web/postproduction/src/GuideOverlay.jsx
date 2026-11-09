import React from 'react';
import {instructionLayers,guideGate,blankResult,visibleEditReference} from './model';

export default function GuideOverlay({scene,node,style,useImage,assetPath}){
 if(!scene||blankResult(node)||node.checkout||!guideGate(node,'visible')||!guideGate(node,'specialVisible'))return null;
 const layers=instructionLayers(scene,node).filter(x=>x.visible);
 return <svg className="instructionOverlay" viewBox={`0 0 ${node.pose.width} ${node.pose.height}`} preserveAspectRatio="none" style={style} aria-hidden="true">
 <defs><pattern id={'hatch-'+node.id} width="16" height="16" patternUnits="userSpaceOnUse"><path d="M-4 16L16-4M8 24L24 8" stroke="#e8ae59" strokeOpacity=".18" strokeWidth="1"/></pattern></defs>
 {layers.map(item=><Entry key={item.id} item={item} node={node} board={scene.id} useImage={useImage} assetPath={assetPath}/>)}
 </svg>;
}
function Entry({item,node,board,useImage,assetPath}){
 const a=item.local,r=item.resource,im=useImage(a?.raster?assetPath(board,a.raster):r?assetPath(board,r.preview):null),edited=r?visibleEditReference(r):null,overlay=useImage(edited?assetPath(board,edited.preview):null);
 if(r){const p={...r.pose,x:r.pose.x-node.pose.x,y:r.pose.y-node.pose.y};return <g>{im&&<image href={im.src} {...p}/ >}{im&&overlay&&<image href={overlay.src} {...p}/>}</g>;}
 if(a.raster)return im?<image href={im.src} {...a.rasterPose}/>:null;
 const pts=(a.points||[]).map(p=>p.slice(0,2).join(',')).join(' '),text=['text','label'].includes(a.kind);
 if(text)return <g>{a.kind==='label'&&<rect x={a.x-3} y={a.y-3} width={Math.max(20,(a.text||'').length*a.size*.7)} height={a.size+6} fill="#20382b"/>}<text x={a.x} y={a.y+a.size} fill={a.color} fontSize={a.size}>{(a.text||'').split('\n').map((s,i)=><tspan key={i} x={a.x} dy={i?a.size:0}>{s}</tspan>)}</text></g>;
 if(['edit','protect'].includes(a.kind)&&a.closed)return <polygon points={pts} fill={`url(#hatch-${node.id})`} stroke={a.kind==='protect'?'#d96d77':'#54a982'} strokeWidth="1.5"/>;
 const points=a.points||[],end=points.at(-1),prev=points.at(-2),angle=end&&prev?Math.atan2(end[1]-prev[1],end[0]-prev[0]):0,size=Math.max(12,a.size*4);
 return <g><polyline points={pts} fill="none" stroke={a.color} strokeWidth={a.size} strokeLinecap="round" strokeLinejoin="round"/>{a.kind==='arrow'&&prev&&<polygon points={`${end[0]},${end[1]} ${end[0]-size*Math.cos(angle-.5)},${end[1]-size*Math.sin(angle-.5)} ${end[0]-size*Math.cos(angle+.5)},${end[1]-size*Math.sin(angle+.5)}`} fill={a.color}/>}</g>;
}
