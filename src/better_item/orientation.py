# SPDX-License-Identifier: GPL-3.0-or-later
"""Axis-oriented operations on the active object, using native transforms."""
import math
import bpy
from mathutils import Matrix, Vector
from . import engine
from .math_core import BetterItemError, vector3


def basis(obj, mode, reference=None):
    if mode == 'GLOBAL':
        return Matrix.Identity(3)
    source = obj if mode == 'LOCAL' else reference
    if source is None:
        raise BetterItemError('Choose an Orientation Object.')
    if mode not in {'LOCAL', 'REFERENCE'}:
        raise BetterItemError('Invalid orientation.')
    # Quaternion extraction removes translation, scale and reflections.
    return source.matrix_world.to_quaternion().normalized().to_matrix()


def dimensions(obj, axes):
    """Evaluated bounding-box extents projected onto an orthonormal frame."""
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    corners = evaluated.bound_box
    if all(tuple(corner) == (-1, -1, -1) for corner in corners):
        raise BetterItemError('This object has no geometry bounds to measure.')
    inverse = axes.transposed()
    linear = evaluated.matrix_world.to_3x3()
    points = [inverse @ (linear @ Vector(corner)) for corner in corners]
    return tuple(max(p[i] for p in points)-min(p[i] for p in points) for i in range(3))


def pivot(context, obj):
    mode = context.scene.tool_settings.transform_pivot_point
    if mode == 'CURSOR':
        return context.scene.cursor.location.copy()
    if mode == 'BOUNDING_BOX_CENTER':
        evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
        if not all(tuple(c) == (-1,-1,-1) for c in evaluated.bound_box):
            return evaluated.matrix_world @ (sum((Vector(c) for c in evaluated.bound_box),Vector()) / 8)
    return obj.matrix_world.translation.copy()


def apply(context, obj, kind, values, mode, reference=None, *, axes_override=None, pivot_override=None, validate=None):
    """Freeze axes before an operation; reference position never defines pivot."""
    engine.editable(obj)
    context.view_layer.update()
    axes = axes_override.copy() if axes_override is not None else basis(obj, mode, reference)
    values = vector3(values)
    if kind == 'MOVE':
        target = obj.matrix_world.translation + axes @ Vector(values)
        return engine.apply_world_positions([obj], {obj.name: tuple(target)})
    if any(not c.mute and c.influence != 0 for c in obj.constraints):
        raise BetterItemError('Disable active constraints before this transform.')
    engine._driver_guard(obj, {'location', 'rotation_euler', 'rotation_quaternion',
        'rotation_axis_angle', 'scale', 'delta_location', 'delta_rotation_euler',
        'delta_rotation_quaternion', 'delta_scale'})
    if kind not in {'ROTATE', 'SCALE', 'DIMENSIONS'}:
        raise BetterItemError('Invalid oriented operation.')
    if kind == 'ROTATE' and any(values) and (any(obj.lock_rotation) or obj.lock_rotation_w):
        raise BetterItemError('Unlock Rotation before this operation.')
    if kind in {'SCALE','DIMENSIONS'} and any(obj.lock_scale):
        raise BetterItemError('Unlock Scale before this operation.')
    # Native transforms otherwise insert animation keys when auto-key is on.
    if context.scene.tool_settings.use_keyframe_insert_auto:
        raise BetterItemError('Disable Auto Key before this operation.')
    previous = {name: tuple(getattr(obj, name)) for name in (
        'location', 'rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'scale')}
    selected = list(context.selected_objects)
    active = context.view_layer.objects.active
    tools = context.scene.tool_settings
    tool_options = {name: getattr(tools,name) for name in (
        'use_transform_data_origin','use_transform_pivot_point_align','use_transform_skip_children')}
    try:
        for name in tool_options:
            setattr(tools,name,False)
        for item in selected:
            item.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        common = dict(orient_type='GLOBAL', orient_matrix=axes,
            orient_matrix_type='GLOBAL', center_override=tuple(pivot_override if pivot_override is not None else pivot(context,obj)),
            use_proportional_edit=False, mirror=False, snap=False)
        if kind == 'ROTATE':
            for i, angle in enumerate(values):
                if angle:
                    status = bpy.ops.transform.rotate(value=angle, orient_axis='XYZ'[i],
                        constraint_axis=tuple(j == i for j in range(3)), **common)
                    if status != {'FINISHED'}:
                        raise BetterItemError('Blender cancelled the rotation.')
        else:
            factors = values
            if kind == 'DIMENSIONS':
                before = dimensions(obj, axes)
                if any(v < 0 for v in values):
                    raise BetterItemError('Dimensions must be nonnegative.')
                if any(size <= 1e-12 and abs(v-size) > 1e-12 for size,v in zip(before, values)):
                    raise BetterItemError('A zero dimension requires editing the geometry.')
                factors = tuple(v/size if size > 1e-12 else 1 for size,v in zip(before, values))
            status = bpy.ops.transform.resize(value=factors, constraint_axis=(True,True,True), **common)
            if status != {'FINISHED'}:
                raise BetterItemError('Blender cancelled the scale.')
        context.view_layer.update()
        for name, locks in (('location',obj.lock_location),('scale',obj.lock_scale),
                            ('rotation_euler',obj.lock_rotation)):
            if any(locked and engine.different(a,b) for locked,a,b in zip(locks,previous[name],getattr(obj,name))):
                raise BetterItemError('This transform would change a locked local axis.')
        if kind == 'ROTATE' and (any(obj.lock_rotation) or obj.lock_rotation_w):
            if obj.rotation_mode not in engine.EULER_MODES:
                raise BetterItemError('Unlock Rotation to rotate in this mode.')
        if kind == 'DIMENSIONS' and not all(math.isclose(a,b,rel_tol=2e-6,abs_tol=1e-7)
                for a,b in zip(dimensions(obj, axes), values)):
            raise BetterItemError('Estas dimensoes exigem deformacao fora da escala nativa. '
                'Use os eixos locais da peca, escala uniforme ou altere a geometria.')
        if validate is not None:
            validate()
    except Exception as exc:
        for name, value in previous.items():
            setattr(obj, name, value)
        context.view_layer.update()
        if isinstance(exc, BetterItemError):
            raise
        raise BetterItemError(str(exc)) from exc
    finally:
        for name, value in tool_options.items():
            setattr(tools,name,value)
        obj.select_set(False)
        for item in selected:
            item.select_set(True)
        context.view_layer.objects.active = active
    return 1
