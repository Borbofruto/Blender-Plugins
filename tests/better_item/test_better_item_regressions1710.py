"""Display, diagnostic and observer regressions found after 1.7.9 (1.7.10).

- F7: an open mesh with Volume placement and complete references reported
  "Complete references to measure spacing". The inspection swallowed BI-P003.
- P1: Transform fields declared precision 3 for every group; the native fields
  use 5 for Location, Rotation and Dimensions (Scale stays at 3).
- F6: BI-F006 was drawn under the title "Reference unavailable".
- F8: the observer's recovery redraw read window.scene outside any handler.

Headless-safe: no Undo, no mouse, no timings. The panel text is exercised through
recording stand-ins for the layout; real drawing remains a manual/GUI check.
"""
import sys
import textwrap
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import bmesh

try:
    import addon_utils
    addon_utils.enable('better_item')
except Exception:
    pass
import better_item
if not hasattr(bpy.types.Object, 'better_item'):
    better_item.register()
from better_item import distribution as d, diagnostics, native_refs
from better_item.math_core import BetterItemError, ReferencePending

ctx = bpy.context
results = {}


def reset():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    s = ctx.scene.better_item
    s.reference_location = 'GLOBAL'
    d.clear_inspection()


def cube(name, x, open_mesh=False):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.)
    if open_mesh:
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[0]], context='FACES_ONLY')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    ctx.scene.collection.objects.link(obj)
    obj.location = (x, 0, 0)
    return obj


def select(objects):
    for obj in list(ctx.scene.objects):
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    ctx.view_layer.objects.active = objects[0]
    ctx.view_layer.update()


def scene_setup(mode):
    s = ctx.scene.better_item
    s.distribution_method = 'OFFSET'
    s.axes = (True, False, False)
    s.distribution_mode = mode
    return s


def status():
    return d.inspect_spacing(ctx, list(ctx.selected_objects))


def open_mesh_volume():
    reset()
    objects = [cube('A', 0), cube('B', 3, open_mesh=True), cube('C', 7)]
    select(objects)
    scene_setup('VOLUME')
    state, message = status()
    assert state == 'INVALID', (state, message)
    assert 'closed' in message and 'Surface' in message, message
    # The operation refuses the same selection with the same diagnostic.
    try:
        d.plan(ctx, objects)
    except BetterItemError as exc:
        assert 'BI-P003' in str(exc), str(exc)
    else:
        raise AssertionError('Volume placement of an open mesh was not refused')
    # Bases that do not need a closed volume are unaffected.
    for mode in ('SURFACE', 'GEOMETRY', 'BOUNDS_CENTER', 'ORIGINS'):
        scene_setup(mode)
        d.clear_inspection()
        state, _ = status()
        assert state in {'UNIFORM', 'MIXED'}, (mode, state)
    # Closing the mesh clears the diagnostic once the inspection is recomputed.
    scene_setup('VOLUME')
    objects[1].data.clear_geometry()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.)
    bm.to_mesh(objects[1].data)
    bm.free()
    ctx.view_layer.update()
    d.clear_inspection()
    state, message = status()
    assert state in {'UNIFORM', 'MIXED'}, (state, message)
    results['open_mesh_volume'] = 'an open mesh in Volume reports its geometry diagnostic; other bases and closed meshes are unchanged'


def incomplete_reference_unchanged():
    reset()
    objects = [bpy.data.objects.new('E%d' % i, None) for i in range(3)]
    for index, obj in enumerate(objects):
        ctx.scene.collection.objects.link(obj)
        obj.location = (index * 3, 0, 0)
    select(objects)
    s = scene_setup('ORIGINS')
    for kind in ('OBJECT', 'FRAME'):
        s.reference_location = kind
        d.clear_inspection()
        state, value = status()
        assert (state, value) == ('UNAVAILABLE', None), (kind, state, value)
    results['incomplete_reference_unchanged'] = 'a missing reference object or Frame still reports UNAVAILABLE'


def unmeasurable_classification():
    for code in ('BI-P001', 'BI-P002', 'BI-P003', 'BI-G001', 'BI-M005'):
        assert d._unmeasurable_geometry(BetterItemError('[%s] x' % code)), code
    for code in ('BI-F002', 'BI-F001', 'BI-E001', 'BI-D001', 'BI-T001', 'BI-A003'):
        assert not d._unmeasurable_geometry(BetterItemError('[%s] x' % code)), code
    assert not d._unmeasurable_geometry(ReferencePending('[BI-F002] choose'))
    results['unmeasurable_classification'] = 'only geometry codes become INVALID; reference, spacing and selection codes keep UNAVAILABLE'


