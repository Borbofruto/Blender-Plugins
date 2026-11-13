"""Blender integration: native transforms and transactional world positioning."""
import math
import bpy
from mathutils import Vector
from .math_core import BetterItemError,linked_values,different

GROUP_ATTR={'LOCATION':'location','ROTATION':'rotation_euler','SCALE':'scale','DIMENSIONS':'dimensions'}
GROUP_LINK={'LOCATION':'link_location','ROTATION':'link_rotation','SCALE':'link_scale','DIMENSIONS':'link_dimensions'}
GROUP_LOCK={'LOCATION':'lock_location','ROTATION':'lock_rotation','SCALE':'lock_scale','DIMENSIONS':'lock_scale'}
EULER_MODES={'XYZ','XZY','YXZ','YZX','ZXY','ZYX'}


def editable(obj):
    if not obj.is_editable:
        raise BetterItemError('O objeto "%s" nao permite edicao local.' % obj.name)


def _driver_guard(obj,paths):
    animation=obj.animation_data
    if animation and any(not curve.mute and curve.data_path in paths for curve in animation.drivers):
        raise BetterItemError('O objeto "%s" possui um driver nesses campos. Edite ou desative o driver.' % obj.name)


def values(obj,group):
    return tuple(getattr(obj,GROUP_ATTR[group]))


def _matches(actual,expected):
    return all(math.isclose(a,b,rel_tol=3e-7,abs_tol=1e-8) for a,b in zip(actual,expected))


def edit_component(obj,group,axis,value):
    editable(obj)
    if group=='ROTATION' and obj.rotation_mode not in EULER_MODES:
        raise BetterItemError('O vinculo proporcional de rotacao exige um modo Euler.')
    bpy.context.view_layer.update()
    before=values(obj,group)
    if group=='DIMENSIONS' and (value<0 or (before[axis]==0 and value!=0)):
        raise BetterItemError('Uma dimensao nula nao pode ser ampliada por escala. Edite a geometria primeiro.')
    links=getattr(obj.better_item,GROUP_LINK[group])
    desired=linked_values(before,axis,value,links)
    for i,locked in enumerate(getattr(obj,GROUP_LOCK[group])):
        if locked and different(before[i],desired[i]):
            raise BetterItemError('O eixo %s esta bloqueado em "%s". A alteracao vinculada foi cancelada.' % ('XYZ'[i],obj.name))
    attribute=GROUP_ATTR[group]
    _driver_guard(obj,{'scale'} if group=='DIMENSIONS' else {attribute})
    restore_attribute='scale' if group=='DIMENSIONS' else attribute
    previous=tuple(getattr(obj,restore_attribute))
    try:
        setattr(obj,attribute,desired)
        bpy.context.view_layer.update()
        if not _matches(values(obj,group),desired):
            raise BetterItemError('O Blender nao manteve o valor solicitado. Verifique drivers, restricoes e a geometria de "%s".' % obj.name)
    except Exception as exc:
        setattr(obj,restore_attribute,previous)
        bpy.context.view_layer.update()
        if isinstance(exc,BetterItemError):
            raise
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
        raise BetterItemError('O parentesco de "%s" possui uma transformacao singular; nao e possivel resolver a posicao.' % obj.name) from exc


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
                raise BetterItemError('O objeto "%s" tem constraints ativas. Desative-as antes de alinhar ou distribuir.' % obj.name)
            _driver_guard(obj,{'location','delta_location'})
            local_delta=_local_delta(obj,delta)
            for axis,locked in enumerate(obj.lock_location):
                if locked and different(local_delta[axis],0):
                    raise BetterItemError('O eixo local %s esta bloqueado em "%s". Nenhum objeto foi reposicionado.' % ('XYZ'[axis],obj.name))
            desired=obj.location+local_delta
            if not all(math.isfinite(component) for component in desired):
                raise BetterItemError('A transformacao de "%s" excedeu o intervalo numerico.' % obj.name)
            changed.append(obj)
            obj.location=desired
        bpy.context.view_layer.update()
        for obj in objects:
            if not _matches(obj.matrix_world.translation,targets[obj.name]):
                raise BetterItemError('Nao foi possivel posicionar "%s" na coordenada planejada. Verifique parentesco e drivers.' % obj.name)
    except Exception as exc:
        for obj in changed:
            obj.location=previous[obj]
        bpy.context.view_layer.update()
        if isinstance(exc,BetterItemError):
            raise
        raise BetterItemError(str(exc)) from exc
    return len(changed)
