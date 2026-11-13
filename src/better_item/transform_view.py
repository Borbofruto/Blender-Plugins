# SPDX-License-Identifier: GPL-3.0-or-later
"""One live transform view: reference changes readings, setters change the object."""
import math
import bpy
import numpy as np
from collections import OrderedDict
from mathutils import Matrix, Vector, Euler
from . import engine, frames
from .math_core import BetterItemError, linked_values
from bpy.app.handlers import persistent

_dimension_cache=OrderedDict()
_geometry_cache=OrderedDict()
_GEOMETRY_CACHE_ENTRIES=8
_GEOMETRY_CACHE_BYTES=64*1024*1024
_DIMENSION_CACHE_ENTRIES=32


@persistent
def clear_cache(_scene=None,_depsgraph=None):
    _dimension_cache.clear()
    _geometry_cache.clear()


@persistent
def invalidate_geometry(_scene,depsgraph):
    """Only evaluated geometry updates invalidate local vertex coordinates.

    Transform-only updates are handled by the projection key. Translation is
    intentionally absent from that key because it cannot change extents.
    """
    updated_objects=set()
    updated_data=set()
    for update in depsgraph.updates:
        if not update.is_updated_geometry:continue
        original=update.id.original
        if isinstance(original,bpy.types.Object):updated_objects.add(original.as_pointer())
        else:updated_data.add(original.as_pointer())
    def changed(key):return key[1] in updated_objects or key[2] in updated_data
    for key in list(_geometry_cache):
        if changed(key):del _geometry_cache[key]
    for key in list(_dimension_cache):
        if changed(key):del _dimension_cache[key]


def _geometry_key(obj,depsgraph):
    return (depsgraph.as_pointer(),obj.as_pointer(),obj.data.as_pointer() if obj.data else 0)


def _coordinates(obj,depsgraph,key):
    if key in _geometry_cache:
        _geometry_cache.move_to_end(key)
        return _geometry_cache[key]
    evaluated=obj.evaluated_get(depsgraph)
    mesh=evaluated.to_mesh()
    try:
        if mesh is None or not mesh.vertices:
            raise BetterItemError('This object has no evaluated vertices to measure.')
        coordinates=np.empty(len(mesh.vertices)*3,dtype=np.float32)
        mesh.vertices.foreach_get('co',coordinates)
        coordinates=coordinates.reshape((-1,3))
    finally:
        evaluated.to_mesh_clear()
    if coordinates.nbytes<=_GEOMETRY_CACHE_BYTES:
        while _geometry_cache and (len(_geometry_cache)>=_GEOMETRY_CACHE_ENTRIES
                or sum(array.nbytes for array in _geometry_cache.values())+coordinates.nbytes>_GEOMETRY_CACHE_BYTES):
            _geometry_cache.popitem(last=False)
        _geometry_cache[key]=coordinates
    return coordinates


def dimensions(obj, axes):
    depsgraph=bpy.context.evaluated_depsgraph_get()
    key=_geometry_key(obj,depsgraph)
    transform=axes.transposed() @ obj.matrix_world.to_3x3()
    projection=tuple(v for row in transform for v in row)
    if key in _dimension_cache and _dimension_cache[key][0]==projection:
        _dimension_cache.move_to_end(key)
        return _dimension_cache[key][1]
    coordinates=_coordinates(obj,depsgraph,key)
    matrix=np.asarray(transform,dtype=np.float32)
    extents=[]
    for row in matrix:
        projected=np.einsum('ij,j->i',coordinates,row,optimize=False)
        extents.append(float(projected.max())-float(projected.min()))
    result=tuple(extents)
    _dimension_cache[key]=(projection,result)
    _dimension_cache.move_to_end(key)
    while len(_dimension_cache)>_DIMENSION_CACHE_ENTRIES:_dimension_cache.popitem(last=False)
    return result


def scale_editable(obj):
    settings = obj.better_item
    return settings.reference_mode=='INDIVIDUAL' and settings.orientation in {'GLOBAL','LOCAL'} and settings.pivot_mode == 'GLOBAL'


