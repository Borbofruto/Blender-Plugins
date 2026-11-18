# SPDX-License-Identifier: GPL-3.0-or-later
"""Interface test with a real window (gui_async style: timers, isolated profile).

    blender --factory-startup --enable-event-simulate --python-exit-code 1 \
        --python test_gui_v0.py -- --out <dir>

Checks one-step Undo/Redo of the mark operators in Edit Mode, opens the real
menus (File > Export, Edit Mode context menu, Edge menu) and the export dialog,
takes screenshots, cancels the dialog and verifies nothing was written and the
scene is unchanged. Writes <out>/gui-<version>.json and PNG screenshots.
"""

import hashlib
import json
import os
import shutil
import sys
import traceback

import addon_utils
import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "calibration"))
import calibrate as shapes  # noqa: E402

MOD = "bl_ext.user_default.better_draft"
ATTR = "better_draft_arc_mode"
ARGV = sys.argv[sys.argv.index("--") + 1 :]
OUT_ROOT = ARGV[ARGV.index("--out") + 1]
VERSION = bpy.app.version_string.split()[0]
OUT = os.path.join(OUT_ROOT, "gui-" + VERSION)
EXPORT_DIR = os.path.join(OUT, "export-target")
STATE = {"checks": [], "errors": [], "screenshots": []}
EXPECTED_DEFAULTS = {
    "confidence_threshold": 0.7,
    "min_segments": 4,
    "circle_min_segments": 8,
    "straight_tolerance": 0.1,
    "fit_tolerance": 0.01,
    "plane": "LOCAL",
    "output": "PER_OBJECT",
    "spacing": 10.0,
    "loose_parts": "REFUSE",
    "min_part_area": 1.0,
    "write_report": True,
}


def check(name, ok, detail=None):
    STATE["checks"].append({"name": name, "ok": bool(ok), "detail": detail})


def window():
    return bpy.context.window_manager.windows[0]


def view3d():
    win = window()
    for area in win.screen.areas:
        if area.type == "VIEW_3D":
            region = next(r for r in area.regions if r.type == "WINDOW")
            return win, area, region
    raise RuntimeError("no 3D viewport")


def override():
    win, area, region = view3d()
    return bpy.context.temp_override(window=win, area=area, region=region, screen=win.screen)


def shot(name, win=None):
    win = win or window()
    path = os.path.join(OUT, name + ".png")
    if win.screen.is_temporary:  # file browser window: screen cannot be overridden
        ctx = bpy.context.temp_override(window=win)
    else:
        ctx = bpy.context.temp_override(window=win, screen=win.screen, area=win.screen.areas[0])
    with ctx:
        bpy.ops.screen.screenshot(filepath=path)
    STATE["screenshots"].append(os.path.basename(path))
    return path


def esc(win=None):
    win = win or window()
    win.event_simulate(type="ESC", value="PRESS")
    win.event_simulate(type="ESC", value="RELEASE")


