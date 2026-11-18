# SPDX-License-Identifier: GPL-3.0-or-later
"""Better Draft (provisional name).

The recognition core (``geometry2d``, ``recognition``, ``parts``, ``pipeline``)
has no Blender imports. Blender-facing modules are imported only in ``register``.
"""


def register():
    from . import operators

    operators.register()


def unregister():
    from . import operators

    operators.unregister()