def values(context, obj, group):
    if group == 'LOCATION':return frames.relative_values(context,obj,'POSITION')
    if group == 'ROTATION':return frames.relative_values(context,obj,'ROTATION')
    if group == 'SCALE':return tuple(obj.scale)
    return dimensions(obj,frames.object_axes(context,obj))


def _snapshot(obj):
    return {name:tuple(getattr(obj,name)) for name in (
        'location','rotation_euler','rotation_quaternion','rotation_axis_angle','scale')}


def _restore(obj, previous):
    for name,value in previous.items():setattr(obj,name,value)
    bpy.context.view_layer.update()


def set_rotation(context, obj, values):
    if any(not c.mute and c.influence for c in obj.constraints):
        raise BetterItemError('Disable active constraints before editing Rotation.')
    engine._driver_guard(obj, {'location','rotation_euler','rotation_quaternion','rotation_axis_angle',
        'scale','delta_rotation_euler','delta_rotation_quaternion','delta_scale'})
    if any(obj.lock_rotation) or obj.lock_rotation_w:
        raise BetterItemError('Unlock Rotation before editing reference-space rotation.')
    from .native_refs import rotation_basis
    axes = rotation_basis(frames.object_axes(context,obj))
    order = obj.better_item.view_rotation_order
    desired = axes @ Euler(values,order).to_matrix()
    native=(obj.parent is None and obj.rotation_mode==order and all(abs(v)<1e-12 for v in obj.delta_rotation_euler)
        and max(abs(axes[i][j]-(1 if i==j else 0)) for i in range(3) for j in range(3))<1e-8)
    current = obj.rotation_euler.to_matrix() if native else obj.matrix_world.to_quaternion().normalized().to_matrix()
    delta = desired @ current.transposed()
    center = frames.object_origin(context,obj) if obj.better_item.use_reference_pivot else obj.matrix_world.translation.copy()
    previous = _snapshot(obj)
    world = obj.matrix_world.copy()
    target = delta.to_4x4() @ world
    target.translation = center + delta @ (world.translation-center)
    try:
        if native:
            obj.location=target.translation
            obj.rotation_euler=values
        else:obj.matrix_world = target
        context.view_layer.update()
        actual = obj.rotation_euler.to_quaternion() if native else obj.matrix_world.to_quaternion().normalized()
        error = actual.rotation_difference(desired.to_quaternion()).angle
        if min(abs(error),abs(math.tau-error)) > 2e-4:
            raise BetterItemError('The parent transform prevents this reference-space rotation.')
        for name,locks in (('location',obj.lock_location),('scale',obj.lock_scale)):
            if any(lock and engine.different(a,b) for lock,a,b in zip(locks,previous[name],getattr(obj,name))):
                raise BetterItemError('This rotation would change a locked native axis.')
        obj.better_item['view_rotation_hint']=tuple(values)
        obj.better_item['view_rotation_hint_order']=order
    except Exception:
        _restore(obj,previous)
        raise


def _new_affine_group():
    group = bpy.data.node_groups.new('Better Item Dimensions','GeometryNodeTree')
    group['better_item_affine'] = 1
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links = group.nodes,group.links
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    position = nodes.new('GeometryNodeInputPosition')
    combine = nodes.new('ShaderNodeCombineXYZ')
    set_position = nodes.new('GeometryNodeSetPosition')
    for i in range(3):
        row = nodes.new('ShaderNodeVectorMath')
        row.operation = 'DOT_PRODUCT'
        row.name = 'Better Item Row %d' % i
        links.new(position.outputs['Position'],row.inputs[0])
        links.new(row.outputs['Value'],combine.inputs[i])
    links.new(input_node.outputs['Geometry'],set_position.inputs['Geometry'])
    links.new(combine.outputs['Vector'],set_position.inputs['Position'])
    links.new(set_position.outputs['Geometry'],output_node.inputs['Geometry'])
    _write_affine(group,Matrix.Identity(3))
    return group


def _write_affine(group, matrix):
    for i in range(3):group.nodes['Better Item Row %d' % i].inputs[1].default_value=matrix[i]
    group['better_item_matrix']=[v for row in matrix for v in row]


