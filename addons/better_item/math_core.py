"""Numeric rules for Better Item. All positions passed here are world origins."""
import math


class BetterItemError(ValueError):
    pass


def vector3(values):
    result=tuple(float(v) for v in values)
    if len(result)!=3 or not all(math.isfinite(v) for v in result):
        raise BetterItemError('Informe tres valores finitos para X, Y e Z.')
    return result


def different(a,b):
    return not math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-12)


def linked_values(before,axis,value,links):
    before=vector3(before)
    value=float(value)
    if axis not in (0,1,2) or len(links)!=3 or not math.isfinite(value):
        raise BetterItemError('Eixo ou valor de transformacao invalido.')
    result=list(before)
    result[axis]=value
    if not different(value,before[axis]):
        return tuple(result)
    if links[axis] and sum(bool(v) for v in links)>1:
        if before[axis]==0:
            raise BetterItemError('Nao existe proporcao a partir de %s = 0. Desvincule esse eixo antes de altera-lo.' % 'XYZ'[axis])
        factor=value/before[axis]
        for i,linked in enumerate(links):
            if linked:
                result[i]=value if i==axis else before[i]*factor
    return vector3(result)


def _inputs(origins,axes,reference,key):
    if len(axes)!=3 or not any(axes):
        raise BetterItemError('Marque pelo menos um eixo: X, Y ou Z.')
    if reference not in {'SELECTION','KEY'}:
        raise BetterItemError('Referencia de alinhamento invalida.')
    if reference=='KEY' and key not in origins:
        raise BetterItemError('O objeto-chave deve ser o objeto ativo e estar selecionado.')
    return {name:list(vector3(position)) for name,position in origins.items()}


def align_positions(origins,axes,reference,mode='MIN',key=None):
    result=_inputs(origins,axes,reference,key)
    if len(result)<2:
        raise BetterItemError('Selecione pelo menos dois objetos.')
    if mode not in {'MIN','CENTER','MAX'}:
        raise BetterItemError('Modo de alinhamento invalido.')
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
        raise BetterItemError('Selecione pelo menos %s objetos.' % (3 if reference=='SELECTION' else 2))
    if not math.isfinite(spacing):
        raise BetterItemError('Informe um espacamento finito.')
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
