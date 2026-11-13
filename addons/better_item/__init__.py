# SPDX-FileCopyrightText: 2026 Gabriel Webber do Nascimento
# SPDX-License-Identifier: GPL-3.0-or-later
bl_info={
    'name':'Better Item','author':'Gabriel Webber do Nascimento','version':(1,0,1),
    'blender':(5,0,0),'location':'View3D > Sidebar > Better Item',
    'description':'Linked transforms and origin-based alignment and distribution',
    'category':'Object',
}

import textwrap
import bpy
from bpy.app.handlers import persistent
from . import engine
from .math_core import BetterItemError,align_positions,distribute_positions

_field_errors={}
_groups=[('LOCATION','Posicao','Posicao local do objeto'),
         ('ROTATION','Rotacao','Angulos Euler do objeto'),
         ('SCALE','Escala','Escala local do objeto'),
         ('DIMENSIONS','Dimensoes','Dimensoes nativas do objeto')]
_references=[('SELECTION','Limites da selecao (origens)','Minimos e maximos das origens selecionadas, em coordenadas globais'),
             ('KEY','Objeto-chave (ativo)','Usar a origem do objeto ativo selecionado como referencia fixa')]


def _active(context):
    return context.active_object if context.mode=='OBJECT' else None


def _component(group,axis):
    def read_value(self):
        return engine.values(self.id_data,group)[axis]
    def write_value(self,value):
        obj=self.id_data
        try:
            engine.edit_component(obj,group,axis,value)
            _field_errors.pop(obj.as_pointer(),None)
        except BetterItemError as exc:
            _field_errors[obj.as_pointer()]=str(exc)
        if bpy.context.area:
            bpy.context.area.tag_redraw()
    args=dict(name='XYZ'[axis],get=read_value,set=write_value,precision=5,options=set())
    if group in {'LOCATION','DIMENSIONS'}:
        args['unit']='LENGTH'
    elif group=='ROTATION':
        args.update(unit='ROTATION',subtype='ANGLE')
    if group=='DIMENSIONS':
        args['min']=0
    return bpy.props.FloatProperty(**args)


class BetterItemObjectSettings(bpy.types.PropertyGroup):
    link_location:bpy.props.BoolVectorProperty(name='Vinculos da posicao',size=3,default=(False,False,False),options=set())
    link_rotation:bpy.props.BoolVectorProperty(name='Vinculos da rotacao',size=3,default=(False,False,False),options=set())
    link_scale:bpy.props.BoolVectorProperty(name='Vinculos da escala',size=3,default=(False,False,False),options=set())
    link_dimensions:bpy.props.BoolVectorProperty(name='Vinculos das dimensoes',size=3,default=(False,False,False),options=set())
    location_x:_component('LOCATION',0)
    location_y:_component('LOCATION',1)
    location_z:_component('LOCATION',2)
    rotation_x:_component('ROTATION',0)
    rotation_y:_component('ROTATION',1)
    rotation_z:_component('ROTATION',2)
    scale_x:_component('SCALE',0)
    scale_y:_component('SCALE',1)
    scale_z:_component('SCALE',2)
    dimensions_x:_component('DIMENSIONS',0)
    dimensions_y:_component('DIMENSIONS',1)
    dimensions_z:_component('DIMENSIONS',2)


class BetterItemSceneSettings(bpy.types.PropertyGroup):
    reference:bpy.props.EnumProperty(name='Referencia',items=_references,default='SELECTION',options=set())
    axes:bpy.props.BoolVectorProperty(name='Eixos globais',size=3,default=(True,False,False),options=set())
    spacing:bpy.props.FloatProperty(name='Passo entre origens',unit='LENGTH',default=.1,precision=5,
        description='Positivo distribui no sentido positivo; negativo, no negativo. A chave fica parada. '
                    'Objetos no lado contrario ao passo tem prioridade; cada grupo e ordenado por distancia a chave',options=set())


class BETTERITEM_OT_link_group(bpy.types.Operator):
    bl_idname='better_item.link_group'
    bl_label='Vincular ou desvincular XYZ'
    bl_description='Vincular os tres eixos deste grupo ou desfazer seus vinculos'
    bl_options={'REGISTER','UNDO'}
    group:bpy.props.EnumProperty(items=_groups)
    @classmethod
    def poll(cls,context):return _active(context) is not None and context.active_object.is_editable
    def execute(self,context):
        settings=context.active_object.better_item
        name=engine.GROUP_LINK[self.group]
        value=not all(getattr(settings,name))
        setattr(settings,name,(value,value,value))
        return {'FINISHED'}


