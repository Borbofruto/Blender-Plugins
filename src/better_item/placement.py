# SPDX-License-Identifier: GPL-3.0-or-later
"""Evaluated placement points and occupied intervals; never edits mesh data."""
import numpy as np
import bpy
from collections import OrderedDict
from mathutils import Matrix
from . import transform_view
from .math_core import BetterItemError

BASES=[('ORIGINS','Origins','Use each existing object origin'),
    ('BOUNDS_CENTER','Bounds Center','Use the evaluated world-aligned bounding box center, without changing the origin'),
    ('SURFACE','Center of Mass (Surface)','Area-weighted centroid of the evaluated surface'),
    ('VOLUME','Center of Mass (Volume)','Uniform-density centroid of a closed, consistently oriented evaluated volume'),
    ('GEOMETRY','Geometry Bounds','Use occupied projected intervals for equal physical gaps')]
# Explicit numeric IDs preserve saved enum values when Endpoint omits Geometry.
_IDS={'ORIGINS':0,'GEOMETRY':1,'BOUNDS_CENTER':2,'SURFACE':3,'VOLUME':4}
OFFSET_ITEMS=[(*item,_IDS[item[0]]) for item in BASES]
ENDPOINT_ITEMS=[item for item in OFFSET_ITEMS if item[0]!='GEOMETRY']


def items(owner,context):
    method=getattr(owner,'distribution_method',getattr(owner,'method','OFFSET'))
    return ENDPOINT_ITEMS if method=='ENDPOINT' else OFFSET_ITEMS


def migrate(settings):
    if settings.get('placement_schema',0)>=1:return
    old=int(settings.get('distribution_mode',0))
    settings['offset_placement_value']=old
    settings['endpoint_placement_value']=old if old!=1 else 0
    if old==1 and getattr(settings,'distribution_method',getattr(settings,'method','OFFSET'))=='ENDPOINT':settings['placement_migration_notice']=True
    settings['placement_schema']=1


def read(settings):
    key='endpoint_placement_value' if getattr(settings,'distribution_method',getattr(settings,'method','OFFSET'))=='ENDPOINT' else 'offset_placement_value'
    old=int(settings.get('distribution_mode',0))
    fallback=old if getattr(settings,'distribution_method',getattr(settings,'method','OFFSET'))!='ENDPOINT' or old!=1 else 0
    return int(settings.get(key,fallback))


def write(settings,value):
    migrate(settings)
    key='endpoint_placement_value' if getattr(settings,'distribution_method',getattr(settings,'method','OFFSET'))=='ENDPOINT' else 'offset_placement_value'
    settings[key]=value
    settings['placement_migration_notice']=False


def operator_read(owner):
    return owner.endpoint_placement if owner.method=='ENDPOINT' else owner.offset_placement


def operator_write(owner,value):
    if owner.method=='ENDPOINT':owner.endpoint_placement=value
    else:owner.offset_placement=value


_point_cache=OrderedDict()


def _triangles(obj):
    if not transform_view.has_surface_geometry(obj):
        raise BetterItemError('[BI-P001] "%s" has no surface geometry for this placement basis. Choose Origins.'%obj.name)
    graph=bpy.context.evaluated_depsgraph_get()
    # Reuse the instance guard and bulk vertex reader used by Dimensions.
    transform_view._coordinates(obj,graph,transform_view._geometry_key(obj,graph))
    evaluated=obj.evaluated_get(graph);mesh=evaluated.to_mesh()
    try:
        if mesh is None or not mesh.polygons:
            raise BetterItemError('[BI-P001] "%s" has no evaluated faces for a centroid.'%obj.name)
        mesh.calc_loop_triangles()
        coords=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',coords)
        indices=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',indices)
        return coords.reshape(-1,3),indices.reshape(-1,3)
    finally:evaluated.to_mesh_clear()


