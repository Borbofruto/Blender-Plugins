# SPDX-License-Identifier: GPL-3.0-or-later
"""Distribution contracts: explicit sources, point placement and interval fitting."""
import math
import bpy
import numpy as np
from mathutils import Matrix
from . import arrange,engine,frames,references,placement,native_refs,geometry_arrange
from .math_core import BetterItemError,ReferencePending
from .transform_view import has_surface_geometry

METHODS=[('OFFSET','Offset','Set a signed spacing using the shared reference axes'),
    ('ENDPOINT','Endpoint','Fit the selection between two references')]
PATHS=[('SEGMENT','Between Points','The Start-to-End segment defines the direction; shared Orientation is unused'),
    ('AXIS','Reference Axis','Project End onto one selected reference axis through Start')]
POINT_MODES=[('MANUAL','Manual','World-space coordinates','EDITMODE_HLT'),
    ('GLOBAL','Global','World origin','WORLD'),('OBJECT','Object','A specific object origin','OBJECT_DATA'),
    ('FRAME','Frame','Only the Location component of a saved frame','EMPTY_AXIS'),
    ('CURSOR','3D Cursor','Current 3D Cursor position','PIVOT_CURSOR'),
    ('ACTIVE','Active Object','Capture the active object as a fixed operation anchor','PIVOT_ACTIVE')]


def changed(self,context):
    arrange.clear_error()
    from . import distribution_preview
    distribution_preview.update(context)


def _frame_items(self,context):return frames.frame_items(self,context)


class BetterItemPointReference(bpy.types.PropertyGroup):
    mode:bpy.props.EnumProperty(name='Location',items=[(*item,i) for i,item in enumerate(POINT_MODES)],default='MANUAL',options=set(),update=changed)
    object:bpy.props.PointerProperty(name='Object',type=bpy.types.Object,update=changed)
    frame:bpy.props.EnumProperty(name='Frame',items=_frame_items,options=set(),update=changed)
    position:bpy.props.FloatVectorProperty(name='Position',size=3,subtype='TRANSLATION',unit='LENGTH',default=(1,0,0),options=set(),update=changed)


def point(context,source):
    mode=source.mode;obj=None
    if mode=='MANUAL':value=source.position
    elif mode=='GLOBAL':value=(0,0,0)
    elif mode=='CURSOR':value=context.scene.cursor.location
    elif mode in {'OBJECT','ACTIVE'}:
        obj=source.object if mode=='OBJECT' else context.active_object
        if obj is None:raise ReferencePending('[BI-F002] Choose an object for this endpoint.')
        if obj.name not in context.scene.objects:raise ReferencePending('[BI-F002] Choose an endpoint object in this scene.')
        value=obj.matrix_world.translation
    elif mode=='FRAME':
        frame=frames.find(context.scene,source.frame)
        value=frames.frame_origin(frame,context);obj=frames.position_reference_object(frame,context.scene)
    else:raise ReferencePending('[BI-F002] Choose an endpoint Location source.')
    result=np.asarray(value,dtype=np.float64).copy()
    if obj is not None and obj.name not in context.scene.objects:raise ReferencePending('[BI-F002] Choose an endpoint source object linked to this scene.')
    if not np.isfinite(result).all():raise BetterItemError('[BI-E001] Endpoint coordinates must be finite.')
    return result,obj


def draw_point(layout,source,label):
    row=layout.split(factor=.52,align=True);row.label(text=label+':',icon='OBJECT_ORIGIN');row.prop(source,'mode',text='')
    if source.mode=='OBJECT':references._source_row(layout,'Object').prop(source,'object',text='')
    elif source.mode=='FRAME':references._source_row(layout,'Frame').prop(source,'frame',text='')
    elif source.mode=='MANUAL':
        column=layout.column(align=True)
        for i,axis in enumerate('XYZ'):references._source_row(column,axis,'└' if i==2 else '├').prop(source,'position',index=i,text='')


def _start(context):
    settings=context.scene.better_item
    if settings.distribution_start_override:return point(context,settings.distribution_start)
    value,source=references.origin(context,settings,context.active_object,True)
    if source is None and references.location_kind(context,settings,True)=='ACTIVE_ELEMENT':source=context.active_object
    return np.asarray(value,dtype=np.float64).copy(),source


