# SPDX-License-Identifier: GPL-3.0-or-later
"""Blender integration: native transforms and transactional world positioning."""
import math
import bpy
import numpy as np
from mathutils import Vector,Matrix
from .math_core import BetterItemError,linked_values,different

GROUP_LINK={'LOCATION':'link_location','ROTATION':'link_rotation','SCALE':'link_scale','DIMENSIONS':'link_dimensions'}


def editable(obj):
    if not obj.is_editable:
        raise BetterItemError('[BI-T001] Object "%s" is not locally editable.' % obj.name)


def _driver_guard(obj,paths,components=None):
    animation=obj.animation_data
    drivers=[curve for curve in animation.drivers if not curve.mute and curve.data_path in paths
             and (components is None or curve.array_index in components.get(curve.data_path,range(4)))] if animation else []
    if drivers:
        labels=['%s[%s]'%(curve.data_path,curve.array_index) for curve in drivers]
        raise BetterItemError('[BI-T002] Object "%s" has an active driver on %s. '
            'Edit or disable that driver before this operation.' % (obj.name,', '.join(labels)))


def _native_matches(actual,expected):
    """Native channels must retain the requested representable float32 value."""
    with np.errstate(over='ignore',under='ignore'):
        stored=np.asarray(expected,dtype=np.float32)
    return all(math.isfinite(a) and math.isfinite(b) and math.isfinite(float(s))
        and (b==0 or s!=0) and a==float(s) for a,b,s in zip(actual,expected,stored))


def edit_scale_component(obj,axis,value):
    editable(obj)
    bpy.context.view_layer.update()
    before=tuple(obj.scale)
    desired=linked_values(before,axis,value,obj.better_item.link_scale)
    for i,locked in enumerate(obj.lock_scale):
        if locked and different(before[i],desired[i]):
            raise BetterItemError('Axis %s is locked on "%s". The linked edit was cancelled.' % ('XYZ'[i],obj.name))
    _driver_guard(obj,{'scale'},{'scale':{i for i in range(3) if before[i]!=desired[i]}})
    try:
        obj.scale=desired
        bpy.context.view_layer.update()
        if not _native_matches(obj.scale,desired):
            raise BetterItemError('Blender did not retain the requested Scale. Check drivers and constraints on "%s".' % obj.name)
    except Exception as exc:
        obj.scale=before
        bpy.context.view_layer.update()
        if isinstance(exc,BetterItemError):raise
        raise BetterItemError('[BI-V002] '+str(exc),severity='ERROR') from exc


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


def _parent_matrix(obj):
    if not obj.parent:return Matrix.Identity(4)
    try:
        if obj.parent_type=='OBJECT':
            return obj.parent.matrix_world @ obj.matrix_parent_inverse
        return obj.matrix_world @ obj.matrix_basis.inverted()
    except ValueError as exc:
        raise BetterItemError('[BI-T005] Cannot resolve %s parenting for "%s": its own matrix_basis is singular. Restore nonzero child Scale before this operation.' % (obj.parent_type,obj.name)) from exc


def _target_location(obj,target):
    """Solve an absolute target, avoiding float32 L + (target - L) cancellation."""
    if not obj.parent:
        current=obj.matrix_world.translation
        return Vector(tuple(float(obj.location[i]) if target[i]==current[i]
            else float(target[i])-float(obj.delta_location[i]) for i in range(3)))
    parent=np.asarray(_parent_matrix(obj),dtype=np.float64)
    try:local=np.linalg.solve(parent[:3,:3],np.asarray(target,dtype=np.float64)-parent[:3,3])
    except np.linalg.LinAlgError as exc:
        raise BetterItemError('[BI-T005] Parent transform of "%s" is singular; restore nonzero parent Scale.' % obj.name) from exc
    return Vector(local-np.asarray(obj.delta_location,dtype=np.float64))


def _world_roundoff(obj,target):
    """Bound the original parent/inverse products before cancellation.

    Bounding only (parent @ inverse) loses large cancelling intermediate terms.
    Blender evaluates these float32 products separately from our float64 solve.
    """
    local=np.abs(np.asarray(obj.location))+np.abs(np.asarray(obj.delta_location))
    if obj.parent and obj.parent_type=='OBJECT':
        parent=np.asarray(obj.parent.matrix_world,dtype=np.float64)
        inverse=np.asarray(obj.matrix_parent_inverse,dtype=np.float64)
        intermediate=np.abs(inverse[:3,:3]) @ local+np.abs(inverse[:3,3])
        terms=np.abs(parent[:3,:3]) @ intermediate+np.abs(parent[:3,3])
        return 8*np.finfo(np.float32).eps*terms
    parent=np.asarray(_parent_matrix(obj),dtype=np.float64)
    terms=np.abs(parent[:3,:3]) @ local+np.abs(parent[:3,3])
    return 4*np.finfo(np.float32).eps*terms


