# SPDX-License-Identifier: GPL-3.0-or-later
"""Plan origin-based arrangements in an explicitly selected reference frame."""
import math
import numpy as np
from mathutils import Vector
from .math_core import BetterItemError,align_positions,distribute_positions

_last_error=(None,'')


def set_error(scene,message):
    global _last_error
    _last_error=(scene.as_pointer(),message)


def error(scene):
    return _last_error[1] if _last_error[0]==scene.as_pointer() else ''


def clear_error():
    global _last_error
    _last_error=(None,'')


def operation_reference(context):
    from . import references
    return 'SELECTION' if references.location_kind(context,context.scene.better_item,True)=='BOUNDING_BOX_CENTER' else 'REFERENCE'


def reference_frame(context,reference=None):
    from . import references
    settings=context.scene.better_item
    active=context.active_object or next(iter(context.selected_objects),None)
    reference=settings.reference if reference is None else (operation_reference(context) if reference=='AUTO' else reference)
    anchor=reference=='REFERENCE'
    try:
        axes=references.axes(context,settings,active,True)
        try:
            origin,source=references.origin(context,settings,active,True)
            if source is None and getattr(context,'mode','OBJECT')=='OBJECT' and references.location_kind(context,settings,True) in {'ACTIVE_ELEMENT','INDIVIDUAL_ORIGINS'}:source=active
        except BetterItemError:
            if anchor:raise
            # An unused origin must not block an orientation-only operation.
            origin,source=Vector(),None
    except (BetterItemError,AttributeError) as exc:
        raise BetterItemError('[BI-A002] Invalid arrangement reference: %s'%exc) from exc
    return np.asarray(axes,dtype=np.float64),np.asarray(origin,dtype=np.float64),source if anchor else None


def _mm_per_unit(scene):
    scale=scene.unit_settings.scale_length
    if not math.isfinite(scale) or scale<=0:raise BetterItemError('[BI-D001] Scene Unit Scale must be finite and greater than zero.')
    return 1000*scale


def _small(distance,minimum):
    return distance<minimum and not math.isclose(distance,minimum,rel_tol=2e-7,abs_tol=0)


def _mm(value):
    if value==0:return '0'
    if 1e-8<=abs(value)<1e7:return ('%.8f'%value).rstrip('0').rstrip('.')
    return '%.6g'%value


def _check_distribution(coordinates,axes,reference,spacing,minimum,mm_per_unit):
    minimum_mm=minimum*mm_per_unit
    if reference!='SELECTION' and _small(abs(spacing),minimum):
        raise BetterItemError('[BI-D001] Spacing is %s mm. Enter a positive or negative spacing with magnitude '
            'at least %s mm; zero spacing is not allowed.' % (_mm(spacing*mm_per_unit),_mm(minimum_mm)))
    conflicts=_coordinate_conflicts(coordinates,axes,minimum)
    if conflicts:
        raise BetterItemError('[BI-D002] Distribution order is ambiguous: object coordinates overlap or are closer '
            'than %s mm on the selected reference axes.\n%s\n'
            'Separate the listed objects on those axes by at least %s mm, then retry. '
            'Use a larger offset if Blender rounds it back to the same coordinate.' %
            (_mm(minimum_mm),'\n'.join(conflicts),_mm(minimum_mm)))


def _coordinate_conflicts(coordinates,axes,minimum):
    conflicts=[]
    for axis,enabled in enumerate(axes):
        if not enabled:continue
        ordered=sorted(coordinates,key=lambda name:(coordinates[name][axis],name))
        cluster=[]
        for left,right in zip(ordered,ordered[1:]):
            gap=coordinates[right][axis]-coordinates[left][axis]
            if _small(gap,minimum):
                if not cluster:cluster=[left]
                cluster.append(right)
            elif cluster:
                conflicts.append('%s: %s' % ('XYZ'[axis],', '.join('"%s"'%name for name in cluster)))
                cluster=[]
        if cluster:conflicts.append('%s: %s' % ('XYZ'[axis],', '.join('"%s"'%name for name in cluster)))
    return conflicts


