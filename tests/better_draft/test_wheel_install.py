# SPDX-License-Identifier: GPL-3.0-or-later
"""Run inside Blender after installing the better_draft ZIP (offline mode).

Checks that the bundled ezdxf wheel imports from the extension's site-packages,
writes a DXF with LINE/ARC/CIRCLE in millimetres and reads it back.

    blender --offline-mode --background --factory-startup --python-exit-code 1 \
        --python test_wheel_install.py -- --out <dir>
"""

import json
import os
import sys

import addon_utils
import bpy


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    out_dir = argv[argv.index("--out") + 1]
    os.makedirs(out_dir, exist_ok=True)
    result = {"blender": bpy.app.version_string, "online_access": bpy.app.online_access}
    mod = "bl_ext.user_default.better_draft"
    addon_utils.enable(mod, default_set=True)
    result["enabled"] = mod in bpy.context.preferences.addons
    import ezdxf  # noqa: E402

    result["ezdxf_version"] = ezdxf.__version__
    result["ezdxf_file"] = ezdxf.__file__
    doc = ezdxf.new("R2010", units=4)  # 4 = millimetres
    msp = doc.modelspace()
    doc.layers.add("OUTER")
    msp.add_line((0, 0), (40, 0), dxfattribs={"layer": "OUTER"})
    msp.add_arc((40, 5), 5, 270, 360, dxfattribs={"layer": "OUTER"})
    msp.add_circle((20, 10), 3, dxfattribs={"layer": "INNER"})
    path = os.path.join(out_dir, "wheel_test.dxf")
    doc.saveas(path)
    back = ezdxf.readfile(path)
    ents = [(e.dxftype(), e.dxf.layer) for e in back.modelspace()]
    result["insunits"] = back.header.get("$INSUNITS")
    result["entities"] = ents
    ok = (
        result["enabled"]
        and result["insunits"] == 4
        and ents == [("LINE", "OUTER"), ("ARC", "OUTER"), ("CIRCLE", "INNER")]
        and ".local" in result["ezdxf_file"].replace("\\", "/")
    )
    result["ok"] = bool(ok)
    with open(os.path.join(out_dir, "wheel_test-%s.json" % bpy.app.version_string.split()[0]), "w") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result))
    if not ok:
        raise SystemExit(1)


main()
