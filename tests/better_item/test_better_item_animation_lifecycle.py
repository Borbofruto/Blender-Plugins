import sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Matrix
addon_utils.enable('better_item',default_set=True)
from better_item import animation,frames
ctx=bpy.context
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def near(a,b):assert np.allclose(a,b,rtol=0,atol=3e-5),(a,b)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
a=empty('Source A');a.location=(10,0,0)
b=empty('Source B');b.location=(30,0,0)
obj=empty('Actor');obj.location=(11,0,0);ctx.view_layer.objects.active=obj;obj.select_set(True);ctx.view_layer.update()
f=frames.create(ctx,'Public frame',a.matrix_world.translation,Matrix.Identity(3),a);public_uid=f.uid
obj.better_item.reference_mode='FRAME';obj.better_item.reference_frame=public_uid
animation.start(ctx,obj);params=obj.better_item.animation
near(obj.matrix_world.translation,(11,0,0))
# Retargeting must replace bookkeeping relations, not retain a stale cycle.
a.parent=obj
f=frames.find(ctx.scene,public_uid);f.position_source=f.rotation_source=b
animation.sync();assert not params.error,params.error
near(obj.matrix_world.translation,(31,0,0))
bpy.data.objects.remove(b,do_unlink=True);ctx.view_layer.update();animation.sync()
assert not params.error,params.error
f=frames.find(ctx.scene,public_uid)
assert f.position_mode==f.rotation_mode=='OBJECT' # Shared user frame was not rewritten.
private=frames.find(ctx.scene,params.binding_uid)
assert private.position_mode==private.rotation_mode=='MANUAL'
near(obj.matrix_world.translation,(31,0,0))
# Removing the owned frame uses its cache without recreating scene entries.
settings=ctx.scene.better_item
settings.active_frame=next(i for i,f in enumerate(settings.frames) if f.uid==params.binding_uid)
bpy.ops.better_item.frame(action='REMOVE');count=len(settings.frames)
animation.sync();params.location=(2,0,0)
assert not params.error,params.error
assert len(settings.frames)==count
near(obj.matrix_world.translation,(32,0,0))
animation.pause(obj);assert animation._dependency_curve(obj) is None
# Cursor values are live even at an unchanged frame (Blender does not allow
# native cursor keyframes, so these are actual manual scene edits).
cursor_actor=empty('Cursor Actor');cursor_actor.location=(6,0,0)
ctx.scene.cursor.location=(5,0,0);ctx.view_layer.objects.active=cursor_actor;ctx.view_layer.update()
cursor_actor.better_item.pivot_mode='CURSOR';cursor_actor.better_item.orientation='CURSOR'
animation.start(ctx,cursor_actor)
ctx.scene.cursor.location=(10,0,0)
ctx.scene.frame_set(6)
assert not cursor_actor.better_item.animation.error,cursor_actor.better_item.animation.error
near(cursor_actor.matrix_world.translation,(11,0,0))
ctx.scene.cursor.location=(20,0,0);animation.sync()
near(cursor_actor.matrix_world.translation,(21,0,0))
# An explicit object/parent feedback loop is reported without leaving our
# bookkeeping drivers poisoning the native graph, and recovers when fixed.
loop=empty('Feedback source');loop.location=(5,0,0);loop.parent=cursor_actor
binding=frames.find(ctx.scene,cursor_actor.better_item.animation.binding_uid)
binding.position_mode='OBJECT';binding.position_source=loop
animation.sync();assert 'BI-AN003' in cursor_actor.better_item.animation.error
assert animation._dependency_curve(cursor_actor) is None
loop.parent=None
ctx.scene.frame_set(6);assert not cursor_actor.better_item.animation.error
near(cursor_actor.matrix_world.translation,(6,0,0))
print('ANIMATION LIFECYCLE PASSED: retargeting, shared-frame isolation, deleted owned frame, live cursor, dependency cleanup, cycle diagnosis and recovery')