class Recorder:
    """Stand-in for a Blender layout that records the labels drawn."""
    def __init__(self, labels):
        self.labels = labels
        self.alert = False

    def box(self):
        return Recorder(self.labels)

    def row(self, align=False):
        return Recorder(self.labels)

    def column(self, align=False):
        return Recorder(self.labels)

    def label(self, text='', icon='NONE'):
        self.labels.append(text)

    def operator(self, *args, **kwargs):
        return None

    def prop(self, *args, **kwargs):
        return None


class Owner:
    show_diagnostic_details = False


def draw_unmeasurable():
    labels = []
    message = 'Needs a closed, consistently oriented volume. Repair the mesh or choose Surface Centroid.'
    d._draw_unmeasurable(Recorder(labels), message)
    assert labels[0] == 'Spacing cannot be measured.', labels
    assert ' '.join(labels[1:]) == ' '.join(textwrap.wrap(message, 34)), labels
    assert all(len(line) <= 34 for line in labels[1:]), labels
    results['draw_unmeasurable'] = 'the explanation is drawn as wrapped panel lines under a short heading'


def precision_by_group():
    reset()
    obj = bpy.data.objects.new('P', None)
    ctx.scene.collection.objects.link(obj)
    properties = obj.better_item.bl_rna.properties
    expected = {'location': 5, 'rotation': 5, 'scale': 3, 'dimensions': 5}
    for group, precision in expected.items():
        for axis in 'xyz':
            actual = properties['%s_%s' % (group, axis)].precision
            assert actual == precision, (group, axis, actual, precision)
    results['precision_by_group'] = 'Location, Rotation and Dimensions use 5 digits, Scale 3, as the native fields do'


def sync_heading():
    paused = diagnostics.Diagnostic(BetterItemError('[BI-F006] RuntimeError: x'))
    assert paused.heading == 'Orientation sync paused', paused.heading
    for error in (BetterItemError('[BI-F006] x', severity='ERROR'), BetterItemError('[BI-F005] x'),
                  BetterItemError('[BI-T001] x'), ReferencePending('[BI-F002] x')):
        assert diagnostics.Diagnostic(error).heading is None, str(error)
    labels = []
    diagnostics.draw(Recorder(labels), BetterItemError('[BI-F006] RuntimeError: x'), Owner(), configuration=True)
    assert labels[0] == 'Orientation sync paused', labels
    labels = []
    diagnostics.draw(Recorder(labels), BetterItemError('[BI-F005] x'), Owner(), configuration=True)
    assert labels[0] == 'Reference unavailable', labels
    labels = []
    diagnostics.draw(Recorder(labels), BetterItemError('[BI-T001] x'), Owner())
    assert labels[0] == 'Not applied', labels
    results['sync_heading'] = 'BI-F006 has its own heading; every other diagnostic keeps its previous heading'


class Area:
    type = 'VIEW_3D'

    def __init__(self):
        self.redraws = 0

    def tag_redraw(self):
        self.redraws += 1


class Screen:
    def __init__(self, areas):
        self.areas = areas


class GoodWindow:
    def __init__(self, scene, areas):
        self.scene = scene
        self.screen = Screen(areas)


class ClosedWindow:
    @property
    def scene(self):
        raise ReferenceError('StructRNA of type Window has been removed')

    @property
    def screen(self):
        raise ReferenceError('StructRNA of type Window has been removed')


class BrokenWindow(ClosedWindow):
    @property
    def scene(self):
        raise RuntimeError('window is not available')


def redraw_invalid_window():
    reset()
    scene = ctx.scene
    area = Area()
    good = GoodWindow(scene, [area])
    for bad in (ClosedWindow(), BrokenWindow()):
        area.redraws = 0
        native_refs._redraw_all([bad, good])
        assert area.redraws == 1, (type(bad).__name__, area.redraws)
        native_refs._redraw_all([good, bad])
        assert area.redraws == 2, (type(bad).__name__, area.redraws)
    native_refs._redraw_all([])
    results['redraw_invalid_window'] = 'an invalid window is skipped and the remaining windows are still redrawn'


for case in (open_mesh_volume, incomplete_reference_unchanged, unmeasurable_classification, draw_unmeasurable,
             precision_by_group, sync_heading, redraw_invalid_window):
    case()
for name, text in results.items():
    print('OK', name, '-', text)
print('BETTER_ITEM_REGRESSIONS1710_OK')