def _line_axes(direction):
    """A deterministic measurement frame; X follows the line, roll is not applied."""
    x=np.asarray(direction,dtype=np.float64)
    seed=np.eye(3)[int(np.argmin(np.abs(x)))]
    y=np.cross(seed,x);y/=np.linalg.norm(y);z=np.cross(x,y)
    return Matrix(np.column_stack((x,y,z)))


def _order(values,start,direction,minimum):
    names=sorted(values,key=lambda name:(values[name],name))
    for left,right in zip(names,names[1:]):
        if arrange._small(values[right]-values[left],minimum):
            raise BetterItemError('[BI-D002] "%s" and "%s" do not define a unique distribution order. Separate their placement points along this direction, then retry.'%(left,right))
    return sorted(values,key=lambda name:(0 if (values[name]-start)*direction<0 else 1,abs(values[name]-start),name))


def _endpoint_order(points,start,direction,minimum):
    # Endpoint has no pre-existing axis: sources can all lie in a plane
    # perpendicular to the new line. Spatial distance still defines an order.
    ranks={name:(0 if np.dot(value-start,direction)<0 else 1,float(np.linalg.norm(value-start))) for name,value in points.items()}
    order=sorted(ranks,key=lambda name:(*ranks[name],name))
    for left,right in zip(order,order[1:]):
        if ranks[left][0]==ranks[right][0] and arrange._small(abs(ranks[left][1]-ranks[right][1]),minimum):
            raise BetterItemError('[BI-D002] "%s" and "%s" have the same distance from Start, so Endpoint order is ambiguous. Move one placement point slightly farther from Start.'%(left,right))
    return order


def _state(objects):
    return {obj.name:(np.asarray(obj.matrix_world.to_3x3(),dtype=np.float64).copy(),tuple(obj.scale),tuple(obj.delta_scale)) for obj in objects}


def _verify_state(objects,state):
    for obj in objects:
        linear,scale,delta=state[obj.name]
        if tuple(obj.scale)!=scale or tuple(obj.delta_scale)!=delta or not np.allclose(np.asarray(obj.matrix_world.to_3x3()),linear,rtol=8*np.finfo(np.float32).eps,atol=0):
            raise BetterItemError('[BI-G005] Rotation or Scale of "%s" changes with Location. Disable the dependent transform before distributing.'%obj.name)


def _tolerance(*values):
    # Match source float32 storage, not an arbitrary fixed scene-unit epsilon.
    return 64*np.finfo(np.float32).eps*max(*(abs(float(v)) for v in values),np.finfo(np.float32).tiny)


def _interval_tolerance(count,*values):
    # Relative spacing accumulated across N float32 placement slots, with no
    # absolute floor that could label collapsed/tiny intervals as uniform.
    return max(64,4*count)*np.finfo(np.float32).eps*max(*(abs(float(v)) for v in values),np.finfo(np.float32).tiny)


def _display_mm(context,value):
    mm=value*arrange._mm_per_unit(context.scene)
    if mm and (abs(mm)<.001 or abs(mm)>=1e6):return '%.4g mm'%mm
    return ('%.3f'%mm).rstrip('0').rstrip('.')+' mm'


