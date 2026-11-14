# SPDX-License-Identifier: GPL-3.0-or-later
"""One live transform view: reference changes readings, setters change the object."""
import math
import bpy
import numpy as np
from collections import OrderedDict
from mathutils import Matrix, Euler
from . import engine, frames
from .math_core import BetterItemError, linked_values
from bpy.app.handlers import persistent

_dimension_cache=OrderedDict()
_geometry_cache=OrderedDict()
_GEOMETRY_CACHE_ENTRIES=8
_GEOMETRY_CACHE_BYTES=64*1024*1024
_DIMENSION_CACHE_ENTRIES=32


def has_surface_geometry(obj):
    return obj.type in {'MESH','CURVE','SURFACE','FONT','META'}


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
    updated_trees=set()
    for update in depsgraph.updates:
        if isinstance(update.id.original,bpy.types.NodeTree):updated_trees.add(update.id.original.as_pointer())
        if not update.is_updated_geometry:continue
        original=update.id.original
        if isinstance(original,bpy.types.Object):updated_objects.add(original.as_pointer())
        else:updated_data.add(original.as_pointer())
    if updated_trees:
        for obj in bpy.data.objects:
            if any(mod.type=='NODES' and mod.node_group and _tree_matches(mod.node_group,updated_trees) for mod in obj.modifiers):updated_objects.add(obj.as_pointer())
    def changed(key):return key[1] in updated_objects or key[2] in updated_data
    for key in list(_geometry_cache):
        if changed(key):del _geometry_cache[key]
    for key in list(_dimension_cache):
        if changed(key):del _dimension_cache[key]


def _tree_matches(tree,pointers,seen=()):
    pointer=tree.as_pointer()
    if pointer in seen:return False
    if pointer in pointers:return True
    return any(node.type=='GROUP' and node.node_tree and _tree_matches(node.node_tree,pointers,(*seen,pointer)) for node in tree.nodes)


def _geometry_key(obj,depsgraph):
    # Frame/subframe evaluation invalidates all measurements through clear_cache.
    # No action/driver introspection is required to identify cached geometry.
    return (depsgraph.as_pointer(),obj.as_pointer(),obj.data.as_pointer() if obj.data else 0)


def _coordinates(obj,depsgraph,key):
    if not has_surface_geometry(obj):
        raise BetterItemError('Dimensions is unavailable for object type %s.'%obj.type)
    if key in _geometry_cache:
        _geometry_cache.move_to_end(key)
        return _geometry_cache[key]
    evaluated=obj.evaluated_get(depsgraph)
    try:mesh=evaluated.to_mesh()
    except RuntimeError as exc:
        raise BetterItemError('Dimensions is unavailable: "%s" has no evaluated surface geometry.'%obj.name) from exc
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


def _dimension_directions(axes):
    """Physical widths use unit directions, preserving their oblique angles."""
    directions=axes.copy()
    for i in range(3):
        column=tuple(axes.col[i])
        length=math.hypot(*column)
        if not math.isfinite(length) or length==0:
            raise BetterItemError('Dimensions requires finite, nonzero reference directions.')
        directions.col[i]=tuple(value/length for value in column)
    return directions


def dimensions(obj, axes):
    depsgraph=bpy.context.evaluated_depsgraph_get()
    key=_geometry_key(obj,depsgraph)
    transform=_dimension_directions(axes).transposed() @ obj.matrix_world.to_3x3()
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
    return settings.transform_space=='DEFAULT' or settings.reference_mode=='INDIVIDUAL' and settings.orientation in {'GLOBAL','LOCAL'} and settings.pivot_mode == 'GLOBAL'


def _validate_default_group(obj,group):
    if group=='ROTATION' and obj.rotation_mode in {'QUATERNION','AXIS_ANGLE'}:
        field='rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_axis_angle'
        raise BetterItemError('Default / Local Rotation uses %s storage. Edit %s directly or select an Euler rotation mode.'%(obj.rotation_mode,field))
    if group=='DIMENSIONS' and not has_surface_geometry(obj):
        raise BetterItemError('Dimensions is unavailable for object type %s.'%obj.type)


def values(context, obj, group):
    if obj.better_item.transform_space=='DEFAULT':
        _validate_default_group(obj,group)
        return tuple(getattr(obj,{'LOCATION':'location','ROTATION':'rotation_euler','SCALE':'scale','DIMENSIONS':'dimensions'}[group]))
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
    from . import orientation
    axes = rotation_basis(frames.object_axes(context,obj))
    order = obj.better_item.view_rotation_order
    desired = axes @ Euler(values,order).to_matrix()
    native=(obj.parent is None and obj.rotation_mode==order and all(abs(v)<1e-12 for v in obj.delta_rotation_euler)
        and max(abs(axes[i][j]-(1 if i==j else 0)) for i in range(3) for j in range(3))<1e-8)
    center = frames.object_origin(context,obj) if obj.better_item.use_reference_pivot else obj.matrix_world.translation.copy()
    previous = _snapshot(obj)
    world = obj.matrix_world.copy()
    local_before=orientation.local_rotation(obj).to_matrix()
    try:
        if native:
            obj.rotation_euler=values
        else:
            local=(orientation.inherited_rotation(obj).inverted() @ desired).to_quaternion()
            delta=orientation.delta_rotation(obj)
            requested=delta.inverted() @ local
            if obj.rotation_mode=='QUATERNION':obj.rotation_quaternion=requested
            elif obj.rotation_mode=='AXIS_ANGLE':
                axis,angle=requested.to_axis_angle()
                obj.rotation_axis_angle=(angle,*axis)
            else:obj.rotation_euler=requested.to_euler(obj.rotation_mode,obj.rotation_euler)
        context.view_layer.update()
        # Preserve Scale exactly. Reject native rotations that would deform the
        # world-space object through a nonuniform parent rather than rotate it.
        inherited=engine._parent_matrix(obj).to_3x3()
        try:world_delta=inherited @ orientation.local_rotation(obj).to_matrix() @ local_before.transposed() @ inherited.inverted()
        except ValueError as exc:raise BetterItemError('The parent transform is singular; restore nonzero parent Scale.') from exc
        gram=world_delta.transposed() @ world_delta
        if max(abs(gram[i][j]-(1 if i==j else 0)) for i in range(3) for j in range(3))>2e-5:
            raise BetterItemError('The nonuniform parent transform prevents a rigid reference-space rotation.')
        target=center+world_delta @ (world.translation-center)
        obj.location=engine._target_location(obj,target)
        context.view_layer.update()
        actual = orientation.rotation(obj).to_quaternion()
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


