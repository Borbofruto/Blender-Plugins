# SPDX-License-Identifier: GPL-3.0-or-later
"""Blender operators and menu entries."""

import os
import re

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from . import constants as C
from . import dxf_writer, messages, parts, pipeline, textreport
from . import recognition as rc
from .region import extract_region

_DEFAULTS = rc.Params()


def _safe_name(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._") or "object"


class BETTER_DRAFT_OT_export_dxf(bpy.types.Operator, ExportHelper):
    """Export the outline of each selected flat mesh as DXF with lines, arcs and circles"""

    bl_idname = C.OPERATOR_PREFIX + ".export_dxf"
    bl_label = "Export Technical Profile"
    bl_options = {"PRESET"}

    filename_ext = ".dxf"
    filter_glob: StringProperty(default="*.dxf", options={"HIDDEN"})

    confidence_threshold: FloatProperty(
        name="Confidence Threshold",
        description="Arc candidates at or above this confidence become arcs",
        default=_DEFAULTS.confidence_threshold, min=0.0, max=1.0, precision=2, step=5,
    )
    min_segments: IntProperty(
        name="Min Segments",
        description="Runs with fewer segments never become arcs automatically",
        default=_DEFAULTS.min_segments, min=2, max=64,
    )
    circle_min_segments: IntProperty(
        name="Circle Min Segments",
        description="A whole loop becomes a circle only with at least this many segments",
        default=_DEFAULTS.circle_min_segments, min=3, max=256,
    )
    straight_tolerance: FloatProperty(
        name="Straight Tolerance",
        description="Vertices turning less than this (degrees) are subdivisions of a straight line",
        default=_DEFAULTS.straight_tolerance_deg, min=0.0, max=10.0, precision=3, step=1,
    )
    fit_tolerance: FloatProperty(
        name="Fit Tolerance (mm)",
        description="Largest accepted distance between a vertex and its arc or line; also the flatness tolerance",
        default=_DEFAULTS.fit_tolerance_mm, min=1e-6, max=10.0, precision=4, step=0.1,
    )
    plane: EnumProperty(
        name="Plane",
        items=(
            ("LOCAL", "Local Part", "Coordinates in the plane of the part, X from the object's X axis"),
            ("WORLD_XY", "World XY", "World X and Y; the region must be parallel to the XY plane"),
        ),
        default="LOCAL",
    )
    output: EnumProperty(
        name="Files",
        items=(
            (pipeline.OUTPUT_PER_OBJECT, "One per Object", "One DXF per selected object"),
            (pipeline.OUTPUT_SINGLE, "Single File", "All pieces side by side in one DXF"),
        ),
        default=pipeline.OUTPUT_PER_OBJECT,
    )
    spacing: FloatProperty(
        name="Spacing (mm)",
        description="Gap between pieces placed side by side",
        default=10.0, min=0.0, max=10000.0, precision=2,
    )
    loose_parts: EnumProperty(
        name="Loose Parts",
        items=(
            (parts.MODE_REFUSE, "Stop", "Stop and report when an object has several separate parts"),
            (parts.MODE_LARGEST, "Largest", "Export only the largest part (one copy if the largest are identical)"),
            (parts.MODE_ALL, "All", "Export every part as its own piece"),
        ),
        default=parts.MODE_REFUSE,
    )
    min_part_area: FloatProperty(
        name="Min Part Area (%)",
        description="Parts smaller than this percentage of the largest part are ignored",
        default=1.0, min=0.0, max=100.0, precision=2,
    )
    write_report: BoolProperty(
        name="Write Report",
        description="Write a .txt report next to each DXF",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and any(o.type == "MESH" for o in context.selected_objects)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(heading="Recognition")
        col.prop(self, "confidence_threshold")
        col.prop(self, "min_segments")
        col.prop(self, "circle_min_segments")
        col.prop(self, "straight_tolerance")
        col.prop(self, "fit_tolerance")
        col = layout.column(heading="Output")
        col.prop(self, "plane")
        col.prop(self, "output")
        col.prop(self, "spacing")
        col.prop(self, "loose_parts")
        col.prop(self, "min_part_area")
        col.prop(self, "write_report")

    def params(self):
        return rc.Params(
            confidence_threshold=self.confidence_threshold,
            min_segments=self.min_segments,
            circle_min_segments=self.circle_min_segments,
            straight_tolerance_deg=self.straight_tolerance,
            fit_tolerance_mm=self.fit_tolerance,
        )

    def execute(self, context):
        objects = sorted((o for o in context.selected_objects if o.type == "MESH"), key=lambda o: o.name)
        if not objects:
            self.report({"ERROR"}, "Select one or more mesh objects")
            return {"CANCELLED"}
        params = self.params()
        depsgraph = context.evaluated_depsgraph_get()
        results = []
        problems = []
        for obj in objects:
            data = extract_region(obj, depsgraph, context.scene, params.fit_tolerance_mm, self.plane == "WORLD_XY")
            res = pipeline.analyze_object(obj.name, data, params, self.loose_parts, self.min_part_area / 100.0)
            results.append(res)
            problems.extend(res.problems)
        if problems:
            texts = [messages.format_problem(n, p, pt, params.fit_tolerance_mm) for n, p, pt in problems]
            for t in texts:
                print("%s: %s" % (C.ADDON_NAME, t))
            for t in texts[1:]:
                self.report({"ERROR"}, t)
            more = " (%d more in the Info editor)" % (len(texts) - 1) if len(texts) > 1 else ""
            self.report({"ERROR"}, "Nothing exported. " + texts[0] + more)
            return {"CANCELLED"}

        pieces = [p for r in results for p in r.pieces]
        notes = {r.name: r.notes for r in results}
        groups = pipeline.layout(pieces, self.output, self.spacing)
        base, _ = os.path.splitext(self.filepath)
        jobs = []
        used = set()
        for key, placed in groups:
            if self.output == pipeline.OUTPUT_SINGLE or len(groups) == 1:
                path = base + ".dxf"
            else:
                stem = "%s_%s" % (base, _safe_name(key))
                path = stem + ".dxf"
                k = 2
                while path.lower() in used:
                    path = "%s_%d.dxf" % (stem, k)
                    k += 1
            used.add(path.lower())
            doc = dxf_writer.build_document(placed)
            text = None
            if self.write_report:
                header = "File: %s\nBlender %s" % (os.path.basename(path), bpy.app.version_string)
                text = textreport.build(placed, params, notes, header)
            jobs.append((path, doc, text))
        try:
            written = dxf_writer.write_all(jobs)
        except OSError as exc:
            self.report({"ERROR"}, "Nothing exported: could not write %s (%s). Check the folder and permissions" % (
                getattr(exc, "filename", None) or "the file", exc.strerror or exc))
            return {"CANCELLED"}
        c = pipeline.counts(pieces)
        manual = sum(
            1 for p in pieces for lr in p.region.loops for e in lr.entities
            if e.kind != "LINE" and e.candidate.manual == "arc"
        )
        dxf_count = sum(1 for w in written if w.lower().endswith(".dxf"))
        summary = "Exported %d piece(s) to %d DXF file(s): %d lines, %d arcs, %d circles (%d marked as arc)" % (
            len(pieces), dxf_count, c["LINE"], c["ARC"], c["CIRCLE"], manual)
        skipped = sum(len(n) for n in notes.values())
        if skipped:
            summary += "; %d part(s) skipped, see report" % skipped
        self.report({"INFO"}, summary)
        return {"FINISHED"}


class _MarkBase:
    bl_options = {"REGISTER", "UNDO"}
    mode = C.MODE_AUTO

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        changed = 0
        selected = 0
        for obj in context.objects_in_mode_unique_data:
            if obj.type != "MESH":
                continue
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            count = sum(1 for e in bm.edges if e.select)
            if not count:
                continue
            selected += count
            layer = bm.edges.layers.int.get(C.ARC_MODE_ATTRIBUTE)
            if layer is None:
                if self.mode == C.MODE_AUTO:
                    continue  # nothing marked yet: do not create the attribute
                # Adding a layer invalidates existing BMEdge references.
                layer = bm.edges.layers.int.new(C.ARC_MODE_ATTRIBUTE)
            for e in (e for e in bm.edges if e.select):
                if e[layer] != self.mode:
                    e[layer] = self.mode
                    changed += 1
            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
        if not selected:
            self.report({"WARNING"}, "Select the edges of the outline run first")
            return {"CANCELLED"}
        self.report({"INFO"}, "%s: %d edge(s) changed" % (self.bl_label, changed))
        return {"FINISHED"}


class BETTER_DRAFT_OT_mark_arc(_MarkBase, bpy.types.Operator):
    """Force the selected outline edges to export as one arc"""

    bl_idname = C.OPERATOR_PREFIX + ".mark_arc"
    bl_label = C.MARK_ARC_LABEL
    mode = C.MODE_ARC


class BETTER_DRAFT_OT_mark_lines(_MarkBase, bpy.types.Operator):
    """Force the selected outline edges to export as straight lines"""

    bl_idname = C.OPERATOR_PREFIX + ".mark_lines"
    bl_label = C.MARK_LINES_LABEL
    mode = C.MODE_LINES


class BETTER_DRAFT_OT_mark_auto(_MarkBase, bpy.types.Operator):
    """Let recognition decide for the selected outline edges"""

    bl_idname = C.OPERATOR_PREFIX + ".mark_auto"
    bl_label = C.MARK_AUTO_LABEL
    mode = C.MODE_AUTO


def menu_export(self, context):
    self.layout.operator(BETTER_DRAFT_OT_export_dxf.bl_idname, text=C.EXPORT_MENU_LABEL)


def menu_mark(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(BETTER_DRAFT_OT_mark_arc.bl_idname)
    layout.operator(BETTER_DRAFT_OT_mark_lines.bl_idname)
    layout.operator(BETTER_DRAFT_OT_mark_auto.bl_idname)


CLASSES = (
    BETTER_DRAFT_OT_export_dxf,
    BETTER_DRAFT_OT_mark_arc,
    BETTER_DRAFT_OT_mark_lines,
    BETTER_DRAFT_OT_mark_auto,
)

MENUS = (
    ("TOPBAR_MT_file_export", menu_export),
    ("VIEW3D_MT_edit_mesh_context_menu", menu_mark),
    ("VIEW3D_MT_edit_mesh_edges", menu_mark),
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    for menu, fn in MENUS:
        getattr(bpy.types, menu).append(fn)


def unregister():
    for menu, fn in reversed(MENUS):
        getattr(bpy.types, menu).remove(fn)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