def endpoint_plan(context,objects,*,basis='ORIGINS',path='SEGMENT',axes=(True,False,False),minimum_mm=.00001):
    if len(objects)<2:raise ReferencePending('[BI-A003] Select at least two objects for Endpoint distribution.')
    start,start_obj=_start(context);end,end_obj=point(context,context.scene.better_item.distribution_end)
    selected={obj.name for obj in objects}
    # A selected endpoint object occupies the first/last slot using the chosen
    # placement point. Native transforms remain fixed, including offset origins.
    for source,is_start in ((start_obj,True),(end_obj,False)):
        if source is not None and source.name in selected and basis!='ORIGINS' and has_surface_geometry(source):
            value=np.asarray(source.matrix_world.translation)+placement.offset(source,'BOUNDS_CENTER' if basis=='GEOMETRY' else basis)
            if is_start:start=value
            else:end=value
    if path=='AXIS':
        if sum(axes)!=1:raise ReferencePending('[BI-A001] Select exactly one reference axis for Endpoint / Reference Axis.')
        axis=next(i for i,value in enumerate(axes) if value)
        vector=np.asarray(references.axes(context,context.scene.better_item,context.active_object,True).col[axis],dtype=np.float64)
        vector/=np.linalg.norm(vector);end=start+vector*np.dot(end-start,vector)
    elif path!='SEGMENT':raise BetterItemError('[BI-E001] Choose a valid Endpoint path.')
    distance=float(np.linalg.norm(end-start))
    minimum=minimum_mm/arrange._mm_per_unit(context.scene)
    if not math.isfinite(minimum) or minimum<=0:raise BetterItemError('[BI-D001] Solver minimum separation must be positive.')
    if not math.isfinite(distance) or distance<minimum:raise BetterItemError('[BI-E001] Start and End are coincident or too close. Separate the endpoint references.')
    direction=(end-start)/distance;measurement_axes=_line_axes(direction)
    origins={obj.name:np.asarray(obj.matrix_world.translation,dtype=np.float64).copy() for obj in objects}
    anchors={obj.name for obj in (start_obj,end_obj) if obj is not None and obj.name in origins}
    offsets={obj.name:np.zeros(3) if obj.name in anchors and not has_surface_geometry(obj) else placement.offset(obj,basis,measurement_axes if basis=='GEOMETRY' else None) for obj in objects}
    points={name:origins[name]+offset for name,offset in offsets.items()}
    if start_obj is not None and start_obj==end_obj:raise BetterItemError('[BI-E001] Start and End cannot use the same fixed object.')
    values={name:float(np.dot(value-start,direction)) for name,value in points.items()}
    moving={name:value for name,value in values.items() if name not in anchors}
    order=_endpoint_order({name:points[name] for name in moving},start,direction,minimum)
    occupied=anchors if basis!='GEOMETRY' else {obj.name for obj in objects if obj.name in anchors and has_surface_geometry(obj)}
    chain=([start_obj.name] if start_obj is not None and start_obj.name in occupied else [])+order+([end_obj.name] if end_obj is not None and end_obj.name in occupied else [])
    if len(chain)<2:raise ReferencePending('[BI-A003] Select objects between the endpoint anchors.')
    if not moving:raise ReferencePending('[BI-A003] Both selected objects are fixed endpoints. Select an intermediate target.')
    targets={name:tuple(value) for name,value in origins.items()};expected={}
    if basis=='GEOMETRY':
        extents={obj.name:placement.intervals(obj,measurement_axes) for obj in objects if obj.name in chain}
        widths={name:float(high[0]-low[0]) for name,(low,high) in extents.items()}
        # A selected anchor occupies its measured interval, rather than forcing
        # its center/origin to a different geometric point.
        low=float(np.dot(origins[chain[0]]-start,direction)+extents[chain[0]][0][0]) if chain[0] in anchors else 0.
        high=float(np.dot(origins[chain[-1]]-start,direction)+extents[chain[-1]][1][0]) if chain[-1] in anchors else distance
        gap=(high-low-sum(widths[name] for name in chain))/(len(chain)-1)
        if gap < -_tolerance(high-low,*widths.values()):
            missing=-gap*(len(chain)-1)*arrange._mm_per_unit(context.scene)
            raise BetterItemError('[BI-E002] The geometry does not fit between these limits; %.6g mm more space is needed. Move the endpoints or choose a point placement basis.'%missing)
        gap=max(0.,gap);boundary=low
        for name in chain:
            left,right=extents[name];center=boundary+widths[name]*.5
            if name not in anchors:targets[name]=tuple(start+direction*center-offsets[name])
            expected[name]=(boundary,boundary+widths[name]);boundary+=widths[name]+gap
    else:
        low=values[chain[0]] if chain[0] in anchors else 0.
        high=values[chain[-1]] if chain[-1] in anchors else distance
        if high-low<minimum:raise BetterItemError('[BI-E001] The anchor placement points are coincident or reversed. Check the placement basis and endpoint references.')
        gap=(high-low)/(len(chain)-1)
        for i,name in enumerate(chain):
            coordinate=low+i*gap
            if name not in anchors:targets[name]=tuple(start+direction*coordinate-offsets[name])
            expected[name]=coordinate
    state=_state(objects)
    source_positions={obj:tuple(obj.matrix_world.translation) for obj in (start_obj,end_obj) if obj is not None}
    def verify(actual):
        _verify_state(actual,state)
        measured_intervals={}
        for source,position in source_positions.items():
            if not engine._position_matches(source,position):raise BetterItemError('[BI-G004] An endpoint moves with a distributed target. Use an independent endpoint or detach that dependency.')
        for obj in actual:
            if obj.name in anchors:
                if basis=='GEOMETRY' and obj.name in expected:
                    left,right=placement.intervals(obj,measurement_axes);coordinate=float(np.dot(np.asarray(obj.matrix_world.translation)-start,direction))
                    measured_intervals[obj.name]=(coordinate+left[0],coordinate+right[0])
                continue
            new_offset=placement.offset(obj,basis,measurement_axes if basis=='GEOMETRY' else None)
            width=float(np.linalg.norm(offsets[obj.name]))
            if np.linalg.norm(new_offset-offsets[obj.name])>_tolerance(width,distance):
                raise BetterItemError('[BI-G003] Geometry of "%s" changes as it moves. Apply or disable position-dependent geometry before distributing.'%obj.name)
            current=np.asarray(obj.matrix_world.translation,dtype=np.float64)
            if basis=='GEOMETRY':
                left,right=placement.intervals(obj,measurement_axes)
                coordinate=float(np.dot(current-start,direction))
                measured_intervals[obj.name]=(coordinate+left[0],coordinate+right[0])
                if max(abs(coordinate+left[0]-expected[obj.name][0]),abs(coordinate+right[0]-expected[obj.name][1]))>_tolerance(distance):
                    raise BetterItemError('[BI-E003] Endpoint geometry could not retain its planned bounds at native coordinate precision. Reduce large offsets.')
            else:
                wanted=start+direction*expected[obj.name]
                budget=_tolerance(distance,float(np.linalg.norm(wanted)))+float(np.linalg.norm(engine._world_roundoff(obj,targets[obj.name])))
                if np.linalg.norm(current+new_offset-wanted)>budget:
                    raise BetterItemError('[BI-E003] The placement point of "%s" cannot retain its segment position (residual %.9g; budget %.9g Blender units). Reduce large offsets.'%(obj.name,np.linalg.norm(current+new_offset-wanted),budget))
        if basis=='GEOMETRY':
            for previous,name in zip(chain,chain[1:]):
                actual_gap=measured_intervals[name][0]-measured_intervals[previous][1]
                if gap>0 and actual_gap<=0 or abs(actual_gap-gap)>_interval_tolerance(len(chain),widths[name],widths[previous],gap):
                    raise BetterItemError('[BI-E003] The gap before "%s" cannot be resolved at native coordinate precision. Reduce large offsets or increase the endpoint interval.'%name)
    return targets,verify,{'spacing':gap,'order':chain,'anchors':anchors,'start':tuple(start),'end':tuple(end)}


