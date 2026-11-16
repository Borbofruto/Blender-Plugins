"""Temporary feasibility probe; not an Edit Mode implementation in Better Item."""
import sys,json,traceback,tempfile
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Matrix,Vector,Euler
root=Path(__file__).parent;result={'passed':False,'blender':bpy.app.version_string,'checks':[]}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
coords=[(0,0,0),(2,0,0),(2,2,0),(0,2,0),(4,0,0),(6,0,0),(6,2,0),(4,2,0)]
objects=[]
for name,loc,rot,scale in [('Probe A',(3,-2,1),(.2,.3,.4),(1.2,.8,1.1)),('Probe B',(-4,3,2),(.3,-.2,.1),(-1,2,.7))]:
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(coords,[],[(0,1,2,3),(4,5,6,7)]);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=rot;obj.scale=scale;obj.select_set(True);objects.append(obj)
bpy.context.view_layer.objects.active=objects[0];bpy.context.view_layer.update();bpy.ops.object.mode_set(mode='EDIT')
assert len(bpy.context.objects_in_mode_unique_data)==2
for obj in bpy.context.objects_in_mode_unique_data:
 bm=bmesh.from_edit_mesh(obj.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
 for face in bm.faces:face.select_set(False)
 for edge in bm.edges:edge.select_set(False)
 for vertex in bm.verts:vertex.select=False
 face=bm.faces[0];face.select_set(True);bm.faces.active=face;bm.select_history.clear();bm.select_history.add(face);bm.select_flush_mode();bm.normal_update()
 assert isinstance(bm.select_history.active,bmesh.types.BMFace)
 ids=bm.verts.layers.int.new('_better_item_probe_id')
 for i,v in enumerate(bm.verts):v[ids]=i+1
 bmesh.update_edit_mesh(obj.data,loop_triangles=True,destructive=False)
result['checks'].append('Multi-object Edit Mode, active face, selection history and custom ID layers')
# Use full local/world matrices. Move selected vertices along a foreign frame.
axes=Euler((.4,-.3,.2)).to_matrix();delta=axes@Vector((1.5,0,0));before={};expected={}
for obj in bpy.context.objects_in_mode_unique_data:
 bm=bmesh.from_edit_mesh(obj.data);selected=[v for v in bm.verts if v.select]
 before[obj.name]=[tuple(v.co) for v in bm.verts]
 expected[obj.name]=[tuple(obj.matrix_world@v.co+delta) for v in selected]
 local=obj.matrix_world.inverted()@Matrix.Translation(delta)@obj.matrix_world
 bmesh.ops.transform(bm,matrix=local,verts=selected);bm.normal_update();bmesh.update_edit_mesh(obj.data,loop_triangles=True,destructive=False)
 for v,p in zip(selected,expected[obj.name]):assert np.allclose(obj.matrix_world@v.co,p,atol=2e-6)
 assert all(tuple(bm.verts[i].co)==before[obj.name][i] for i in range(4,8))
 assert len(bm.verts)==8 and len(bm.faces)==2
result['checks'].append('Foreign-axis transform under rotated, nonuniform and mirrored object matrices; untouched vertices preserved')
# Native Normal capture uses supported transform operators and active geometry.
obj=bpy.context.active_object;bm=bmesh.from_edit_mesh(obj.data);face=bm.faces.active
normal=(obj.matrix_world.to_3x3().inverted().transposed()@face.normal).normalized()
slot=bpy.context.scene.transform_orientation_slots[0];previous=slot.type
assert bpy.ops.transform.create_orientation(name='Study active face',use=True)=={'FINISHED'}
assert abs(abs(slot.custom_orientation.matrix.col[2].normalized().dot(normal))-1)<1e-5
assert bpy.ops.transform.delete_orientation()=={'FINISHED'}
slot.type=previous
result['checks'].append('Native orientation from active face and full transformed normal')
# Show why element index/custom IDs alone are not a topology-proof reference.
copy=bm.copy()
try:
 ids=copy.verts.layers.int.get('_better_item_probe_id');bmesh.ops.duplicate(copy,geom=list(copy.faces));values=[v[ids] for v in copy.verts]
 assert len(values)>len(set(values));result['duplicated_geometry_inherits_ids']=True
finally:copy.free()
result['checks'].append('Topology experiment: duplicate geometry inherits custom IDs; reference policy is required')
bpy.context.preferences.edit.use_global_undo=True
bpy.ops.ed.undo_push(message='Before Edit Mode probe')
for item in bpy.context.objects_in_mode_unique_data:
 bm=bmesh.from_edit_mesh(item.data)
 for v in bm.verts:
  if v.select:v.co.z+=.5
 bmesh.update_edit_mesh(item.data,loop_triangles=True,destructive=False)
bpy.ops.ed.undo_push(message='After Edit Mode probe');bpy.ops.ed.undo()
for name in ('Probe A','Probe B'):
 item=bpy.data.objects[name];bm=bmesh.from_edit_mesh(item.data);selected=[v for v in bm.verts if v.select]
 for v,p in zip(selected,expected[name]):assert np.allclose(item.matrix_world@v.co,p,atol=2e-6)
bpy.ops.ed.redo();result['checks'].append('Native Edit Mode Undo/Redo with BMesh handles reacquired')
bpy.ops.object.mode_set(mode='OBJECT')
with tempfile.TemporaryDirectory(dir=root) as temp:
 path=str(Path(temp)/'edit-study.blend');bpy.ops.wm.save_as_mainfile(filepath=path);bpy.ops.wm.open_mainfile(filepath=path)
 for name in ('Probe A','Probe B'):
  mesh=bpy.data.objects[name].data;assert mesh.attributes.get('_better_item_probe_id') is not None
result['checks'].append('Custom mesh data survives save/reopen')
result['passed']=True;Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('EDIT MODE API STUDY PASSED',json.dumps(result))
