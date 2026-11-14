# SPDX-License-Identifier: GPL-3.0-or-later
"""Plan and verify physical gaps between evaluated projected intervals."""
import math
import numpy as np
from mathutils import Matrix
from . import arrange,transform_view,engine
from .math_core import BetterItemError,ReferencePending


def _bounds(obj,basis):
    if not transform_view.has_surface_geometry(obj):
        raise BetterItemError('[BI-G001] "%s" has no supported surface geometry. Use Origins distribution for this object.'%obj.name)
    try:low,high=transform_view.projected_bounds(obj,Matrix(basis))
    except BetterItemError as exc:
        exc.subject=obj.name
        raise
    return np.asarray(low),np.asarray(high)


def plan(context,objects,origins,axes,reference='AUTO',*,spacing=0.,minimum_mm=.00001):
    if context.mode!='OBJECT':raise ReferencePending('[BI-A003] Switch to Object Mode to distribute whole objects.')
    if not any(axes):raise ReferencePending('[BI-A001] Select an axis for distribution.')
    if not math.isfinite(spacing):raise BetterItemError('[BI-D001] Enter a finite Spacing.')
    direction=-1 if spacing<0 else 1
    gap=abs(spacing)
    if not math.isfinite(minimum_mm) or minimum_mm<=0:raise BetterItemError('[BI-D001] Solver minimum separation must be greater than zero.')
    reference=arrange.operation_reference(context) if reference=='AUTO' else reference
    if reference not in {'SELECTION','KEY','REFERENCE'}:raise BetterItemError('[BI-A004] Choose a valid Location reference.')
    if not objects:raise ReferencePending('[BI-A003] Select objects to distribute.')
    basis,origin,source=arrange.reference_frame(context,reference)
    directions=basis/np.linalg.norm(basis,axis=0)
    coordinates={name:directions.T @ (np.asarray(value)-origin) for name,value in origins.items()}
    key=context.active_object if reference=='KEY' else source
    if reference=='KEY' and (key is None or key.name not in origins):raise ReferencePending('[BI-A004] Select the active key object with the targets.')
    fixed=key.name if key is not None and key.name in origins else None
    moving=[obj for obj in objects if obj.name!=fixed]
    if not moving:raise ReferencePending('[BI-A003] Select at least one object other than the reference.')
    if reference=='SELECTION' and len(moving)<2:raise ReferencePending('[BI-A003] Select at least two objects for selection-bound distribution.')
    mm_per_unit=arrange._mm_per_unit(context.scene)
    conflicts=arrange._coordinate_conflicts(coordinates,axes,minimum_mm/mm_per_unit)
    if conflicts:
        raise BetterItemError('[BI-D002] The starting positions do not define a unique order. Separate these origins by at least %s mm on the selected axes, then retry:\n%s'%
            (arrange._mm(minimum_mm),'\n'.join(conflicts)))
    local={obj.name:_bounds(obj,basis) for obj in moving}
    linear={obj.name:np.asarray(obj.matrix_world.to_3x3(),dtype=np.float64).copy() for obj in moving}
    key_position=np.asarray(key.matrix_world.translation,dtype=np.float64).copy() if key else None
    key_linear=np.asarray(key.matrix_world.to_3x3(),dtype=np.float64).copy() if key else None
    key_bounds=_bounds(key,basis) if key and transform_view.has_surface_geometry(key) else (np.zeros(3),np.zeros(3))
    key_coordinate=directions.T @ (key_position-origin) if key is not None else np.zeros(3)
    planned={name:value.copy() for name,value in coordinates.items()}
    chains={}
    for axis,enabled in enumerate(axes):
        if not enabled:continue
        if reference=='SELECTION':
            order=sorted((obj.name for obj in moving),key=lambda name:(direction*coordinates[name][axis],name))
            boundary=(min(coordinates[name][axis]+local[name][0][axis] for name in order) if direction>0 else
                      max(coordinates[name][axis]+local[name][1][axis] for name in order))
        else:
            def priority(name):
                delta=coordinates[name][axis]-key_coordinate[axis]
                return (0 if delta*direction<0 else 1,abs(delta),name)
            order=sorted((obj.name for obj in moving),key=priority)
            boundary=key_coordinate[axis]+key_bounds[1 if direction>0 else 0][axis]+direction*gap
        for name in order:
            low,high=local[name]
            planned[name][axis]=boundary-(low[axis] if direction>0 else high[axis])
            boundary=planned[name][axis]+(high[axis] if direction>0 else low[axis])+direction*gap
        chains[axis]=order
    on_line=reference!='SELECTION' and context.scene.better_item.arrange_on_axis and sum(axes)==1
    targets={}
    for obj in objects:
        if obj.name==fixed:targets[obj.name]=tuple(origins[obj.name]);continue
        if on_line:
            axis=next(i for i,flag in enumerate(axes) if flag)
            world=origin+directions[:,axis]*planned[obj.name][axis]
        else:world=origin+np.linalg.solve(directions.T,planned[obj.name])
        targets[obj.name]=tuple(world)
    expected={name:(planned[name]+low,planned[name]+high) for name,(low,high) in local.items()}
    def verify(actual_objects):
        if key is not None and (not np.array_equal(np.asarray(key.matrix_world.translation),key_position) if fixed is None else not engine._position_matches(key,key_position)):
            raise BetterItemError('[BI-G004] Reference "%s" moves with a target through parenting or another dependency. Use an independent reference before distributing. The operation was rolled back.'%key.name)
        if key is not None and not np.allclose(np.asarray(key.matrix_world.to_3x3()),key_linear,rtol=8*np.finfo(np.float32).eps,atol=0):
            raise BetterItemError('[BI-G005] Rotation or Scale of the reference changes with the targets. Disable its dependent transform driver or use an independent reference. The operation was rolled back.')
        measured={}
        for obj in actual_objects:
            if obj.name==fixed:continue
            if not np.allclose(np.asarray(obj.matrix_world.to_3x3()),linear[obj.name],rtol=8*np.finfo(np.float32).eps,atol=0):
                raise BetterItemError('[BI-G005] Rotation or Scale of "%s" changes when Location changes. Disable the dependent transform driver before geometric distribution. The operation was rolled back.'%obj.name)
            low,high=_bounds(obj,basis)
            old_low,old_high=local[obj.name]
            widths=old_high-old_low
            shape_tolerance=32*np.finfo(np.float32).eps*widths+64*np.finfo(np.float64).eps*np.maximum(np.abs(old_low),np.abs(old_high))
            if np.any(np.abs(low-old_low)>shape_tolerance) or np.any(np.abs(high-old_high)>shape_tolerance):
                raise BetterItemError('[BI-G003] Geometry of "%s" changes when it moves. Apply or disable position-dependent modifiers before geometric distribution. The operation was rolled back.'%obj.name)
            center=directions.T @ (np.asarray(obj.matrix_world.translation)-origin)
            measured[obj.name]=(center+low,center+high)
        for axis,order in chains.items():
            for index,name in enumerate(order):
                low,high=measured[name];want_low,want_high=expected[name]
                width=local[name][1][axis]-local[name][0][axis]
                tolerance=32*np.finfo(np.float32).eps*max(width,gap)+64*np.finfo(np.float64).eps*max(abs(want_low[axis]),abs(want_high[axis]))
                if max(abs(low[axis]-want_low[axis]),abs(high[axis]-want_high[axis]))>tolerance:
                    raise BetterItemError('[BI-G002] The requested gap on %s cannot be retained for "%s" at the current coordinate precision. Use a larger spacing magnitude or reduce large object/parent offsets. The operation was rolled back.'%('XYZ'[axis],name))
                if index or reference!='SELECTION':
                    if index:previous=measured[order[index-1]]
                    else:
                        actual_key_coordinate=directions.T @ (np.asarray(key.matrix_world.translation)-origin) if key is not None else np.zeros(3)
                        actual_key_bounds=_bounds(key,basis) if key and transform_view.has_surface_geometry(key) else key_bounds
                        if not np.allclose(actual_key_bounds,key_bounds,rtol=32*np.finfo(np.float32).eps,atol=0):
                            raise BetterItemError('[BI-G003] Reference geometry changes when a target moves. Apply or disable its position-dependent modifiers before geometric distribution. The operation was rolled back.')
                        previous=tuple(actual_key_coordinate+value for value in actual_key_bounds)
                    actual_gap=low[axis]-previous[1][axis] if direction>0 else previous[0][axis]-high[axis]
                    if gap>0 and actual_gap<=0 or abs(actual_gap-gap)>tolerance*2:
                        raise BetterItemError('[BI-G002] The gap before "%s" on %s cannot be distinguished at this coordinate precision. Use a larger spacing magnitude or reduce coordinate offsets. The operation was rolled back.'%(name,'XYZ'[axis]))
    return targets,verify
