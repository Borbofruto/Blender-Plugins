import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector
addon_utils.enable('better_item',default_set=True)
from better_item import native_refs,frames
ctx=bpy.context
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.object.empty_add();parent=ctx.object
parent.rotation_euler=(.15,.25,.35)
bpy.ops.mesh.primitive_cube_add();obj=ctx.object
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);ctx.view_layer.objects.active=obj
checks=0
with native_refs.view_context(ctx):
    for use_parent in (False,True):
        obj.parent=parent if use_parent else None
        for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX','QUATERNION','AXIS_ANGLE'):
            obj.rotation_mode=order
            if order=='QUATERNION':obj.rotation_quaternion=(.9,.1,.2,.3)
            elif order=='AXIS_ANGLE':obj.rotation_axis_angle=(.4,.2,.4,.8)
            else:obj.rotation_euler=(.2,.3,.4)
            ctx.view_layer.update()
            basis=native_refs.orientation(ctx,'GIMBAL',obj)
            for axis in range(3):
                start=obj.matrix_world.translation.copy()
                values=[0,0,0];values[axis]=1
                bpy.ops.transform.translate(value=values,orient_type='GIMBAL',constraint_axis=tuple(i==axis for i in range(3)))
                ctx.view_layer.update()
                actual=obj.matrix_world.translation-start
                assert (actual-basis.col[axis]).length<2e-5,(use_parent,order,axis,actual,basis.col[axis])
                checks+=1
    # Normal follows the actual edit selection, captured by the native operator.
    obj.parent=None;obj.rotation_mode='XYZ';obj.rotation_euler=(.1,.2,.3)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    import bmesh
    mesh=bmesh.from_edit_mesh(obj.data)
    mesh.faces.ensure_lookup_table()
    mesh.faces[0].select_set(True)
    bmesh.update_edit_mesh(obj.data)
    f=frames.create(ctx,'Edit Normal',Vector(),native_refs.Matrix.Identity(3))
    f.rotation_mode='NATIVE';f.native_source='NORMAL'
    native_refs.sync()
    matrix=frames.frame_axes(f)
    assert abs(matrix.determinant())>.99
    bpy.ops.object.mode_set(mode='OBJECT')
print('NATIVE AXES PASSED: %d actual Gimbal transforms, all storage orders, parent rotation, edit-mode Normal'%checks)