def set_dimensions(context,obj,desired):
    if any(obj.lock_scale):raise BetterItemError('Unlock Scale before editing Dimensions.')
    axes = frames.object_axes(context,obj)
    before = dimensions(obj,axes)
    if any(v<0 for v in desired):raise BetterItemError('Dimensions cannot be negative.')
    if any(size<=1e-12 and abs(value-size)>1e-12 for size,value in zip(before,desired)):
        raise BetterItemError('A zero dimension requires editing the geometry first.')
    factors=tuple(value/size if size>1e-12 else 1 for size,value in zip(before,desired))
    world_linear=obj.matrix_world.to_3x3()
    try: local=world_linear.inverted() @ axes.transposed().inverted() @ Matrix.Diagonal(factors) @ axes.transposed() @ world_linear
    except ValueError as exc:raise BetterItemError('The object transform is singular; restore a nonzero Scale first.') from exc
    # Use native Scale whenever the requested affine transform is diagonal locally.
    if all(abs(local[i][j])<2e-6 for i in range(3) for j in range(3) if i!=j):
        engine._driver_guard(obj,{'scale'})
        previous=tuple(obj.scale)
        try:
            obj.scale=tuple(previous[i]*local[i][i] for i in range(3))
            context.view_layer.update()
            if all(math.isclose(a,b,rel_tol=2e-5,abs_tol=1e-7) for a,b in zip(dimensions(obj,axes),desired)):return
        except Exception:
            obj.scale=previous
            context.view_layer.update()
            raise
        obj.scale=previous
        context.view_layer.update()
    if obj.type!='MESH':
        raise BetterItemError('Oblique reference-space dimension editing currently requires a Mesh object.')
    # Preserve the base mesh, shape keys, and shared mesh users. A constant
    # affine Geometry Nodes modifier stores the edit without linking any source.
    modifier=obj.modifiers[-1] if obj.modifiers else None
    owned=modifier and modifier.type=='NODES' and modifier.node_group and modifier.node_group.get('better_item_affine')==1
    created=False
    old_group=None
    if owned and (not modifier.show_viewport or not modifier.show_render):
        raise BetterItemError('Enable the Better Item Dimensions modifier before editing Dimensions.')
    if not owned:
        group=_new_affine_group()
        modifier=obj.modifiers.new('Better Item Dimensions','NODES')
        modifier.node_group=group
        created=True
    else:
        group=modifier.node_group
        if len(group.get('better_item_matrix',()))!=9 or any('Better Item Row %d' % i not in group.nodes for i in range(3)):
            raise BetterItemError('The Better Item Dimensions node group was modified. Restore its original nodes before editing Dimensions.')
        if group.users>1:
            old_group=group
            group=group.copy()
            modifier.node_group=group
    old_matrix=Matrix(tuple(tuple(group['better_item_matrix'][i*3+j] for j in range(3)) for i in range(3)))
    try:
        _write_affine(group,local @ old_matrix)
        context.view_layer.update()
        if not all(math.isclose(a,b,rel_tol=2e-5,abs_tol=1e-7) for a,b in zip(dimensions(obj,axes),desired)):
            raise BetterItemError('The evaluated geometry did not reach the requested Dimensions.')
    except Exception:
        if created:obj.modifiers.remove(modifier)
        elif old_group is not None:modifier.node_group=old_group
        else:_write_affine(group,old_matrix)
        if group.users==0:bpy.data.node_groups.remove(group)
        context.view_layer.update()
        raise


def edit_component(context,obj,group,axis,value):
    engine.editable(obj)
    context.view_layer.update()
    if group=='SCALE':
        if not scale_editable(obj):raise BetterItemError('Scale shows native values and is read-only in reference modes.')
        return engine.edit_scale_component(obj,axis,value)
    before=values(context,obj,group)
    links=getattr(obj.better_item,engine.GROUP_LINK[group])
    desired=linked_values(before,axis,value,links,zero_angle_as_turn=group=='ROTATION')
    if not any(engine.different(a,b) for a,b in zip(before,desired)):return
    if group=='LOCATION':
        return frames.set_position(context,obj,desired)
    if group=='ROTATION':return set_rotation(context,obj,desired)
    return set_dimensions(context,obj,desired)