def offset_plan(context,objects,*,basis,axes,spacing,minimum_mm):
    if basis=='GEOMETRY':return (*geometry_arrange.plan(context,objects,{o.name:tuple(o.matrix_world.translation) for o in objects},axes,'REFERENCE',spacing=spacing,minimum_mm=minimum_mm,preserve_transverse=True),{})
    if not any(axes):raise ReferencePending('[BI-A001] Select at least one distribution axis.')
    if not math.isfinite(spacing):raise BetterItemError('[BI-D001] Enter a finite spacing.')
    matrix,origin,source=arrange.reference_frame(context,'REFERENCE');inverse=np.linalg.inv(matrix)
    origins={obj.name:np.asarray(obj.matrix_world.translation,dtype=np.float64).copy() for obj in objects}
    fixed=source.name if source is not None and source.name in origins else None
    offsets={obj.name:np.zeros(3) if obj.name==fixed and not has_surface_geometry(obj) else placement.offset(obj,basis) for obj in objects}
    coordinates={name:inverse@(value+offsets[name]-origin) for name,value in origins.items()}
    anchor=inverse@placement.offset(source,basis) if source is not None and basis!='ORIGINS' and has_surface_geometry(source) else np.zeros(3)
    minimum=minimum_mm/arrange._mm_per_unit(context.scene)
    if not math.isfinite(minimum) or minimum<=0:raise BetterItemError('[BI-D001] Solver minimum separation must be positive.')
    arrange._check_distribution(coordinates,axes,'REFERENCE',spacing,minimum,arrange._mm_per_unit(context.scene))
    moving=[name for name in origins if name!=fixed]
    if not moving:raise ReferencePending('[BI-A003] Select an object other than the reference anchor.')
    desired={name:value.copy() for name,value in coordinates.items()}
    orders={}
    for axis,enabled in enumerate(axes):
        if not enabled:continue
        order=_order({name:coordinates[name][axis] for name in moving},anchor[axis],spacing,minimum)
        orders[axis]=order
        for i,name in enumerate(order,1):desired[name][axis]=anchor[axis]+i*spacing
    targets={name:tuple(origin+matrix@desired[name]-offsets[name]) if name!=fixed else tuple(origins[name]) for name in origins}
    state=_state(objects);source_position=tuple(source.matrix_world.translation) if source else None
    def verify(actual):
        _verify_state(actual,state)
        if source and not engine._position_matches(source,source_position):raise BetterItemError('[BI-G004] The reference follows a moved target. Use an independent anchor.')
        for obj in actual:
            if obj.name==fixed:continue
            offset=placement.offset(obj,basis)
            if np.linalg.norm(offset-offsets[obj.name])>_tolerance(np.linalg.norm(offsets[obj.name]),spacing):
                raise BetterItemError('[BI-G003] The placement geometry changes with Location. Disable the dependent geometry before distributing.')
        points={obj.name:inverse@(np.asarray(obj.matrix_world.translation)+placement.offset(obj,basis)-origin) for obj in actual if obj.name!=fixed}
        for axis,order in orders.items():
            previous=anchor[axis]
            for name in order:
                interval=points[name][axis]-previous;previous=points[name][axis]
                if abs(interval-spacing)>_interval_tolerance(len(order),spacing):
                    raise BetterItemError('[BI-E003] The requested point spacing cannot be retained at native coordinate precision. Reduce large source/object offsets or increase Spacing.')
    return targets,verify,{'spacing':spacing,'anchors':{fixed} if fixed else set()}


