import sys, json, hashlib, os
from pathlib import Path
sys.dont_write_bytecode = True
root = Path(os.environ.get('BETTER_ITEM_REPO', str(Path(__file__).resolve().parents[4])))
assert (root/'src/better_item').is_dir(), 'Set BETTER_ITEM_REPO to a checkout containing src/better_item' 
sys.path.insert(0, str(root/'src'))
import bpy
import better_item as addon
captured = []
original = addon.BETTERITEM_OT_distribute.execute
def execute(self, context):
    captured.append(dict(method=self.method, basis=self.distribution_mode,
                         offset=self.offset_placement, endpoint=self.endpoint_placement))
    return original(self, context)
addon.BETTERITEM_OT_distribute.execute = execute
addon.register()
results = []
def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    s = bpy.context.scene.better_item
    s.arrange_reference_mode='INDIVIDUAL'
    s.arrange_origin='GLOBAL'; s.arrange_orientation='GLOBAL'
    s.distribution_start_override=False
    s.distribution_end.mode='MANUAL'; s.distribution_end.position=(30,0,0)
    objs=[]
    for i in range(3):
        bpy.ops.mesh.primitive_cube_add(location=(3+5*i,2+i,0))
        obj=bpy.context.object
        for v in obj.data.vertices: v.co.x += i+1
        objs.append(obj)
    for obj in objs:obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.context.view_layer.update()
    return objs
for basis in ('ORIGINS','BOUNDS_CENTER','SURFACE','VOLUME','GEOMETRY'):
    for order in ('method_first','basis_first'):
        objs=reset()
        kwargs=dict(method='ENDPOINT',distribution_mode=basis) if order=='method_first' else dict(distribution_mode=basis,method='ENDPOINT')
        try:
            status=sorted(bpy.ops.better_item.distribute(**kwargs))
        except Exception as exc:status=str(exc)
        results.append(dict(requested=basis,order=order,status=status,effective=captured[-1].copy(),positions=[list(o.location) for o in objs]))
objs=reset()
status=sorted(bpy.ops.better_item.distribute(method='ENDPOINT',endpoint_placement=4))
results.append(dict(requested='explicit hidden endpoint=4',status=status,effective=captured[-1].copy(),positions=[list(o.location) for o in objs]))
out=dict(blender=bpy.app.version_string,archive_sha256=hashlib.sha256((root/'addons/better_item.zip').read_bytes()).hexdigest(),results=results)
Path(__file__).with_name('operator-'+bpy.app.version_string+'.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
addon.unregister()