def move_mouse_to_view():
    win, area, region = view3d()
    win.event_simulate(type="MOUSEMOVE", value="NOTHING", x=area.x + area.width // 2, y=area.y + area.height // 2)


def counts():
    obj = bpy.data.objects["rr"]
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.edges.layers.int.get(ATTR)
        vals = [0] * len(bm.edges) if layer is None else [e[layer] for e in bm.edges]
    else:
        attr = obj.data.attributes.get(ATTR)
        vals = [0] * len(obj.data.edges) if attr is None else [d.value for d in attr.data]
    return {"mode": obj.mode, "arc": vals.count(1), "lines": vals.count(2)}


def snapshot():
    bpy.context.view_layer.update()
    h = hashlib.sha256()
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        h.update(repr((obj.name, [tuple(r) for r in obj.matrix_world], obj.mode)).encode())
        if obj.type == "MESH":
            me = obj.data
            h.update(repr([tuple(v.co) for v in me.vertices]).encode())
            h.update(repr(sorted((a.name, a.domain) for a in me.attributes)).encode())
    h.update(repr(len(bpy.data.texts)).encode())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Steps: each returns a delay (seconds) before the next step.


def step_close_splash():
    move_mouse_to_view()
    esc()
    return 0.5


def step_setup():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(EXPORT_DIR)
    addon_utils.enable(MOD, default_set=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    obj, _ = shapes.case_rounded_rect_bmesh(8)
    obj.name = "rr"
    for o in bpy.context.view_layer.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    with override():
        bpy.ops.view3d.view_all()
        bpy.ops.ed.undo_push(message="Setup")
    check("export poll in Object Mode", bpy.ops.better_draft.export_dxf.poll())
    check("mark_arc poll in Object Mode is False", not bpy.ops.better_draft.mark_arc.poll())
    return 0.5


def step_menu_export_object():
    move_mouse_to_view()
    with override():
        bpy.ops.wm.call_menu(name="TOPBAR_MT_file_export")
    return 0.8


def step_shot_export_object():
    shot("menu_file_export_object_mode")
    esc()
    return 0.4


def step_enter_edit():
    with override():
        # Third positional argument = push an undo step, as the UI does.
        bpy.ops.object.mode_set("EXEC_DEFAULT", True, mode="EDIT")
        bpy.ops.mesh.select_mode("EXEC_DEFAULT", True, type="EDGE")
    obj = bpy.data.objects["rr"]
    bm = bmesh.from_edit_mesh(obj.data)
    for e in bm.edges:
        a, b = sorted(v.index for v in e.verts)
        e.select_set(b <= 8 and b - a == 1)  # first corner, 8 edges
    bmesh.update_edit_mesh(obj.data)
    with override():
        bpy.ops.ed.undo_push(message="Select corner")
    check("export poll in Edit Mode is False", not bpy.ops.better_draft.export_dxf.poll())
    check("mark_arc poll in Edit Mode", bpy.ops.better_draft.mark_arc.poll())
    return 0.4


def step_menu_export_edit():
    move_mouse_to_view()
    with override():
        bpy.ops.wm.call_menu(name="TOPBAR_MT_file_export")
    return 0.8


def step_shot_export_edit():
    shot("menu_file_export_edit_mode")
    esc()
    return 0.4


def step_menu_context():
    move_mouse_to_view()
    with override():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_context_menu")
    return 0.8


def step_shot_context():
    shot("menu_edit_mesh_context")
    esc()
    return 0.4


def step_menu_edges():
    move_mouse_to_view()
    with override():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_edges")
    return 0.8


def step_shot_edges():
    shot("menu_edit_mesh_edges")
    esc()
    return 0.4


def step_undo():
    seq = {}
    with override():
        seq["start"] = counts()
        bpy.ops.better_draft.mark_arc("EXEC_DEFAULT", True)
        seq["after_arc"] = counts()
        bpy.ops.better_draft.mark_lines("EXEC_DEFAULT", True)
        seq["after_lines"] = counts()
        bpy.ops.ed.undo()
        seq["undo1"] = counts()
        bpy.ops.ed.undo()
        seq["undo2"] = counts()
        bpy.ops.ed.redo()
        seq["redo1"] = counts()
        bpy.ops.ed.redo()
        seq["redo2"] = counts()
    check("mark arc marks 8 edges", seq["after_arc"] == {"mode": "EDIT", "arc": 8, "lines": 0}, seq)
    check("mark lines overrides to 8 lines", seq["after_lines"] == {"mode": "EDIT", "arc": 0, "lines": 8}, seq)
    check("undo 1 restores arc marks, stays in Edit Mode", seq["undo1"] == {"mode": "EDIT", "arc": 8, "lines": 0}, seq)
    check("undo 2 removes marks, stays in Edit Mode", seq["undo2"] == {"mode": "EDIT", "arc": 0, "lines": 0}, seq)
    check("redo 1 restores arc marks", seq["redo1"] == {"mode": "EDIT", "arc": 8, "lines": 0}, seq)
    check("redo 2 restores line marks", seq["redo2"] == {"mode": "EDIT", "arc": 0, "lines": 8}, seq)
    STATE["undo_sequence"] = seq
    with override():
        bpy.ops.object.mode_set(mode="OBJECT")
    return 0.4


def step_invoke_dialog():
    STATE["before_dialog"] = snapshot()
    STATE["windows_before"] = len(bpy.context.window_manager.windows)
    with override():
        res = bpy.ops.better_draft.export_dxf("INVOKE_DEFAULT", filepath=os.path.join(EXPORT_DIR, "dialog.dxf"))
    check("invoke opens file browser", res == {"RUNNING_MODAL"}, sorted(res))
    return 1.5


def _file_browser():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "FILE_BROWSER":
                return win, area
    return None, None


def step_dialog_inspect():
    win, area = _file_browser()
    check("file browser found", area is not None)
    if area is None:
        return 0.2
    op = area.spaces.active.active_operator
    values = {k: getattr(op.properties, k) for k in EXPECTED_DEFAULTS}
    bad = {k: v for k, v in values.items() if (abs(v - EXPECTED_DEFAULTS[k]) > 1e-6 if isinstance(v, float)
                                               else v != EXPECTED_DEFAULTS[k])}
    check("dialog defaults match approved values", not bad, {"values": values, "mismatch": bad})
    STATE["dialog_values"] = values
    # Make sure the side panel with the options is visible before the screenshot.
    for region in area.regions:
        if region.type == "TOOL_PROPS":
            STATE["tool_props_width"] = region.width
    shot("export_dialog", win)
    return 0.3


def step_dialog_cancel():
    win, area = _file_browser()
    if area is not None:
        # What a person does: Escape in the file browser window.
        region = next(r for r in area.regions if r.type == "WINDOW")
        win.event_simulate(type="MOUSEMOVE", value="NOTHING", x=region.x + region.width // 2, y=region.y + region.height // 2)
        esc(win)
        STATE["cancel_method"] = "Escape key (event_simulate)"
    return 1.0


def step_dialog_cancel_fallback():
    win, area = _file_browser()
    if area is not None:
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.file.cancel()
        STATE["cancel_method"] = "file.cancel (Escape did not close the browser)"
    return 1.0


def step_after_cancel():
    win, area = _file_browser()
    check("file browser closed after cancel", area is None)
    check("cancel wrote no file", os.listdir(EXPORT_DIR) == [], os.listdir(EXPORT_DIR))
    check("cancel left the scene unchanged", snapshot() == STATE["before_dialog"])
    return 0.2


def step_finish():
    STATE["passed"] = all(c["ok"] for c in STATE["checks"]) and not STATE["errors"]
    STATE["blender"] = bpy.app.version_string
    with open(os.path.join(OUT_ROOT, "gui-%s.json" % VERSION), "w", encoding="utf-8") as f:
        json.dump(STATE, f, indent=1, default=str)
    print("better_draft gui: %s on %s" % ("PASSED" if STATE["passed"] else "FAILED", VERSION))
    for c in STATE["checks"]:
        print("%s %s" % ("PASS" if c["ok"] else "FAIL", c["name"]))
    bpy.ops.wm.quit_blender()
    return None


STEPS = [
    step_close_splash,
    step_setup,
    step_menu_export_object,
    step_shot_export_object,
    step_enter_edit,
    step_menu_export_edit,
    step_shot_export_edit,
    step_menu_context,
    step_shot_context,
    step_menu_edges,
    step_shot_edges,
    step_undo,
    step_invoke_dialog,
    step_dialog_inspect,
    step_dialog_cancel,
    step_dialog_cancel_fallback,
    step_after_cancel,
    step_finish,
]


def runner():
    if not STEPS:
        return None
    fn = STEPS.pop(0)
    try:
        delay = fn()
    except Exception:  # noqa: BLE001
        STATE["errors"].append({"step": fn.__name__, "error": traceback.format_exc()})
        if fn is not step_finish:
            while STEPS and STEPS[0] is not step_finish:
                STEPS.pop(0)
        delay = 0.2
    return delay if STEPS else None


bpy.app.timers.register(runner, first_interval=2.0)