class BETTERITEM_OT_clear_error(bpy.types.Operator):
    bl_idname='better_item.clear_error'
    bl_label='Fechar mensagem'
    def execute(self,context):
        if context.active_object:
            _field_errors.pop(context.active_object.as_pointer(),None)
        return {'FINISHED'}


class BETTERITEM_OT_align(bpy.types.Operator):
    bl_idname='better_item.align'
    bl_label='Alinhar origens'
    bl_description='Alinhar as origens dos objetos nos eixos globais escolhidos'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Eixos globais',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Referencia',items=_references,default='SELECTION')
    mode:bpy.props.EnumProperty(name='Alinhamento',items=[('MIN','Minimo','Menor coordenada'),
        ('CENTER','Centro','Centro entre as coordenadas extremas'),('MAX','Maximo','Maior coordenada')])
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=2
    def invoke(self,context,event):
        self.axes=context.scene.better_item.axes
        self.reference=context.scene.better_item.reference
        return self.execute(context)
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            key=context.active_object.name if context.active_object else None
            targets=align_positions(origins,self.axes,self.reference,self.mode,key)
            count=engine.apply_world_positions(objects,targets)
        except BetterItemError as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        self.report({'INFO'},'%s objeto(s) alinhado(s).' % count)
        return {'FINISHED'}


class BETTERITEM_OT_distribute(bpy.types.Operator):
    bl_idname='better_item.distribute'
    bl_label='Distribuir origens'
    bl_description='Distribuir pelas origens, por limites da selecao ou por passo assinado a partir da chave'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Eixos globais',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Referencia',items=_references,default='SELECTION')
    spacing:bpy.props.FloatProperty(name='Passo entre origens',unit='LENGTH',default=.1)
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=2
    def invoke(self,context,event):
        settings=context.scene.better_item
        self.axes=settings.axes
        self.reference=settings.reference
        self.spacing=settings.spacing
        return self.execute(context)
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            key=context.active_object.name if context.active_object else None
            targets=distribute_positions(origins,self.axes,self.reference,self.spacing,key)
            count=engine.apply_world_positions(objects,targets)
        except BetterItemError as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        self.report({'INFO'},'%s objeto(s) distribuido(s).' % count)
        return {'FINISHED'}


def _linked_rows(layout,obj,group,label,prefix,lock_name=None):
    box=layout.box()
    settings=obj.better_item
    link_name=engine.GROUP_LINK[group]
    links=getattr(settings,link_name)
    row=box.row(align=True)
    row.label(text=label)
    row.operator('better_item.link_group',text='',icon='LINKED' if all(links) else 'UNLINKED').group=group
    column=box.column(align=True)
    column.use_property_decorate=False
    for i,axis in enumerate('xyz'):
        row=column.row(align=True)
        field=row.row(align=True)
        native_locks=getattr(obj,lock_name) if lock_name else obj.lock_scale
        field.enabled=not native_locks[i] and obj.is_editable
        field.prop(settings,prefix+'_'+axis,text=axis.upper())
        row.prop(settings,link_name,index=i,text='',toggle=True,icon='LINKED' if links[i] else 'UNLINKED')
        if lock_name:
            row.prop(obj,lock_name,index=i,text='',emboss=False,icon='LOCKED' if native_locks[i] else 'UNLOCKED')
        if group!='DIMENSIONS':
            row.prop_decorator(obj,engine.GROUP_ATTR[group],index=i)
    return box


