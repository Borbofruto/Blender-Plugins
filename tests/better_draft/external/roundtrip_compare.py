# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare original DXFs with their ODA File Converter round trip (DXF -> DWG -> DXF).

    python -I roundtrip_compare.py <original_dir> <dwg_dir> <roundtrip_dir> <out.json>
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxf_raw  # noqa: E402


def main():
    orig_dir, dwg_dir, rt_dir, out = sys.argv[1:5]
    rows = []
    for name in sorted(n for n in os.listdir(orig_dir) if n.lower().endswith(".dxf")):
        stem = os.path.splitext(name)[0]
        row = {"file": name}
        dwg = os.path.join(dwg_dir, stem + ".dwg")
        rt = os.path.join(rt_dir, stem + ".dxf")
        row["dwg_bytes"] = os.path.getsize(dwg) if os.path.exists(dwg) else None
        errs = [n for n in os.listdir(dwg_dir) if n.startswith(stem) and n.lower().endswith(".err")]
        errs += [n for n in os.listdir(rt_dir) if n.startswith(stem) and n.lower().endswith(".err")]
        row["err_files"] = {n: open(os.path.join(dwg_dir if os.path.exists(os.path.join(dwg_dir, n)) else rt_dir, n),
                                    encoding="utf-8", errors="replace").read()[:2000] for n in errs}
        if not os.path.exists(rt):
            row.update({"ok": False, "error": "round-trip DXF missing"})
            rows.append(row)
            continue
        a = dxf_raw.parse_raw(os.path.join(orig_dir, name))
        b = dxf_raw.parse_raw(rt)
        problems = dxf_raw.compare(a["entities"], b["entities"], tol=1e-6)
        layers_a = sorted({e["layer"] for e in a["entities"]})
        layers_b = sorted({e["layer"] for e in b["entities"]})
        row.update({
            "entities_original": len(a["entities"]),
            "entities_roundtrip": len(b["entities"]),
            "other_entities_roundtrip": b["other_entities"],
            "insunits": [a["header"].get("$INSUNITS"), b["header"].get("$INSUNITS")],
            "layers": [layers_a, layers_b],
            "problems": problems[:10],
            "ok": not problems and layers_a == layers_b and a["header"].get("$INSUNITS") == b["header"].get("$INSUNITS")
            and not row["err_files"],
        })
        rows.append(row)
    data = {"rows": rows, "passed": all(r["ok"] for r in rows)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("oda round trip:", sum(r["ok"] for r in rows), "/", len(rows))


main()