def distribution_verifier(context,axes,reference,minimum_mm):
    reference=operation_reference(context) if reference=='AUTO' else reference
    # Capture axes/origin before movement, including selection-derived pivots.
    basis,origin,_=reference_frame(context,reference)
    minimum=minimum_mm/_mm_per_unit(context.scene)
    def verify(objects):
        coordinates={obj.name:np.linalg.solve(basis,np.asarray(obj.matrix_world.translation)-origin) for obj in objects}
        conflicts=_coordinate_conflicts(coordinates,axes,minimum)
        if conflicts:
            raise BetterItemError('[BI-D003] Blender coordinate precision would place these objects closer than '
                '%s mm after distribution:\n%s\nIncrease Spacing or reduce large coordinate/parent offsets. '
                'The operation was undone; no objects were repositioned.' % (_mm(minimum_mm),'\n'.join(conflicts)))
    return verify


def plan(context,objects,origins,axes,reference,*,mode='CENTER',spacing=None,minimum_mm=0.00001):
    reference=operation_reference(context) if reference=='AUTO' else reference
    if not any(axes):raise BetterItemError('[BI-A001] Select at least one arrangement axis: X, Y or Z.')
    distributing=spacing is not None
    required=1 if reference=='REFERENCE' else (3 if distributing and reference=='SELECTION' else 2)
    if len(objects)<required:
        raise BetterItemError('[BI-A003] Select at least %s objects for this operation.' % required)
    if reference not in {'SELECTION','KEY','REFERENCE'}:
        raise BetterItemError('[BI-A004] Choose a valid Location reference.')
    basis,origin,source=reference_frame(context,reference)
    try:coordinates={name:tuple(np.linalg.solve(basis,np.asarray(value,dtype=np.float64)-origin)) for name,value in origins.items()}
    except np.linalg.LinAlgError as exc:raise BetterItemError('[BI-A002] Reference axes are singular.') from exc
    active=context.active_object.name if context.active_object else None
    if reference=='KEY' and active not in origins:
        raise BetterItemError('[BI-A004] The key object must be active and selected.')
    mm_per_unit=_mm_per_unit(context.scene)
    if not math.isfinite(minimum_mm) or minimum_mm<=0:
        raise BetterItemError('[BI-D001] Minimum Distance must be greater than zero.')
    minimum=minimum_mm/mm_per_unit
    if distributing:
        if not math.isfinite(spacing):raise BetterItemError('[BI-D001] Enter a finite Spacing.')
        _check_distribution(coordinates,axes,reference,spacing,minimum,mm_per_unit)
    fixed=source.name if reference=='REFERENCE' and source is not None and source.name in origins else None
    working={name:value for name,value in coordinates.items() if name!=fixed}
    synthetic='\0Better Item Reference'
    if reference=='REFERENCE':
        if not working:raise BetterItemError('[BI-A003] Select at least one object other than the reference source.')
        working[synthetic]=(0.,0.,0.)
        planner_reference,key='KEY',synthetic
    else:planner_reference,key=reference,active
    if distributing:result=distribute_positions(working,axes,planner_reference,spacing,key)
    else:result=align_positions(working,axes,planner_reference,mode,key)
    result.pop(synthetic,None)
    if reference=='REFERENCE' and distributing and context.scene.better_item.arrange_on_axis and sum(axes)==1:
        for value in result.values():
            for i,enabled in enumerate(axes):
                if not enabled:value[i]=0.
    if fixed is not None:result[fixed]=coordinates[fixed]
    return {name:tuple(np.asarray(origins[name],dtype=np.float64)+basis @
        (np.asarray(result[name])-np.asarray(coordinates[name]))) for name in origins}
