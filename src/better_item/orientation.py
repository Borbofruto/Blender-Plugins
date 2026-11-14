# SPDX-License-Identifier: GPL-3.0-or-later
"""Orthonormal axes for world and object orientations."""
from mathutils import Matrix,Quaternion,Euler
from .math_core import BetterItemError,ReferencePending


def channel_rotation(obj):
    if obj.rotation_mode=='QUATERNION':return obj.rotation_quaternion.normalized()
    if obj.rotation_mode=='AXIS_ANGLE':
        angle,*axis=obj.rotation_axis_angle
        return Quaternion(axis,angle)
    return obj.rotation_euler.to_quaternion()


def local_rotation(obj):
    scale=tuple(obj.scale[i]*obj.delta_scale[i] for i in range(3))
    if all(abs(v)>1e-12 for v in scale):
        # matrix_basis includes Blender's actual delta rotation, including
        # axis-angle delta data that has no public RNA property.
        matrix=obj.matrix_basis.to_3x3() @ Matrix.Diagonal(tuple(1/v for v in scale))
        return matrix.to_quaternion().normalized()
    if obj.rotation_mode=='QUATERNION':return obj.delta_rotation_quaternion.normalized() @ channel_rotation(obj)
    if obj.rotation_mode!='AXIS_ANGLE':return Euler(tuple(obj.delta_rotation_euler),obj.rotation_mode).to_quaternion() @ channel_rotation(obj)
    return channel_rotation(obj)


def delta_rotation(obj):
    return local_rotation(obj) @ channel_rotation(obj).inverted()


def inherited_rotation(obj):
    if not obj.parent:return Matrix.Identity(3)
    from .engine import _parent_matrix
    matrix=_parent_matrix(obj).to_3x3()
    if matrix.determinant()>0:return matrix_rotation(matrix)
    if obj.parent_type!='OBJECT':
        return matrix_rotation(matrix)
    else:
        # Object channel rotations are independent of signed scale.
        return rotation(obj.parent) @ matrix_rotation(obj.matrix_parent_inverse.to_3x3())


def matrix_rotation(matrix):
    if matrix.determinant()<=0:
        raise BetterItemError('A reflected or singular parent-inverse/bone matrix has no unambiguous rotation. Clear the parent inverse or use a manual reference.')
    return matrix.to_quaternion().normalized().to_matrix()


def rotation(obj):
    """World channel rotation, without interpreting negative scale as 180°."""
    signs=Matrix.Diagonal(tuple(-1 if obj.scale[i]*obj.delta_scale[i]<0 else 1 for i in range(3)))
    unsigned=obj.matrix_world.to_3x3() @ signs
    if unsigned.determinant()>1e-12:
        return unsigned.to_quaternion().normalized().to_matrix()
    # A mirrored ancestor or collapsed axis needs the native channel basis;
    # a matrix by itself cannot tell which ancestor channel owned each sign.
    return inherited_rotation(obj) @ local_rotation(obj).to_matrix()


def basis(obj, mode, reference=None):
    if mode == 'GLOBAL':
        return Matrix.Identity(3)
    source = obj if mode == 'LOCAL' else reference
    if source is None:
        raise ReferencePending('[BI-F002] Choose an object for Orientation.')
    if mode not in {'LOCAL', 'REFERENCE'}:
        raise BetterItemError('Invalid orientation.')
    return rotation(source)

