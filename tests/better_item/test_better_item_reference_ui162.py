"""Shared reference UI hierarchy: category icons and indented dependent fields."""
import sys,json
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import references,frames
ctx=bpy.context;obj=ctx.object
frame=frames.create(ctx,'Source Frame',Vector(),Matrix.Identity(3))
source=bpy.data.objects.new('Source Object',None);ctx.scene.collection.objects.link(source)
class Layout:
    def __init__(self,events=None,path=()):self.events=[] if events is None else events;self.path=path
    def split(self,**kw):
        self.events.append(('split',self.path,kw));return Layout(self.events,self.path+(kw.get('factor'),))
    def row(self,**kw):return Layout(self.events,self.path+('row',))
    def box(self):return Layout(self.events,self.path+('box',))
    def label(self,**kw):self.events.append(('label',self.path,kw))
    def prop(self,owner,name,**kw):self.events.append(('prop',self.path,dict(kw,name=name)))
    def operator(self,*args,**kw):self.events.append(('operator',self.path,kw));return SimpleNamespace()
count=0
for arrangement in (False,True):
    settings=ctx.scene.better_item if arrangement else obj.better_item
    fields=references._FIELDS[arrangement]
    setattr(settings,fields['mode'],'INDIVIDUAL')
    for kind,modes in (('axes',('GLOBAL','REFERENCE','SAVED','NATIVE')),('origin',('GLOBAL','OBJECT','FRAME'))):
        for mode in modes:
            stored='SAVED' if arrangement and kind=='origin' and mode=='FRAME' else mode
            setattr(settings,fields['axes' if kind=='axes' else 'origin'],stored)
            layout=Layout();before={name:getattr(settings,name) for name in fields.values()}
            references.draw_component(layout,settings,kind,arrangement)
            assert {name:getattr(settings,name) for name in fields.values()}==before
            labels=[e[2] for e in layout.events if e[0]=='label']
            assert labels[0]==dict(text='Orientation:' if kind=='axes' else 'Location:',icon='ORIENTATION_GLOBAL' if kind=='axes' else 'OBJECT_ORIGIN')
            assert sum(bool(e.get('icon')) for e in labels)==1
            branches=[e for e in layout.events if e[0]=='split' and e[2].get('factor')==.32]
            assert len(branches)==(0 if mode=='GLOBAL' else 1)
            if branches:
                assert any(e.get('text')=='└' and 'icon' not in e for e in labels)
                props=[e for e in layout.events if e[0]=='prop']
                assert props[1][2]['text']=='' and 'icon' not in props[1][2]
            count+=1
# Frame sources use exactly the same category/branch helper.
for kind,modes in (('axes',('MANUAL','OBJECT','FRAME','NATIVE')),('origin',('MANUAL','OBJECT','FRAME'))):
    for mode in modes:
        setattr(frame,'rotation_mode' if kind=='axes' else 'position_mode',mode)
        if mode=='NATIVE':frame.native_source='Custom Test'
        layout=Layout();references.draw_component(layout,frame,kind,frame=True)
        labels=[e[2] for e in layout.events if e[0]=='label']
        assert labels[0]['icon']==('ORIENTATION_GLOBAL' if kind=='axes' else 'OBJECT_ORIGIN')
        assert sum(bool(e.get('icon')) for e in labels)==1
        assert sum(e.get('text')=='└' for e in labels)==(0 if mode=='MANUAL' else 1)
        count+=1
result={'component_states':count,'consumers':['Transform','Align and Distribute','Reference Frames'],'category_icons_only':True,'branch_for_secondary_object_frame_name':True,'draw_does_not_mutate_sources':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('162 REFERENCE UI PASSED',json.dumps(result))
