import sys,numpy as np
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
import better_item as addon
from better_item import frames,native_refs,transform_view as view
from better_item.math_core import BetterItemError
ctx=bpy.context;o=ctx.object

def near(a,b):assert np.allclose(a,b,rtol=3e-5,atol=2e-6),(a,b)
def brute(obj,axes):
 graph=ctx.evaluated_depsgraph_get();evaluated=obj.evaluated_get(graph);mesh=evaluated.to_mesh()
 try:
  world=np.asarray([tuple(obj.matrix_world@v.co) for v in mesh.vertices],dtype=np.float64)
 finally:evaluated.to_mesh_clear()
 directions=np.asarray(axes,dtype=np.float64);directions=directions/np.linalg.norm(directions,axis=0)
 return np.ptp(world@directions,axis=0)
# A real Gimbal under nonuniform ancestor scaling has nonunit columns.
g=bpy.data.objects.new('Scaled ancestor',None);ctx.scene.collection.objects.link(g);g.scale=(2,1,.5)
p=bpy.data.objects.new('Rotated parent',None);ctx.scene.collection.objects.link(p);p.parent=g;p.rotation_euler=(.4,.8,.2)
o.parent=p;o.rotation_euler=(.3,.5,.2);ctx.view_layer.update()
axes=native_refs._gimbal(o);assert min(axes.col[i].length for i in range(3))<.7
raw_before=tuple(v for row in axes for v in row)
measured=view.dimensions(o,axes);expected=brute(o,axes);near(measured,expected)
assert abs(measured[0]-5.000715)<1e-4,measured
# Rescaling or reversing individual directions cannot alter physical width.
scaled=axes@Matrix.Diagonal((4,.2,-3));near(view.dimensions(o,scaled),expected)
assert raw_before==tuple(v for row in native_refs._gimbal(o) for v in row)
f=frames.create(ctx,'Gimbal basis',Vector(),axes);uid=f.uid
s=o.better_item;s.reference_mode='FRAME';s.reference_frame=uid
location_before=frames.relative_values(ctx,o,'POSITION');verts=[tuple(v.co) for v in o.data.vertices]
desired=tuple(v*k for v,k in zip(measured,(1.2,.8,1.1)))
view.set_dimensions(ctx,o,desired);near(view.values(ctx,o,'DIMENSIONS'),desired)
assert verts==[tuple(v.co) for v in o.data.vertices]
near(frames.relative_values(ctx,o,'POSITION'),location_before)
near(frames.frame_axes(frames.find(ctx.scene,uid)),axes)
view.set_dimensions(ctx,o,measured);near(view.values(ctx,o,'DIMENSIONS'),measured)
# Bad directions fail with an explicit domain error.
for invalid in (Matrix(((0,0,0),(0,1,0),(0,0,1))),Matrix(((float('nan'),0,0),(0,1,0),(0,0,1)))):
 try:view.dimensions(o,invalid)
 except BetterItemError:pass
 else:raise AssertionError('Invalid dimension direction must reject')
# Per-group UI validation must not erase readable channels.
s.reference_mode='INDIVIDUAL';s.orientation='GLOBAL';s.pivot_mode='GLOBAL'
class Layout:
 def __init__(self):self.props=[];self.labels=[]
 def row(self,**kwargs):return self
 def column(self,**kwargs):return self
 def label(self,**kwargs):self.labels.append(kwargs.get('text',''))
 def prop(self,owner,field,**kwargs):self.props.append(field)
 def operator(self,*args,**kwargs):return SimpleNamespace()
def group(name,prefix):
 layout=Layout();addon._linked_rows(layout,o,name,name.title(),prefix);return layout
s.orientation='REFERENCE';s.orientation_object=None
for name,prefix in [('LOCATION','location'),('ROTATION','rotation'),('DIMENSIONS','dimensions')]:
 layout=group(name,prefix);assert 'Unavailable' in layout.labels and not any(p.startswith(prefix+'_') for p in layout.props),(name,layout.props)
assert 'scale' in group('SCALE','scale').props
# Missing Location alone leaves Rotation and Dimensions readable/editable.
s.orientation='GLOBAL';s.pivot_mode='OBJECT';s.origin_object=None
assert 'Unavailable' in group('LOCATION','location').labels
assert 'rotation_x' in group('ROTATION','rotation').props
assert 'dimensions_x' in group('DIMENSIONS','dimensions').props
s.pivot_mode='GLOBAL';s.reference_mode='FRAME';s.reference_frame='NONE';s.transform_space='DEFAULT'
assert 'location_x' in group('LOCATION','location').props
assert 'rotation_x' in group('ROTATION','rotation').props
# Restoring the reference restores the fields, including a valid zero Location.
s.transform_space='REFERENCE';s.reference_mode='INDIVIDUAL'
assert 'location_x' in group('LOCATION','location').props
# Repeated registration doesn't duplicate the measurement callback.
addon.register();addon.register();assert bpy.app.handlers.frame_change_post.count(view.clear_cache)==1
assert not hasattr(s,'animation')
print('154 DIRECTIONS/UI PASSED: nonunit inherited Gimbal physical widths, rescaled/reversed axes, dimension edits and reversal, base mesh/coordinate basis preserved, invalid directions, independently unavailable groups, Default independence and registration')
