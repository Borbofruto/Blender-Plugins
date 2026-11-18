# SPDX-License-Identifier: GPL-3.0-or-later
"""DXF output through the bundled ezdxf wheel. No Blender imports.

Files are first written next to their targets under temporary names; targets
are replaced only after every file of the export has been written.
"""

import os

from .constants import LAYER_INNER, LAYER_OUTER

TMP_SUFFIX = ".better-draft-tmp"


def load_error():
    """None if ezdxf imports, otherwise a short description of the failure."""
    try:
        import ezdxf  # noqa: F401
    except Exception as exc:  # noqa: BLE001  (ImportError or a broken install)
        return "%s: %s" % (type(exc).__name__, exc)
    return None


def build_document(placed):
    """Return an ezdxf document for [(piece, (dx, dy)), ...]."""
    import ezdxf
    from ezdxf import units

    doc = ezdxf.new("R2010", units=units.MM)
    doc.header["$MEASUREMENT"] = 1  # metric
    doc.layers.add(LAYER_OUTER)
    doc.layers.add(LAYER_INNER)
    msp = doc.modelspace()
    for piece, (dx, dy) in placed:
        for lr, role in zip(piece.region.loops, piece.region.roles):
            attribs = {"layer": LAYER_OUTER if role == "OUTER" else LAYER_INNER}
            for e in lr.entities:
                if e.kind == "LINE":
                    msp.add_line(
                        (e.start[0] + dx, e.start[1] + dy), (e.end[0] + dx, e.end[1] + dy), dxfattribs=attribs
                    )
                elif e.kind == "ARC":
                    a0, a1 = e.dxf_angles
                    msp.add_arc((e.center[0] + dx, e.center[1] + dy), e.radius, a0, a1, dxfattribs=attribs)
                else:
                    msp.add_circle((e.center[0] + dx, e.center[1] + dy), e.radius, dxfattribs=attribs)
    return doc


def write_all(jobs):
    """Write every (path, document, report_text_or_None) job, all or nothing.

    Returns the list of written paths. On failure removes temporary files,
    leaves existing targets untouched and re-raises.
    """
    temps = []
    try:
        for path, doc, text in jobs:
            tmp = path + TMP_SUFFIX
            doc.saveas(tmp)
            temps.append((tmp, path))
            if text is not None:
                rpath = os.path.splitext(path)[0] + ".txt"
                rtmp = rpath + TMP_SUFFIX
                with open(rtmp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
                temps.append((rtmp, rpath))
    except Exception:
        for tmp, _ in temps:
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise
    written = []
    for tmp, path in temps:
        os.replace(tmp, path)
        written.append(path)
    return written