def _dimensions_modifier(obj):
    """Resolve our one final affine stage without changing the user's stack."""
    owned=[mod for mod in obj.modifiers if mod.type=='NODES' and mod.node_group
           and mod.node_group.get('better_item_affine')==1]
    if len(owned)>1:
        raise BetterItemError('[BI-M001] Object "%s" has multiple Better Item Dimensions modifiers: %s. Resolve the stack before editing Reference Dimensions; no modifiers were changed.'%
            (obj.name,', '.join(mod.name for mod in owned)))
    if not owned:return None
    modifier=owned[0]
    if modifier!=obj.modifiers[-1]:
        raise BetterItemError('[BI-M002] Move "%s" to the end of the modifier stack before editing Reference Dimensions. The addon will not reorder or duplicate it.'%modifier.name)
    if not modifier.show_viewport or not modifier.show_render:
        raise BetterItemError('Enable the Better Item Dimensions modifier before editing Dimensions.')
    return modifier


def set_dimensions(context,obj,desired):
    if any(obj.lock_scale):raise BetterItemError('Unlock Scale before editing Dimensions.')
    modifier=_dimensions_modifier(obj)
    axes = _dimension_directions(frames.object_axes(context,obj))
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
    created=False
    old_group=None
    if modifier is None:
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
    old_matrix=Matrix(tuple(tuple(group.nodes['Better Item Row %d'%i].inputs[1].default_value) for i in range(3)))
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
    if obj.better_item.transform_space=='DEFAULT':return _edit_default(obj,group,axis,value)
    if group=='SCALE':
        if not scale_editable(obj):raise BetterItemError('Scale shows native values and is read-only in reference modes.')
        return engine.edit_scale_component(obj,axis,value)
    if group=='LOCATION':
        before,uncertainty=frames.position_values(context,obj)
        denominator_tolerance=uncertainty[axis]
    else:
        before=values(context,obj,group)
        denominator_tolerance=0.
    links=getattr(obj.better_item,engine.GROUP_LINK[group])
    desired=linked_values(before,axis,value,links,zero_angle_as_turn=group=='ROTATION',denominator_tolerance=denominator_tolerance)
    if (before==desired if group=='LOCATION' else not any(engine.different(a,b) for a,b in zip(before,desired))):return
    if group=='LOCATION':
        return frames.set_position(context,obj,desired)
    if group=='ROTATION':return set_rotation(context,obj,desired)
    return set_dimensions(context,obj,desired)


def _edit_default(obj,group,axis,value):
    """Edit Blender's actual Item channels; no parent/reference conversion."""
    _validate_default_group(obj,group)
    if group=='SCALE':return engine.edit_scale_component(obj,axis,value)
    attribute={'LOCATION':'location','ROTATION':'rotation_euler','DIMENSIONS':'dimensions'}[group]
    before=tuple(getattr(obj,attribute))
    desired=linked_values(before,axis,value,getattr(obj.better_item,engine.GROUP_LINK[group]),zero_angle_as_turn=group=='ROTATION')
    locks=obj.lock_location if group=='LOCATION' else obj.lock_rotation if group=='ROTATION' else obj.lock_scale
    if group!='DIMENSIONS' and any(locked and engine.different(old,new) for locked,old,new in zip(locks,before,desired)):
        raise BetterItemError('Unlock the affected default/local channel before editing it.')
    engine._driver_guard(obj,{'scale' if group=='DIMENSIONS' else attribute})
    previous=_snapshot(obj)
    try:
        if group=='DIMENSIONS':
            if any(abs(old)<1e-12 and engine.different(old,new) for old,new in zip(before,desired)):
                raise BetterItemError('A zero Dimension cannot be reopened through Scale. Restore a nonzero Scale first.')
            obj.scale=tuple(scale*(new/old) if abs(old)>1e-12 else scale for scale,old,new in zip(obj.scale,before,desired))
        else:setattr(obj,attribute,desired)
        bpy.context.view_layer.update()
        if group=='DIMENSIONS' and any(locked and engine.different(old,new) for locked,old,new in zip(locks,previous['scale'],obj.scale)):
            raise BetterItemError('Dimensions would change a locked Scale channel.')
        if not engine._matches(tuple(getattr(obj,attribute)),desired):
            raise BetterItemError('Blender did not retain the requested default/local channel values.')
    except Exception:
        _restore(obj,previous)
        raise
