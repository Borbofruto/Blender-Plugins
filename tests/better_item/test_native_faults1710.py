"""Publish/remove fault boundaries preserve intent, recovery and healthy Frames."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
import bpy
import better_item as addon
from mathutils import Vector,Matrix
from better_item import native_refs as nr,frames,diagnostics
from better_item.math_core import BetterItemError
addon.register()
if bpy.app.timers.is_registered(nr.sync):bpy.app.timers.unregister(nr.sync)
nr.sync()
ctx=bpy.context;checks=[]
for native,field in [('location','location_x'),('rotation_euler','rotation_x'),('scale','scale_x'),('dimensions','dimensions_x')]:
    assert ctx.object.bl_rna.properties[native].precision==ctx.object.better_item.bl_rna.properties[field].precision
assert callable(diagnostics.Diagnostic(BetterItemError('[BI-F006] Controlled fault')).title)
checks.append('Transform precision matches native groups and Diagnostic preserves str.title')
def create(name):
    source=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(source)
    frame=frames.create(ctx,name,Vector(),Matrix.Identity(3))
    frame.rotation_mode='OBJECT';frame.rotation_source=source
    nr.publish(ctx,frame)
    return source,frame
source,bad=create('Faulted export');other,good=create('Healthy export')
original_publish=nr.publish;original_remove=nr.remove_native
def matches(frame):
    actual=nr.named(ctx.scene,frame.native_name).matrix
    expected=frames.frame_axes(frame,ctx)
    return max(abs(actual[i][j]-expected[i][j]) for i in range(3) for j in range(3))<2e-6
for operation in ('publish','remove'):
    for error_type in (RuntimeError,TypeError):
        source.rotation_euler.z+=.2;other.rotation_euler.z+=.3;ctx.view_layer.update()
        if operation=='remove':bad.rotation_source=None
        def faulty(context,frame,*args,**kwargs):
            if frame.uid==bad.uid:raise error_type('Controlled '+operation+' failure')
            return (original_publish if operation=='publish' else original_remove)(context,frame,*args,**kwargs)
        if operation=='publish':nr.publish=faulty
        else:nr.remove_native=faulty
        nr.sync()
        issue=nr.sync_error(ctx.scene,bad)
        assert issue and 'BI-F006' in str(issue)
        assert bad.native_enabled and not bad.native_suspended
        assert matches(good),'healthy export starved by another frame'
        assert diagnostics.Diagnostic(issue).heading=='Orientation sync paused'
        nr.publish=original_publish;nr.remove_native=original_remove
        nr._sync_errors[(ctx.scene.as_pointer(),bad.uid)]['retry_at']=0
        nr.sync()
        assert nr.sync_error(ctx.scene,bad) is None
        if operation=='remove':
            assert bad.native_suspended and bad.native_enabled
            bad.rotation_source=source;nr.sync()
        assert matches(bad) and not bad.native_suspended
        checks.append(operation+' '+error_type.__name__+' isolation and recovery')

class InvalidWindow:
    @property
    def scene(self):raise ReferenceError('Controlled invalid window')
real_bpy=nr.bpy;original_migrate=frames.migrate
def migration_fault():raise RuntimeError('Controlled migration fault')
try:
    nr.bpy=SimpleNamespace(types=bpy.types,context=SimpleNamespace(window_manager=SimpleNamespace(windows=[InvalidWindow()])))
    frames.migrate=migration_fault;nr._needs_migration=True
    assert nr.sync()==.2
    assert not nr._syncing and nr._sync_errors[(0,'')]
finally:nr.bpy=real_bpy;frames.migrate=original_migrate
nr._sync_errors[(0,'')]['retry_at']=0
assert nr.sync()==.2 and not nr._sync_errors
checks.append('invalid window does not escape observer failure or prevent recovery')
result={'passed':True,'blender':bpy.app.version_string,'checks':checks}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('NATIVE FAULTS 1710',json.dumps(result))
