# SPDX-License-Identifier: GPL-3.0-or-later
"""Run after installing better_draft and a fake extension that bundles another
version of ezdxf or pyparsing. Records what loads and whether export works.

    blender --offline-mode --background --factory-startup --python-exit-code 1 \
        --python test_conflict_check.py -- --out <dir> --label <name>
"""

import glob
import json
import os
import sys

import addon_utils
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "calibration"))
import calibrate as shapes  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    out = argv[argv.index("--out") + 1]
    label = argv[argv.index("--label") + 1]
    result = {"blender": bpy.app.version_string, "label": label}
    enabled = {}
    for mod in ("bl_ext.user_default.better_draft", "bl_ext.user_default.bd_conflict_pyparsing",
                "bl_ext.user_default.bd_conflict_ezdxf"):
        try:
            addon_utils.enable(mod, default_set=True)
        except Exception as exc:  # noqa: BLE001
            enabled[mod] = "error: %s" % exc
            continue
        enabled[mod] = mod in bpy.context.preferences.addons
    result["enabled"] = enabled
    site = [p for p in sys.path if p.replace("\\", "/").endswith(".local/lib/python%d.%d/site-packages" % sys.version_info[:2])]
    result["site_packages"] = site
    result["dist_info"] = sorted(os.path.basename(p) for s in site for p in glob.glob(os.path.join(s, "*.dist-info")))
    import ezdxf
    import pyparsing

    result["ezdxf"] = ezdxf.__version__
    result["pyparsing"] = pyparsing.__version__
    obj, _ = shapes.case_bevel_modifier(8)
    for o in bpy.context.view_layer.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    path = os.path.join(out, "conflict_%s.dxf" % label)
    try:
        res = bpy.ops.better_draft.export_dxf(filepath=path)
        result["export"] = sorted(res)
        doc = ezdxf.readfile(path)
        counts = {}
        for e in doc.modelspace():
            counts[e.dxftype()] = counts.get(e.dxftype(), 0) + 1
        result["entities"] = counts
        result["export_ok"] = counts == {"ARC": 4, "LINE": 4} and doc.header.get("$INSUNITS") == 4
    except Exception as exc:  # noqa: BLE001
        result["export"] = "error: %s" % exc
        result["export_ok"] = False
    with open(os.path.join(out, "conflict-%s-%s.json" % (label, bpy.app.version_string.split()[0])), "w") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))


main()
