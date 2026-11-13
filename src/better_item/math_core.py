"""Numeric rules for Better Item. All positions passed here are world origins."""
import math


class BetterItemError(ValueError):
    pass


def vector3(values):
    result=tuple(float(v) for v in values)
    if len(result)!=3 or not all(math.isfinite(v) for v in result):
        raise BetterItemError('Enter three finite X, Y and Z values.')
    return result


def different(a,b):
    return not math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-12)


def linked_values(before,axis,value,links,zero_angle_as_turn=False):
    before=vector3(before)
    value=float(value)
    if axis not in (0,1,2) or len(links)!=3 or not math.isfinite(value):
        raise BetterItemError('Invalid transform axis or value.')
    result=list(before)
    result[axis]=value
    if not different(value,before[axis]):
        return tuple(result)
    if links[axis] and sum(bool(v) for v in links)>1:
        if before[axis]==0 and not zero_angle_as_turn:
            raise BetterItemError('Cannot define a ratio from %s = 0. Unlink that axis first.' % 'XYZ'[axis])
        # Zero is only a denominator fallback for the axis being edited.
        # Other zero angles remain zero, and crossing zero scales to zero.
        denominator=math.tau if zero_angle_as_turn and before[axis]==0 else before[axis]
        factor=value/denominator
        for i,linked in enumerate(links):
            if linked:
                result[i]=value if i==axis else before[i]*factor
    return vector3(result)


def _inputs(origins,axes,reference,key):
    if len(axes)!=3 or not any(axes):
        raise BetterItemError('Select at least one axis: X, Y or Z.')
    if reference not in {'SELECTION','KEY'}:
        raise BetterItemError('Invalid alignment reference.')
    if reference=='KEY' and key not in origins:
        raise BetterItemError('The key object must be active and selected.')
    return {name:list(vector3(position)) for name,position in origins.items()}


def align_positions(origins,axes,reference,mode='MIN',key=None):
    result=_inputs(origins,axes,reference,key)
    if len(result)<2:
        raise BetterItemError('Select at least two objects.')
    if mode not in {'MIN','CENTER','MAX'}:
        raise BetterItemError('Invalid alignment mode.')
    for axis,enabled in enumerate(axes):
        if not enabled:
            continue
        values=[position[axis] for position in origins.values()]
        target=origins[key][axis] if reference=='KEY' else (
            min(values) if mode=='MIN' else max(values) if mode=='MAX' else (min(values)+max(values))/2)
        for name in result:
            result[name][axis]=target
    return result


def distribute_positions(origins,axes,reference,spacing=0,key=None):
    result=_inputs(origins,axes,reference,key)
    if len(result)<(3 if reference=='SELECTION' else 2):
        raise BetterItemError('Select at least %s objects.' % (3 if reference=='SELECTION' else 2))
    if not math.isfinite(spacing):
        raise BetterItemError('Enter a finite spacing.')
    for axis,enabled in enumerate(axes):
        if not enabled:
            continue
        if reference=='SELECTION':
            order=sorted(origins,key=lambda name:(origins[name][axis],name))
            low,high=origins[order[0]][axis],origins[order[-1]][axis]
            step=(high-low)/(len(order)-1)
            for rank,name in enumerate(order):
                result[name][axis]=low if rank==0 else high if rank==len(order)-1 else low+rank*step
        else:
            anchor=origins[key][axis]
            def priority(name):
                delta=origins[name][axis]-anchor
                # Opposite half-space first, then distance within each half.
                return (0 if delta*spacing<0 else 1,abs(delta),name)
            order=sorted((name for name in origins if name!=key),key=priority)
            for rank,name in enumerate(order,1):
                result[name][axis]=anchor+rank*spacing
    return result
