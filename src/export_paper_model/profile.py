"""Extract a single planar cutting surface on a private, transformed BMesh."""
import bmesh


class ProfileError(ValueError):
    pass


def extract_profile(bm, matrix):
    # Ignore object placement, but respect rotation, scale, parent shear/mirrors.
    bmesh.ops.transform(bm, matrix=matrix.to_3x3().to_4x4(), verts=list(bm.verts))
    bm.normal_update()
    if not bm.faces:
        raise ProfileError('O perfil de corte requer uma malha com faces.')
    points=[v.co for v in bm.verts if v.link_faces]
    span=max(max(p[i] for p in points)-min(p[i] for p in points) for i in range(3))
    tolerance=span*1e-5
    # Sum parallel surface areas so a triangulated front is not mistaken for
    # a small face simply because an untriangulated side has a larger polygon.
    groups={}
    for face in bm.faces:
        if face.calc_area()<=0:
            continue
        normal=face.normal.copy().normalized()
        component=max(range(3),key=lambda i:abs(normal[i]))
        if normal[component]<0:
            normal.negate()
        key=tuple(round(c,5) for c in normal)
        if key not in groups:
            groups[key]=[normal,0.0]
        groups[key][1]+=face.calc_area()
    if not groups:
        raise ProfileError('A malha nao possui uma superficie plana com area valida.')
    normal=max(groups.values(),key=lambda group:group[1])[0]
    depth=[p.dot(normal) for p in points]
    low,high=min(depth),max(depth)
    thickness=high-low
    tangent=normal.orthogonal().normalized()
    across=normal.cross(tangent).normalized()
    def bounds(vertices,axis):
        coordinates=[p.dot(axis) for p in vertices]
        return min(coordinates),max(coordinates)
    source_bounds=[bounds(points,axis) for axis in (tangent,across)]
    other_extents=[]
    for direction,_area in groups.values():
        if abs(direction.dot(normal))<.01:
            lo,hi=bounds(points,direction)
            other_extents.append(hi-lo)
    main_min=min(other_extents or [b-a for a,b in source_bounds])
    if thickness>tolerance and thickness>=main_min-tolerance:
        raise ProfileError('A menor dimensao nao define uma chapa plana nesta malha. '
                           'Use Desdobramento completo ou exporte uma superficie plana separada.')
    parallel=[face for face in bm.faces if abs(face.normal.dot(normal))>.99999]
    def on_plane(face,plane):
        return all(abs(v.co.dot(normal)-plane)<=tolerance for v in face.verts)
    front=[face for face in parallel if on_plane(face,high)]
    if not front:
        raise ProfileError('Nao foi encontrada uma face plana externa para o perfil de corte.')
    front_points=[v.co for face in front for v in face.verts]
    for original,axis in zip(source_bounds,(tangent,across)):
        actual=bounds(front_points,axis)
        if any(abs(a-b)>tolerance for a,b in zip(original,actual)):
            raise ProfileError('A face externa nao cobre as duas dimensoes principais. '
                               'O perfil automatico requer uma chapa plana de espessura uniforme.')
    if thickness>tolerance:
        back=[face for face in parallel if on_plane(face,low)]
        front_area=sum(f.calc_area() for f in front)
        back_area=sum(f.calc_area() for f in back)
        if not back or abs(front_area-back_area)>max(front_area,back_area)*1e-4:
            raise ProfileError('As faces principais possuem recortes diferentes. '
                               'O perfil automatico requer recortes passantes, sem rebaixos.')
        if any(not on_plane(f,high) and not on_plane(f,low) for f in parallel):
            raise ProfileError('A malha possui planos intermediarios, como rebaixos ou furos cegos. '
                               'Separe a superficie que define o corte.')
    keep=set(front)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f not in keep],context='FACES')
    unused=[v for v in bm.verts if not v.link_faces]
    if unused:
        bmesh.ops.delete(bm,geom=unused,context='VERTS')
    for vertex in bm.verts:
        vertex.co-=normal*(vertex.co.dot(normal)-high)
    for face in bm.faces:
        if face.normal.dot(normal)<0:
            face.normal_flip()
    freestyle=bm.edges.layers.bool.get('freestyle_edge')
    for edge in bm.edges:
        edge.seam=False
        if freestyle:
            edge[freestyle]=False
    bm.normal_update()
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    return thickness
