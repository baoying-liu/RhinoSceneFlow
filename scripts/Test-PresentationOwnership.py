"""Guard native caption ownership against reintroducing a second text writer."""
import pathlib,re
root=pathlib.Path(__file__).resolve().parents[1]/'src/RhinoSceneFlow.Plugin'
errors=[]
for p in root.glob('*.cs'):
 if p.name=='UiPresentation.cs':continue
 code=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|@"(?:""|[^"])*"|\$?"(?:\\.|[^"\\])*"','',p.read_text(encoding='utf-8-sig'))
 for m in re.finditer(r'\bnew\s+(Label|Button|CheckBox|ListItem|ButtonMenuItem|GroupBox|Expander|GridColumn|TextBox)\b',code):errors.append((p.name,m.group()))
appearance=(root/'WorkspaceAppearance.cs').read_text(encoding='utf-8-sig')
assert not re.search(r'\.(Text|HeaderText|PlaceholderText)\s*=',appearance),'Theme decoration must not write captions'
workspace=(root/'WorkspacePanels.cs').read_text(encoding='utf-8-sig')
method=workspace.split('internal void RefreshDocument()',1)[1].split('public object State()',1)[0]
assert 'Apply(this)' not in method.split('rebinding=true;',1)[0],'No periodic presentation pass'
assert not errors,errors
print('PASS: bound caption constructors, theme-only decoration and no idle translation writer.')
