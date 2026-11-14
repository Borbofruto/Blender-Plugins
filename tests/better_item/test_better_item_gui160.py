"""Real sidebar/render/invoke checks in a separate factory-startup Blender UI."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,numpy as np
from mathutils import Matrix,Euler
import better_item as addon
addon.frames.BETTERITEM_PT_frames.bl_options={'DEFAULT_CLOSED'}
addon.BETTERITEM_PT_transform.bl_options={'DEFAULT_CLOSED'}
addon.register()
from better_item import arrange,transform_view as v,native_refs,orientation
ctx=bpy.context;root=Path(__file__).parent;phase=0;result={'passed':False,'phases':[]}
ctx.preferences.view.show_splash=False
key=ctx.object;key.name='Key'
bpy.ops.mesh.primitive_cube_add(location=(0,5,0));b=ctx.object;b.name='Part B';b.rotation_euler.z=.3
bpy.ops.mesh.primitive_cube_add(location=(0,10,0));c=ctx.object;c.name='Part C';c.rotation_euler.z=-.2
bpy.ops.object.select_all(action='DESELECT')
for obj in (key,b,c):obj.select_set(True)
ctx.view_layer.objects.active=key
s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key;s.axes=(False,True,False)
s.distribution_mode='GEOMETRY';s.spacing=0
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True
area.spaces.active.region_3d.view_distance=12
def shot(name):bpy.ops.screen.screenshot(filepath=str(root/name))
def run():
    global phase
    try:
        with native_refs.view_context(ctx):
            if phase==0:
                ui=next(r for r in area.regions if r.type=='UI');ui.active_panel_category='Better Item'
                assert bpy.ops.better_item.distribute('INVOKE_DEFAULT')=={'FINISHED'}
                edges=[]
                for obj in (key,b,c):
                    lo,hi=v.projected_bounds(obj,Matrix.Identity(3));edges.append((obj.matrix_world.translation.y+lo[1],obj.matrix_world.translation.y+hi[1]))
                assert abs(edges[1][0]-edges[0][1])<1e-5 and abs(edges[2][0]-edges[1][1])<1e-5,edges
                assert not s.show_solver
            elif phase==1:
                shot('ui160-geometry.png')
                s.arrange_origin_object=None
            elif phase==2:
                shot('ui160-pending.png')
                s.alignment_type='ORIENTATION';s.arrange_orientation='REFERENCE';s.arrange_object=key
                s.orientation_action='SET';s.orientation_axes=(True,False,False);s.orientation_angles=(.3,0,0)
                positions={obj.name:tuple(obj.matrix_world.translation) for obj in (key,b,c)}
                expected={obj.name:list(orientation.rotation(obj).to_euler('XYZ')) for obj in (b,c)}
                assert bpy.ops.better_item.align_orientation('INVOKE_DEFAULT')=={'FINISHED'}
                for obj in (b,c):
                    expected[obj.name][0]=.3
                    assert np.allclose(orientation.rotation(obj),Euler(expected[obj.name]).to_matrix(),atol=2e-5)
                    assert np.allclose(obj.matrix_world.translation,positions[obj.name])
                assert s.arrange_origin_object is None
            elif phase==3:
                shot('ui160-orientation.png')
                s.orientation_angles=(.4,0,0)
                assert bpy.ops.better_item.align_orientation('INVOKE_DEFAULT')=={'FINISHED'}
                for obj in (b,c):assert abs(orientation.rotation(obj).to_euler('XYZ').x-.4)<1e-5
                s.arrange_origin_object=key;s.show_solver=True
            elif phase==4:
                shot('ui160-solver.png');s.show_solver=False
                c.location=b.location;ctx.view_layer.update()
                assert bpy.ops.better_item.distribute('INVOKE_DEFAULT')=={'CANCELLED'}
                assert arrange.error(ctx.scene).severity=='WARNING'
            elif phase==5:
                shot('ui160-warning.png');s.show_diagnostic_details=True
            elif phase==6:
                shot('ui160-details.png');arrange.clear_error();s.show_diagnostic_details=False
                b.location=(0,5,0);c.location=(0,10,0);s.spacing=-.1
                assert bpy.ops.better_item.distribute('INVOKE_DEFAULT')=={'FINISHED'}
                edges=[]
                for obj in (key,b,c):
                    lo,hi=v.projected_bounds(obj,Matrix.Identity(3));edges.append((obj.matrix_world.translation.y+lo[1],obj.matrix_world.translation.y+hi[1]))
                assert abs(edges[0][0]-edges[1][1]-.1)<1e-5 and abs(edges[1][0]-edges[2][1]-.1)<1e-5,edges
            else:
                shot('ui160-negative-spacing.png');result['passed']=True;result['phases'].append(phase)
                result['checks']=['actual Geometry INVOKE uses scene Y/zero spacing/positive packing','negative spacing reverses packing without a Direction control','sidebar Pending source is neutral','orientation works with Location pending','partial Set Rotation preserves positions','repeated INVOKE captures new panel angles','solver collapsed/expanded','domain rejection WARNING','support code in optional Details']
                (root/'ui160.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                print('160 REAL UI PASSED',flush=True);bpy.ops.wm.quit_blender();return None
        result['phases'].append(phase);phase+=1;return 1.
    except Exception:
        traceback.print_exc();result['traceback']=traceback.format_exc();(root/'ui160.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