class BETTERITEM_PT_transform(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Transformacoes'
    def draw(self,context):
        layout=self.layout
        obj=_active(context)
        if obj is None:
            layout.label(text='Selecione um objeto no Modo Objeto.')
            return
        layout.label(text=obj.name,icon='OBJECT_DATA')
        error=_field_errors.get(obj.as_pointer())
        if error:
            box=layout.box()
            box.alert=True
            row=box.row()
            row.label(text='Alteracao cancelada',icon='ERROR')
            row.operator('better_item.clear_error',text='',icon='X')
            width=max(24,int((context.region.width-50)/7))
            for line in textwrap.wrap(error,width):box.label(text=line)
        _linked_rows(layout,obj,'LOCATION','Posicao (local)','location','lock_location')
        layout.prop(obj,'rotation_mode',text='Modo de rotacao')
        if obj.rotation_mode in engine.EULER_MODES:
            _linked_rows(layout,obj,'ROTATION','Rotacao','rotation','lock_rotation')
        else:
            box=layout.box()
            box.label(text='Rotacao')
            box.prop(obj,'lock_rotations_4d',text='Cadeados 4D')
            attribute='rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_axis_angle'
            for i,axis in enumerate(('W','X','Y','Z') if attribute=='rotation_quaternion' else ('Angulo','X','Y','Z')):
                row=box.row(align=True)
                locked=obj.lock_rotation_w if i==0 else obj.lock_rotation[i-1]
                field=row.row(align=True)
                field.enabled=not locked
                field.prop(obj,attribute,index=i,text=axis)
                row.prop(obj,'lock_rotation_w' if i==0 else 'lock_rotation',
                         **({} if i==0 else {'index':i-1}),text='',icon='LOCKED' if locked else 'UNLOCKED',emboss=False)
            box.label(text='Vinculo proporcional: use Euler.',icon='INFO')
        _linked_rows(layout,obj,'SCALE','Escala','scale','lock_scale')
        _linked_rows(layout,obj,'DIMENSIONS','Dimensoes','dimensions')


class BETTERITEM_PT_alignment(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Alinhar e distribuir'
    def draw(self,context):
        layout=self.layout
        settings=context.scene.better_item
        layout.label(text='Referencia pelas origens dos objetos.')
        layout.prop(settings,'reference')
        if settings.reference=='KEY':
            key=context.active_object
            layout.label(text='Chave: '+(key.name if key and key.select_get() else 'selecione o objeto ativo'),icon='OBJECT_DATA')
        row=layout.row(align=True)
        row.label(text='Eixos globais')
        for i,axis in enumerate('XYZ'):row.prop(settings,'axes',index=i,text=axis,toggle=True)
        box=layout.box()
        box.label(text='Alinhamento')
        row=box.row(align=True)
        if settings.reference=='KEY':
            row.operator('better_item.align',text='Alinhar a origem da chave').mode='CENTER'
        else:
            for mode,label in (('MIN','Minimo'),('CENTER','Centro'),('MAX','Maximo')):
                row.operator('better_item.align',text=label).mode=mode
        box=layout.box()
        box.label(text='Distribuicao')
        if settings.reference=='KEY':
            box.prop(settings,'spacing')
            box.label(text='Sinal do passo define o sentido.')
        else:
            box.label(text='Extremos fixos; passos iguais.')
        box.operator('better_item.distribute',text='Distribuir')


@persistent
def _clear_runtime(_unused):
    _field_errors.clear()


classes=(BetterItemObjectSettings,BetterItemSceneSettings,BETTERITEM_OT_link_group,
         BETTERITEM_OT_clear_error,BETTERITEM_OT_align,BETTERITEM_OT_distribute,
         BETTERITEM_PT_transform,BETTERITEM_PT_alignment)


def register():
    try:
        for cls in classes:
            if not cls.is_registered:bpy.utils.register_class(cls)
        if not hasattr(bpy.types.Object,'better_item'):
            bpy.types.Object.better_item=bpy.props.PointerProperty(type=BetterItemObjectSettings)
        if not hasattr(bpy.types.Scene,'better_item'):
            bpy.types.Scene.better_item=bpy.props.PointerProperty(type=BetterItemSceneSettings)
        if _clear_runtime not in bpy.app.handlers.load_post:bpy.app.handlers.load_post.append(_clear_runtime)
    except Exception:
        unregister()
        raise


def unregister():
    if _clear_runtime in bpy.app.handlers.load_post:bpy.app.handlers.load_post.remove(_clear_runtime)
    _field_errors.clear()
    for owner in (bpy.types.Scene,bpy.types.Object):
        if hasattr(owner,'better_item'):del owner.better_item
    for cls in reversed(classes):
        if cls.is_registered:bpy.utils.unregister_class(cls)