def plan(context,objects,*,basis=None,method=None,path=None,axes=None,spacing=None,minimum_mm=None):
    if context.mode!='OBJECT':raise ReferencePending('[BI-A003] Switch to Object Mode to distribute whole objects.')
    s=context.scene.better_item
    args=dict(basis=basis or s.distribution_mode,axes=tuple(s.axes) if axes is None else tuple(axes),
        minimum_mm=s.minimum_distance_mm if minimum_mm is None else minimum_mm)
    method=method or s.distribution_method
    if method=='ENDPOINT':return endpoint_plan(context,objects,path=path or s.endpoint_path,**args)
    if method!='OFFSET':raise BetterItemError('[BI-E001] Choose Offset or Endpoint.')
    return offset_plan(context,objects,spacing=s.spacing if spacing is None else spacing,**args)


def apply(context,objects,**kwargs):
    settings=context.scene.better_item
    settings['distribution_schema']=1
    requested=kwargs.get('spacing',settings.spacing)
    if (kwargs.get('method') or settings.distribution_method)=='OFFSET' and math.isfinite(requested) and requested:
        settings['distribution_last_sign']=-1 if requested<0 else 1
    context.view_layer.update();targets,verify,info=plan(context,objects,**kwargs)
    return engine.apply_world_positions(objects,targets,verify=verify),info


def inspect_spacing(context,objects):
    """Measure against the same plan, including the reference-to-first interval."""
    if not objects:return 'EMPTY',None
    try:
        s=context.scene.better_item
        if s.distribution_method=='ENDPOINT':
            targets,_,info=plan(context,objects)
            uniform=all(engine._position_matches(obj,targets[obj.name]) for obj in objects)
            return ('UNIFORM' if uniform else 'MIXED'),info.get('spacing') if uniform else None
        if not any(s.axes):return 'UNAVAILABLE',None
        matrix,origin,source=arrange.reference_frame(context,'REFERENCE')
        physical=s.distribution_mode=='GEOMETRY'
        axes=matrix/np.linalg.norm(matrix,axis=0) if physical else matrix
        transform=axes.T if physical else np.linalg.inv(axes)
        fixed=source.name if source and source in objects else None;gaps=[]
        offsets={obj.name:np.zeros(3) if physical or obj.name==fixed and not has_surface_geometry(obj) else placement.offset(obj,s.distribution_mode) for obj in objects}
        values={obj.name:transform@(np.asarray(obj.matrix_world.translation)+offsets[obj.name]-origin) for obj in objects}
        sign=-1 if s.spacing<0 or s.spacing==0 and s.distribution_last_sign<0 else 1
        for axis,enabled in enumerate(s.axes):
            if not enabled:continue
            if physical:
                anchor=np.asarray(source.matrix_world.translation)-origin if source else np.zeros(3)
                if source and has_surface_geometry(source):
                    left,right=placement.intervals(source,Matrix(matrix));previous=float((transform@anchor)[axis]+(right if sign>0 else left)[axis])
                else:previous=float((transform@anchor)[axis])
                occupied=[]
                for obj in objects:
                    if obj.name==fixed:continue
                    left,right=placement.intervals(obj,Matrix(matrix))
                    center=float((transform@(np.asarray(obj.matrix_world.translation)-origin))[axis])
                    occupied.append((center+(left if sign>0 else right)[axis],center+(right if sign>0 else left)[axis]))
                for edge,far in sorted(occupied,key=lambda interval:sign*interval[0]):
                    gaps.append(sign*(edge-previous));previous=far
            else:
                previous=float((transform@placement.offset(source,s.distribution_mode))[axis]) if source and has_surface_geometry(source) else 0.
                order=_order({name:value[axis] for name,value in values.items() if name!=fixed},previous,sign,0)
                for name in order:gaps.append(sign*(values[name][axis]-previous));previous=values[name][axis]
        if not gaps:return 'EMPTY',None
        first=gaps[0]
        uniform=all(abs(value-first)<=_interval_tolerance(len(objects),value,first) for value in gaps)
        return ('UNIFORM',sign*first) if uniform else ('MIXED',None)
    except BetterItemError:return 'UNAVAILABLE',None


