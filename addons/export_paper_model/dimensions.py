"""Read-only dimensional annotations for the original unfolded mesh.

Coordinates arriving here are paper meters, after final placement. Multiplying
by the export scale recovers physical model lengths, including object scaling
and the scene's unit scale already applied by the upstream unfolder.
"""

from math import atan2, cos, sin, pi

FOOTER_HEIGHT = 0.018


def annotation_padding(text_size):
    return max(.008, text_size * 3.5)


def edge_records(mesh, island):
    """One record per UV segment; a seam on two islands occurs in both."""
    seen = set()
    boundary = set(island.boundary)
    for loop, uv in sorted(island.edges.items(), key=lambda item: (item[0].edge.index, item[0].face.index)):
        key = frozenset((uv.va, uv.vb))
        if key in seen:
            continue
        seen.add(key)
        edge = mesh.edges[loop.edge]
        if uv in boundary:
            kind = 'boundary'
        elif edge.freestyle:
            kind = 'freestyle'
        else:
            convex = edge.is_convex() != island.is_inside_out
            kind = 'fold_convex' if convex else 'fold_concave'
        yield {
            'edge_id': loop.edge.index + 1,
            'kind': kind,
            'a': uv.va.co.copy(), 'b': uv.vb.co.copy(),
            'angle': abs(edge.angle or 0),
            'has_tab': bool(uv.sticker),
        }


def edge_labels(exporter, mesh, island):
    """Fit labels to visible segments; omit dense or short edge labels."""
    if exporter.dimension_mode == 'NONE':
        return
    occupied = []
    height = exporter.dimension_text_size
    for row in edge_records(mesh, island):
        if exporter.profile_mode and row['kind'] != 'boundary':
            continue
        if row['kind'] != 'boundary':
            if exporter.dimension_mode == 'BOUNDARY':
                continue
            if row['kind'] != 'freestyle' and row['angle'] <= exporter.angle_epsilon:
                continue
        delta = row['b'] - row['a']
        label = f"{delta.length * 1000 * exporter.model_scale:.{exporter.dimension_precision}f}"
        width = len(label) * height * 0.62
        if delta.length < max(exporter.dimension_min_length, width + height):
            continue
        angle = atan2(delta.y, delta.x)
        if angle > pi / 2:
            angle -= pi
        elif angle < -pi / 2:
            angle += pi
        center = (row['a'] + row['b']) * 0.5
        center.x -= sin(angle) * height * 0.85
        center.y += cos(angle) * height * 0.85
        # Conservative axis-aligned extents of rotated text plus its white halo.
        half_x = abs(cos(angle)) * width / 2 + abs(sin(angle)) * height
        half_y = abs(sin(angle)) * width / 2 + abs(cos(angle)) * height
        box = (center.x-half_x, center.y-half_y, center.x+half_x, center.y+half_y)
        if any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1] for b in occupied):
            continue
        page_center = center + island.pos + exporter.margin
        if not (half_x <= page_center.x <= exporter.page_size.x-half_x
                and half_y <= page_center.y <= exporter.page_size.y-half_y):
            continue
        occupied.append(box)
        yield center, angle, label


def footer(exporter, page_number):
    """Paper-space calibration; never use the model scale to size the ruler."""
    x = exporter.margin.x
    # Margin.y includes the reserved footer; recover the original page margin.
    y = exporter.margin.y - FOOTER_HEIGHT
    width = min(0.050, exporter.page_size.x - 2 * x)
    lines = [((x, y + .008), (x + width, y + .008))]
    for fraction in (0, .5, 1):
        t = x + width * fraction
        lines.append(((t, y + .0065), (t, y + .0095)))
    labels = [
        (x, y + .014, f"Escala 1:{exporter.model_scale:g} | Cotas em mm reais | Pagina {page_number}"),
        (x, y + .002, f"{width*1000:g} mm no papel = {width*1000*exporter.model_scale:g} mm reais"),
    ]
    return lines, labels


def overall_dimensions(exporter, island):
    """Projected total width/height with extension lines and diagonal end ticks.

    Dimension values exclude gluing tabs. The lines are placed beyond the
    complete drawing (including tabs); the pagination reserves room for them.
    """
    points = [vertex.co for vertex in set(island.vertices.values())]
    lo_x, hi_x = min(v.x for v in points), max(v.x for v in points)
    lo_y, hi_y = min(v.y for v in points), max(v.y for v in points)
    factor = 1000 * exporter.model_scale
    precision = exporter.dimension_precision
    def point(x, y):
        v = points[0].copy()
        v.x, v.y = x, y
        return v
    gap = .003
    dim_x, dim_y = island.bounding_box.x + gap, island.bounding_box.y + gap
    lines = [(point(lo_x,dim_y),point(hi_x,dim_y)),
             (point(dim_x,lo_y),point(dim_x,hi_y))]
    lines.extend((point(x,hi_y+.0005),point(x,dim_y+.001)) for x in (lo_x,hi_x))
    lines.extend((point(hi_x+.0005,y),point(dim_x+.001,y)) for y in (lo_y,hi_y))
    for x,y in ((lo_x,dim_y),(hi_x,dim_y),(dim_x,lo_y),(dim_x,hi_y)):
        lines.append((point(x-.0008,y-.0008),point(x+.0008,y+.0008)))
    labels = [
        (point((lo_x+hi_x)/2,dim_y+.0012),0,
         f"I{island.abbreviation}: {(hi_x-lo_x)*factor:.{precision}f} mm"),
        (point(dim_x+.0012,(lo_y+hi_y)/2),pi/2,
         f"{(hi_y-lo_y)*factor:.{precision}f} mm"),
    ]
    return lines, labels