def offset(obj,basis,axes=None):
    if basis=='ORIGINS':return np.zeros(3)
    graph=bpy.context.evaluated_depsgraph_get()
    key=(obj.as_pointer(),obj.data.as_pointer() if obj.data else 0,basis)
    signature=(transform_view._geometry_revision,graph.as_pointer(),
        tuple(v for row in obj.matrix_world.to_3x3() for v in row),tuple(v for row in axes for v in row) if axes is not None else None)
    if key in _point_cache and _point_cache[key][0]==signature:
        _point_cache.move_to_end(key);return _point_cache[key][1].copy()
    value=_offset(obj,basis,axes)
    _point_cache[key]=(signature,value.copy());_point_cache.move_to_end(key)
    while len(_point_cache)>64:_point_cache.popitem(last=False)
    return value


def _offset(obj,basis,axes=None):
    """World vector from native origin to the selected representative point.

    Bounds Center uses an orthonormal measurement frame (world if omitted).
    Geometry Bounds uses the same center only for transverse placement; its
    axial minimum/maximum are measured separately by intervals().
    """
    if basis=='ORIGINS':return np.zeros(3)
    linear=np.asarray(obj.matrix_world.to_3x3(),dtype=np.float64)
    if basis in {'BOUNDS_CENTER','GEOMETRY'}:
        if basis=='GEOMETRY' and axes is not None:
            center=offset(obj,'BOUNDS_CENTER')
            direction=np.asarray(axes.col[0],dtype=np.float64);direction/=np.linalg.norm(direction)
            low,high=transform_view.projected_bounds(obj,axes)
            return center+direction*((low[0]+high[0])*.5-np.dot(direction,center))
        axes=Matrix.Identity(3) if axes is None else axes
        directions=np.asarray(axes,dtype=np.float64);directions=directions/np.linalg.norm(directions,axis=0)
        low,high=transform_view.projected_bounds(obj,axes)
        return np.linalg.solve(directions.T,(np.asarray(low)+np.asarray(high))*.5)
    coords,triangles=_triangles(obj)
    # Recenter before integration to avoid volume cancellation for offset meshes.
    anchor=(coords.min(axis=0)+coords.max(axis=0))*.5
    points=(coords-anchor)@linear.T
    a,b,c=points[triangles[:,0]],points[triangles[:,1]],points[triangles[:,2]]
    if basis=='SURFACE':
        weights=np.linalg.norm(np.cross(b-a,c-a),axis=1)
        total=weights.sum()
        if not np.isfinite(total) or total<=0:
            raise BetterItemError('[BI-P002] "%s" has no nonzero evaluated surface area.'%obj.name)
        value=np.einsum('i,ij->j',weights,(a+b+c)/3)/total
    elif basis=='VOLUME':
        edges=np.concatenate((triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]))
        unique,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
        directed,directed_counts=np.unique(edges,axis=0,return_counts=True)
        if np.any(counts!=2) or np.any(directed_counts!=1) or len(directed)!=2*len(unique):
            raise BetterItemError('[BI-P003] "%s" needs closed, consistently oriented geometry for Volume Centroid. Repair the mesh or choose Surface Centroid.'%obj.name)
        weights=np.einsum('ij,ij->i',a,np.cross(b,c))
        total=weights.sum();magnitude=np.abs(weights).sum()
        if not np.isfinite(total) or magnitude==0 or abs(total)<=64*np.finfo(np.float64).eps*magnitude:
            raise BetterItemError('[BI-P003] "%s" has zero or unresolved signed volume. Repair the volume or choose another basis.'%obj.name)
        value=np.einsum('i,ij->j',weights,(a+b+c)/4)/total
    else:raise BetterItemError('[BI-P001] Choose a valid placement basis.')
    result=anchor@linear.T+value
    if not np.isfinite(result).all():raise BetterItemError('[BI-P002] "%s" has an unresolved geometric centroid.'%obj.name)
    return result


def intervals(obj,axes):
    low,high=transform_view.projected_bounds(obj,axes)
    return np.asarray(low),np.asarray(high)
