# SPDX-License-Identifier: GPL-3.0-or-later
"""Orthonormal axes for world and object orientations."""
from mathutils import Matrix
from . import engine
from .math_core import BetterItemError, vector3


def basis(obj, mode, reference=None):
    if mode == 'GLOBAL':
        return Matrix.Identity(3)
    source = obj if mode == 'LOCAL' else reference
    if source is None:
        raise BetterItemError('Choose an Orientation Object.')
    if mode not in {'LOCAL', 'REFERENCE'}:
        raise BetterItemError('Invalid orientation.')
    # Quaternion extraction removes translation, scale and reflections.
    return source.matrix_world.to_quaternion().normalized().to_matrix()