def draw(layout,context):
    from . import distribution_preview
    settings=context.scene.better_item;box=layout.box();box.label(text='Distribution')
    box.row(align=True).prop(settings,'distribution_method',expand=True)
    row=box.split(factor=.42,align=True);row.label(text='Placement:');row.prop(settings,'distribution_mode',text='')
    live=distribution_preview.active(context.scene)
    if settings.distribution_legacy_range and settings.distribution_method=='OFFSET':
        box.label(text='Legacy selection-bound distribution.',icon='INFO')
        box.label(text='Switch Method to use explicit references.')
    if settings.distribution_method=='ENDPOINT':
        box.prop(settings,'endpoint_path',text='Path')
        box.prop(settings,'distribution_start_override')
        if settings.distribution_start_override:draw_point(box,settings.distribution_start,'Start')
        else:box.label(text='Start: shared Location reference.')
        draw_point(box,settings.distribution_end,'End')
        if settings.endpoint_path=='SEGMENT':box.label(text='Start → End defines the direction.')
        else:box.label(text='End is projected onto one Move axis.')
        box.label(text='Endpoint objects stay fixed.')
        status,value=inspect_spacing(context,list(context.selected_objects))
        if status=='UNIFORM' and value is not None:box.label(text=('Gap: ' if settings.distribution_mode=='GEOMETRY' else 'Point interval: ')+_display_mm(context,value))
        else:box.label(text='Spacing is derived from the endpoints.')
    else:
        status,value=inspect_spacing(context,list(context.selected_objects))
        if status=='UNIFORM':box.label(text='Current: '+_display_mm(context,value))
        elif status=='MIXED':
            box.label(text='Mixed spacing.',icon='INFO');box.label(text='Edit Spacing to make it uniform.')
        elif status=='UNAVAILABLE':box.label(text='Complete references to measure spacing.',icon='INFO')
        box.prop(settings,'spacing_view' if live else 'spacing',text='Spacing')
        box.label(text='Sign sets direction.'+(' Zero allows contact.' if settings.distribution_mode=='GEOMETRY' else ''))
    row=box.row()
    row.enabled=live or (not settings.distribution_legacy_range and not distribution_preview.contextual_start(context))
    row.prop(settings,'distribution_live',text='Live')
    if not live:
        row=box.row();row.enabled=bool(context.selected_objects)
        row.operator('better_item.distribute',text='Distribute')
    if distribution_preview.contextual_start(context):box.label(text='Capture Location to a Frame for Live.',icon='INFO')


def migrate():
    """Preserve old saved selection-range operations; new choices are explicit."""
    if not hasattr(bpy.data,'scenes'):return  # addon_utils uses a restricted registration context.
    for scene in bpy.data.scenes:
        settings=scene.better_item
        if 'distribution_last_sign' not in settings and settings.spacing:
            settings['distribution_last_sign']=-1 if settings.spacing<0 else 1
        if settings.get('distribution_schema',0)>=1:continue
        if bpy.data.filepath and settings.get('arrange_origin') is not None:
            try:settings.distribution_legacy_range=references.location_kind(bpy.context,settings,True)=='BOUNDING_BOX_CENTER'
            except BetterItemError:pass
        settings['distribution_schema']=1
