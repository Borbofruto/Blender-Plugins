"""Object identity with duplicate names: a local object and a linked library object.

Blender allows a local "Cube" and a "Cube" linked from another .blend in the same
scene. Every case runs twice on identical geometry: once with the local object
named "Cube.local" (control) and once named "Cube" (homonym of the linked one).
Positions, rotations, outcome and diagnostic code must be identical; the control
is also checked against analytic expectations where they are simple.

Self-contained: the library .blend is written to a temporary folder by this script.
Background-safe: operators run with EXEC_DEFAULT; Live is driven by update().
"""
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import addon_utils
import numpy as np

addon_utils.enable('better_item')
from better_item import arrange, distribution_preview as live

ctx = bpy.context
TEMP = Path(tempfile.mkdtemp(prefix='better_item_identity_'))
LIBRARY = TEMP / 'library.blend'
LINKED_AT = (0., 20., 30.)
CONTROL_NAME = 'Cube.local'
HOMONYM = 'Cube'


def cube_mesh(name, half):
    h = half
    verts = [(-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h), (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def write_library():
    reset()  # the factory scene has its own "Cube"
    mesh = cube_mesh('Library cube', 1.)
    obj = bpy.data.objects.new(HOMONYM, mesh)
    assert obj.name == HOMONYM, obj.name
    obj.location = LINKED_AT
    bpy.data.libraries.write(str(LIBRARY), {obj, mesh})
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh)


def reset():
    if live.active(ctx.scene):
        live.forget()
    arrange.clear_error()
    for library in list(bpy.data.libraries):
        bpy.data.libraries.remove(library)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for mesh in list(bpy.data.meshes):
        if not mesh.users:
            bpy.data.meshes.remove(mesh)
    s = ctx.scene.better_item
    s.arrange_reference_mode = 'INDIVIDUAL'
    s.arrange_origin = 'GLOBAL'
    s.arrange_orientation = 'GLOBAL'
    s.distribution_legacy_range = False
    s.distribution_method = 'OFFSET'
    s.distribution_mode = 'ORIGINS'
    s.endpoint_path = 'SEGMENT'
    s.distribution_start_override = False
    s.distribution_end.mode = 'MANUAL'
    s.distribution_end.position = (30., 20., 30.)
    s.axes = (True, False, False)
    s.spacing = 3.
    return s


def build(local_name, linked_first=True):
    """Linked "Cube" at LINKED_AT, a local cube named local_name, and two others.

    linked_first changes the scene/selection order, which decides which object
    overwrites the other in a name-keyed dictionary.
    """
    s = reset()

    def link_library_cube():
        with bpy.data.libraries.load(str(LIBRARY), link=True) as (_source, loaded):
            loaded.objects = [HOMONYM]
        ctx.scene.collection.objects.link(loaded.objects[0])
        return loaded.objects[0]

    roles = {}
    if linked_first:
        roles['linked'] = link_library_cube()
    for role, name, location in (('local', local_name, (5., 0., 0.)), ('other', 'Other', (8., 1., 1.)),
                                 ('third', 'Third', (12., -1., 2.))):
        obj = bpy.data.objects.new(name, cube_mesh(name + ' mesh', .5))
        ctx.scene.collection.objects.link(obj)
        obj.location = location
        roles[role] = obj
    if not linked_first:
        roles['linked'] = link_library_cube()
    linked = roles['linked']
    ctx.view_layer.update()
    assert linked.library is not None and linked.name == HOMONYM, (linked.name, linked.library)
    assert roles['local'].library is None and roles['local'].name == local_name, roles['local'].name
    assert tuple(linked.matrix_world.translation) == LINKED_AT
    return s, roles


def select(roles, names, active='local'):
    for obj in ctx.view_layer.objects:
        obj.select_set(False)
    for name in names:
        roles[name].select_set(True)
    ctx.view_layer.objects.active = roles[active]
    ctx.view_layer.update()


def snapshot(roles):
    ctx.view_layer.update()
    state = {}
    for role, obj in roles.items():
        try:
            in_scene = any(item == obj for item in ctx.scene.objects)
            state[role] = dict(position=[float(v) for v in obj.matrix_world.translation],
                               rotation=[float(v) for v in obj.rotation_euler], in_scene=in_scene)
        except ReferenceError:
            state[role] = dict(removed=True)
    return state


def outcome(call):
    arrange.clear_error()
    try:
        result = call()
        status = 'FINISHED' if 'FINISHED' in result else 'CANCELLED'
    except RuntimeError as exc:
        status = 'CANCELLED'
        message = str(exc)
    else:
        message = ''
    error = arrange.error(ctx.scene)
    message = str(error) if error else message
    code = re.search(r'BI-[A-Z]\d{3}', message)
    return dict(status=status, code=code.group(0) if code else None, message=message[:240])


def live_outcome():
    error = arrange.error(ctx.scene)
    message = str(error) if error else ''
    code = re.search(r'BI-[A-Z]\d{3}', message)
    return dict(status='ERROR' if error else 'UPDATED', code=code.group(0) if code else None, message=message[:240])


# --- cases: each receives (settings, roles) and returns an outcome dict -------------

def align_selection_min(s, r):
    select(r, ('local', 'linked', 'other'))
    return outcome(lambda: bpy.ops.better_item.align(axes=(True, False, False), reference='SELECTION', mode='MIN'))


def align_selection_min_linked_last(s, r):
    return align_selection_min(s, r)


align_selection_min_linked_last.linked_first = False


def align_selection_max_refused(s, r):
    # Max X is Other (8); the linked cube would have to move: T001 must refuse atomically.
    select(r, ('local', 'linked', 'other'))
    return outcome(lambda: bpy.ops.better_item.align(axes=(True, False, False), reference='SELECTION', mode='MAX'))


def align_to_linked_object(s, r):
    s.arrange_origin = 'OBJECT'
    s.arrange_origin_object = r['linked']
    select(r, ('local', 'other'))
    return outcome(lambda: bpy.ops.better_item.align(axes=(True, False, False), mode='MIN'))


def offset_origins(s, r):
    s.arrange_origin = 'OBJECT'
    s.arrange_origin_object = r['linked']
    select(r, ('local', 'other', 'third'))
    return outcome(lambda: bpy.ops.better_item.distribute(
        modern=True, method='OFFSET', distribution_mode='ORIGINS', axes=(True, False, False), spacing=3.))


def offset_geometry(s, r):
    s.arrange_origin = 'OBJECT'
    s.arrange_origin_object = r['linked']
    select(r, ('local', 'other', 'third'))
    return outcome(lambda: bpy.ops.better_item.distribute(
        modern=True, method='OFFSET', distribution_mode='GEOMETRY', axes=(True, False, False), spacing=1.))


def endpoint_setup(s, r):
    s.distribution_method = 'ENDPOINT'
    s.distribution_start_override = True
    s.distribution_start.mode = 'OBJECT'
    s.distribution_start.object = r['linked']
    s.distribution_end.mode = 'MANUAL'
    s.distribution_end.position = (30., 20., 30.)
    select(r, ('local', 'other', 'third'))


def endpoint_origins(s, r):
    endpoint_setup(s, r)
    return outcome(lambda: bpy.ops.better_item.distribute(
        modern=True, method='ENDPOINT', distribution_mode='ORIGINS', path='SEGMENT'))


def orientation_match(s, r):
    # The linked cube is the orientation reference and is selected: a selected
    # reference keeps its orientation and is not required to be editable.
    s.arrange_orientation = 'REFERENCE'
    s.arrange_object = r['linked']
    r['local'].rotation_euler = (0., 0., .5)
    r['other'].rotation_euler = (.3, 0., 0.)
    select(r, ('local', 'other', 'linked'))
    return outcome(lambda: bpy.ops.better_item.align_orientation(mode='MATCH', axes=(True, True, True)))


def live_endpoint(s, r):
    endpoint_setup(s, r)
    s.distribution_mode = 'ORIGINS'
    live.begin(ctx)
    try:
        s.distribution_end.position = (36., 20., 30.)
        ctx.view_layer.update()
        live.update(ctx)
        return live_outcome()
    finally:
        live.finish(ctx)


def live_target_unlinked(s, r):
    # A captured target leaves the scene; a homonym in the scene must not count as it.
    endpoint_setup(s, r)
    live.begin(ctx)
    try:
        ctx.scene.collection.objects.unlink(r['local'])
        s.distribution_end.position = (36., 20., 30.)
        ctx.view_layer.update()
        live.update(ctx)
        return live_outcome()
    finally:
        live.forget()
        arrange.clear_error()


CASES = [align_selection_min, align_selection_min_linked_last, align_selection_max_refused, align_to_linked_object, offset_origins,
         offset_geometry, endpoint_origins, orientation_match, live_endpoint, live_target_unlinked]


def close(a, b, tolerance=1e-5):
    return all(abs(x - y) <= tolerance for x, y in zip(a, b))


def same_state(control, homonym):
    for role in control:
        c, h = control[role], homonym[role]
        if c.get('removed') or h.get('removed'):
            if c.get('removed') != h.get('removed'):
                return False
            continue
        if c['in_scene'] != h['in_scene'] or not close(c['position'], h['position']) or not close(c['rotation'], h['rotation']):
            return False
    return True


def control_expectations(name, before, after, result):
    """Analytic checks on the control run only; returns a list of problems."""
    problems = []
    pos = {role: np.array(state['position']) for role, state in after.items() if not state.get('removed')}
    if not close(pos['linked'], LINKED_AT):
        problems.append('linked object moved')
    if name in ('align_selection_min', 'align_selection_min_linked_last'):
        if result['status'] != 'FINISHED':
            problems.append('expected success')
        if not (close(pos['local'], (0, 0, 0)) and close(pos['other'], (0, 1, 1))):
            problems.append('local/other not aligned to x=0 with Y/Z preserved')
    elif name == 'align_selection_max_refused':
        if result['status'] == 'FINISHED' or result['code'] != 'BI-T001':
            problems.append('expected BI-T001 refusal')
        if any(not close(after[k]['position'], before[k]['position']) for k in after):
            problems.append('refusal was not atomic')
    elif name == 'align_to_linked_object':
        if result['status'] != 'FINISHED' or abs(pos['local'][0]) > 1e-6 or abs(pos['other'][0]) > 1e-6:
            problems.append('expected local and other at the linked origin x=0')
    elif name == 'offset_origins':
        if result['status'] != 'FINISHED':
            problems.append('expected success')
        expected = {'local': (3, 0, 0), 'other': (6, 1, 1), 'third': (9, -1, 2)}
        if any(not close(pos[k], v) for k, v in expected.items()):
            problems.append('offset slots 3/6/9 with Y/Z preserved not reached')
    elif name == 'endpoint_origins':
        if result['status'] != 'FINISHED':
            problems.append('expected success')
        # Endpoint orders by initial distance to Start: Other 35.6, local 36.4, Third 37.0.
        expected = {'other': (0, 20, 30), 'local': (15, 20, 30), 'third': (30, 20, 30)}
        if any(not close(pos[k], v) for k, v in expected.items()):
            problems.append('endpoint slots 0/15/30 on the segment not reached')
    elif name == 'live_endpoint':
        if result['status'] != 'UPDATED':
            problems.append('expected a Live update without error')
        expected = {'other': (0, 20, 30), 'local': (18, 20, 30), 'third': (36, 20, 30)}
        if any(not close(pos[k], v) for k, v in expected.items()):
            problems.append('Live endpoint slots 0/18/36 not reached')
    elif name == 'live_target_unlinked':
        if result['code'] != 'BI-L001':
            problems.append('expected BI-L001 for a captured target outside the scene')
    elif name in ('offset_geometry', 'orientation_match'):
        if result['status'] != 'FINISHED':
            problems.append('expected success')
        if name == 'orientation_match':
            if not (close(after['local']['rotation'], (0, 0, 0)) and close(after['other']['rotation'], (0, 0, 0))):
                problems.append('rotations not matched to Global')
            if any(not close(after[k]['position'], before[k]['position']) for k in ('local', 'other')):
                problems.append('origins moved while matching orientation')
    return problems


def run(case, local_name):
    s, roles = build(local_name, getattr(case, 'linked_first', True))
    before = snapshot(roles)
    try:
        result = case(s, roles)
    except Exception as exc:  # report, do not stop the other cases
        result = dict(status='EXCEPTION', code=None, message=('%s: %s' % (type(exc).__name__, exc))[:240])
    return before, snapshot(roles), result


write_library()
report = []
try:
    for case in CASES:
        c_before, c_after, c_result = run(case, CONTROL_NAME)
        h_before, h_after, h_result = run(case, HOMONYM)
        problems = control_expectations(case.__name__, c_before, c_after, c_result)
        identical = (c_result['status'], c_result['code']) == (h_result['status'], h_result['code']) and same_state(c_after, h_after)
        report.append(dict(case=case.__name__, control_ok=not problems, control_problems=problems,
                           homonym_matches_control=identical, control=dict(result=c_result, after=c_after),
                           homonym=dict(result=h_result, after=h_after)))
finally:
    reset()
    shutil.rmtree(TEMP, ignore_errors=True)

failed = [row['case'] for row in report if not (row['control_ok'] and row['homonym_matches_control'])]
for row in report:
    print('%-28s control=%-4s homonym=%-4s  control:%s %s | homonym:%s %s' % (
        row['case'], 'ok' if row['control_ok'] else 'FAIL', 'same' if row['homonym_matches_control'] else 'DIFF',
        row['control']['result']['status'], row['control']['result']['code'],
        row['homonym']['result']['status'], row['homonym']['result']['code']))
    for problem in row['control_problems']:
        print('    control problem:', problem)
    if not row['homonym_matches_control']:
        for role in row['control']['after']:
            c, h = row['control']['after'][role], row['homonym']['after'][role]
            if c != h:
                print('    %-7s control %s | homonym %s' % (role, c, h))
result = dict(passed=not failed, blender=bpy.app.version_string, module=__import__('better_item').__file__,
              failed=failed, cases=report)
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
if failed:
    raise AssertionError('duplicate-name identity failures: ' + ', '.join(failed))
print('BETTER_ITEM_IDENTITY1711_OK')