def _position_matches(obj,target,accepted_world_roundoff=None):
    actual=tuple(obj.matrix_world.translation)
    if not all(math.isfinite(v) for v in (*actual,*target)):return False
    budget=_world_roundoff(obj,target)
    if accepted_world_roundoff is not None:budget+=accepted_world_roundoff
    return all(abs(a-t)<=max(3e-7*abs(t),float(budget[i])) for i,(a,t) in enumerate(zip(actual,target)))


def _local_roundoff(obj,target):
    """Float32 world evaluation + inverse solve budget in local coordinates."""
    eps=np.finfo(np.float32).eps
    if not obj.parent:
        return 4*eps*(np.abs(np.asarray(target))+np.abs(np.asarray(obj.delta_location)))
    parent=np.asarray(_parent_matrix(obj),dtype=np.float64)
    try:inverse=np.linalg.inv(parent[:3,:3])
    except np.linalg.LinAlgError as exc:
        raise BetterItemError('[BI-T005] Parent transform of "%s" is singular; restore nonzero parent Scale.'%obj.name) from exc
    terms=np.abs(parent[:3,:3]) @ np.abs(np.asarray(obj.location)+np.asarray(obj.delta_location))+np.abs(parent[:3,3])
    return np.abs(inverse) @ _world_roundoff(obj,target)+4*eps*(np.abs(inverse) @ (terms+np.abs(np.asarray(target))+np.abs(parent[:3,3])))


def apply_world_positions(objects,targets,*,verify=None):
    """Preserve native rotation/scale; either all planned origins move or none."""
    previous={obj:obj.location.copy() for obj in objects}
    changed=[]
    accepted_roundoff={}
    try:
        for obj in sorted(objects,key=lambda item:(_depth(item),item.name)):
            bpy.context.view_layer.update()
            if tuple(targets[obj.name])==tuple(obj.matrix_world.translation):
                continue
            editable(obj)
            constraints=[constraint.name for constraint in obj.constraints if not constraint.mute and constraint.influence!=0]
            if constraints:
                raise BetterItemError('[BI-T004] Object "%s" has active constraints: %s. '
                    'Disable them before aligning or distributing.' % (obj.name,', '.join(constraints)))
            _driver_guard(obj,{'location','delta_location'})
            desired=_target_location(obj,targets[obj.name])
            roundoff=_local_roundoff(obj,targets[obj.name])
            locked_roundoff=np.zeros(3,dtype=np.float64)
            for axis,locked in enumerate(obj.lock_location):
                if locked:
                    if abs(desired[axis]-obj.location[axis])>float(roundoff[axis]):
                        raise BetterItemError('[BI-T003] Local %s is locked on "%s". Unlock it before moving; no objects were repositioned.' % ('XYZ'[axis],obj.name))
                    if desired[axis]!=obj.location[axis]:locked_roundoff[axis]=float(roundoff[axis])
                    desired[axis]=obj.location[axis]
            if np.any(locked_roundoff):
                accepted_roundoff[obj]=np.abs(np.asarray(_parent_matrix(obj),dtype=np.float64)[:3,:3]) @ locked_roundoff
            if not all(math.isfinite(component) for component in desired):
                raise BetterItemError('[BI-T007] Position of "%s" exceeds the numeric range. Reduce coordinate magnitudes.' % obj.name)
            changed.append(obj)
            obj.location=desired
        bpy.context.view_layer.update()
        for obj in objects:
            if not _position_matches(obj,targets[obj.name],accepted_roundoff.get(obj)):
                error=max(abs(a-t) for a,t in zip(obj.matrix_world.translation,targets[obj.name]))
                raise BetterItemError('[BI-T006] Position verification failed for "%s" (residual %.9g Blender units). '
                    'The evaluated position exceeds the float32 rounding budget for its parent/inverse transform. Check evaluated overrides and coordinate precision. No objects were repositioned.' % (obj.name,error))
        if verify is not None:verify(objects)
    except Exception as exc:
        for obj in changed:
            obj.location=previous[obj]
        bpy.context.view_layer.update()
        if isinstance(exc,BetterItemError):
            raise
        raise BetterItemError('[BI-V002] '+str(exc),severity='ERROR') from exc
    return len(changed)
