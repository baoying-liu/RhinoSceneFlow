// Next-generation input is deliberately separate from the pinned comparison input.
export function generationInput(board,node){
 if(!node)return null;
 if(node.original)return {...node,skipped:[]};
 let parent=board.nodes.find(n=>n.id===node.parentId),skipped=[],seen=new Set();
 while(parent?.archived){if(seen.has(parent.id))return null;seen.add(parent.id);skipped.unshift({id:parent.id,summary:parent.archiveSummary||''});parent=board.nodes.find(n=>n.id===parent.parentId);}
 return parent?{...parent,skipped}:null;
}
