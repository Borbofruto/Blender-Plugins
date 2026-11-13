"""Blender integration: native transforms and transactional world positioning."""
import math
import bpy
from mathutils import Vector
from .math_core import BetterItemError,linked_values,different

GROUP_LINK={'LOCATION':'link_location','ROTATION':'link_rotation','SCALE':'link_scale','DIMENSIONS':'link_dimensions'}


def editable(obj):
    if not obj.is_editable:
        raise BetterItemError('Object "%s" is not locally editable.' % obj.name)


def _driver_guard(obj,paths):
    animation=obj.animation_data
    if animation and any(not curve.mute and curve.data_path in paths for curve in animation.drivers):
        raise BetterItemError('Object "%s" has a driver on these fields. Edit or disable the driver.' % obj.name)


def _matches(actual,expected):
    return all(math.isclose(a,b,rel_tol=3e-7,abs_tol=1e-8) for a,b in zip(actual,expected))


def edit_scale_component(obj,axis,value):
    editable(obj)
    bpy.context.view_layer.update()
    before=tuple(obj.scale)
    desired=linked_values(before,axis,value,obj.better_item.link_scale)
    for i,locked in enumerate(obj.lock_scale):
        if locked and different(before[i],desired[i]):
            raise BetterItemError('Axis %s is locked on "%s". The linked edit was cancelled.' % ('XYZ'[i],obj.name))
    _driver_guard(obj,{'scale'})
    try:
        obj.scale=desired
        bpy.context.view_layer.update()
        if not _matches(obj.scale,desired):
            raise BetterItemError('Blender did not retain the requested Scale. Check drivers and constraints on "%s".' % obj.name)
    except Exception as exc:
        obj.scale=before
        bpy.context.view_layer.update()
        if isinstance(exc,BetterItemError):raise
        raise BetterItemError(str(exc)) from exc


def selection_origins(context):
    bpy.context.view_layer.update()
    objects=list(context.selected_objects)
    return objects,{obj.name:tuple(obj.matrix_world.translation) for obj in objects}


def _depth(obj):
    depth=0
    while obj.parent:
        obj=obj.parent
        depth+=1
    return depth


def _local_delta(obj,world_delta):
    if not obj.parent:
        return world_delta
    try:
        if obj.parent_type=='OBJECT':
            parent=obj.parent.matrix_world @ obj.matrix_parent_inverse
        else:
            parent=obj.matrix_world @ obj.matrix_basis.inverted()
        return parent.to_3x3().inverted() @ world_delta
    except ValueError as exc:
        raise BetterItemError('The parent transform of "%s" is singular; its position cannot be resolved.' % obj.name) from exc


def apply_world_positions(objects,targets):
    """Preserve native rotation/scale; either all planned origins move or none."""
    previous={obj:obj.location.copy() for obj in objects}
    changed=[]
    try:
        for obj in sorted(objects,key=lambda item:(_depth(item),item.name)):
            bpy.context.view_layer.update()
            delta=Vector(targets[obj.name])-obj.matrix_world.translation
            if all(not different(component,0) for component in delta):
                continue
            editable(obj)
            if any(not constraint.mute and constraint.influence!=0 for constraint in obj.constraints):
                raise BetterItemError('Object "%s" has active constraints. Disable them before aligning or distributing.' % obj.name)
            _driver_guard(obj,{'location','delta_location'})
            local_delta=_local_delta(obj,delta)
            for axis,locked in enumerate(obj.lock_location):
                if locked and different(local_delta[axis],0):
                    raise BetterItemError('Local axis %s is locked on "%s". No objects were repositioned.' % ('XYZ'[axis],obj.name))
            desired=obj.location+local_delta
            if not all(math.isfinite(component) for component in desired):
                raise BetterItemError('The transform of "%s" exceeded the numeric range.' % obj.name)
            changed.append(obj)
            obj.location=desired
        bpy.context.view_layer.update()
        for obj in objects:
            if not _matches(obj.matrix_world.translation,targets[obj.name]):
                raise BetterItemError('Could not position "%s" at the planned coordinate. Check parenting and drivers.' % obj.name)
    except Exception as exc:
        for obj in changed:
            obj.location=previous[obj]
        bpy.context.view_layer.update()
        if isinstance(exc,BetterItemError):
            raise
        raise BetterItemError(str(exc)) from exc
    return len(changed)
