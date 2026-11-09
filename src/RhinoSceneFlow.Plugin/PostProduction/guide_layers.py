"""Shared instruction identity; display gates never enter generation signatures."""
import copy
import canvas_context as context

def gate(n,key):return (n.get('guideControls') or {}).get(key,True)

def items(b,n):
    if n['kind']!='image':return []
    f=context.frame(n);result=[]
    for entry in context.world_marks(b,include_disabled=True):
        a=entry['annotation']
        if context.area(context.bounds(a),f)>0:
            result.append(dict(id=a['id'],kind=a['kind'],home=entry['home'],name=a.get('text') or a['kind'],annotation=context.translate(a,-n['pose']['x'],-n['pose']['y']),visible=a.get('visible',True),enabled=a.get('enabled',True)))
    for r in b['nodes']:
        if r['kind']=='reference' and context.alive(r) and context.area(r['pose'],f)>0:
            p=r['pose'];result.append(dict(id=r['id'],kind='reference',home=r['id'],name=r['name'],visible=r.get('contextVisible',True),enabled=r.get('contextEnabled',True),pose=dict(p,x=p['x']-n['pose']['x'],y=p['y']-n['pose']['y']),resource=r))
    return result

def content_key(b,n):
    """Pins editable content across editor awaits, allows display-only eye changes."""
    import hashlib,json
    values=[]
    for item in items(b,n):
        q=copy.deepcopy(item);q.pop('visible',None)
        if q.get('annotation'):q['annotation'].pop('visible',None)
        if q.get('resource'):
            r=q['resource'];q['resource']={k:r.get(k) for k in ('asset','versionId','pose','contextEnabled')};q['resource']['editedAsset']=(r.get('editReference') or {}).get('asset')
        values.append(q)
    return hashlib.sha256(json.dumps(dict(frame=n['frame'],items=values,enabled=gate(n,'enabled'),specialEnabled=gate(n,'specialEnabled')),sort_keys=True).encode()).hexdigest()

def strip_display(a):
    a=copy.deepcopy(a);a.pop('visible',None);return a
