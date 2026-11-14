# SPDX-License-Identifier: GPL-3.0-or-later
"""User-facing status, kept separate from technical support details."""
import textwrap
import re
import traceback
from .math_core import BetterItemError,ReferencePending

_GUIDANCE={
    'BI-F005':('Choose a stable orientation.','The reference axes are too close to parallel. Change the source rotation or apply an independent Frame.'),
    'BI-T006':('That position could not be retained.','Reduce large object or parent offsets, or use a closer reference. The operation was rolled back.'),
    'BI-T008':('Linked axes need a nonzero starting value.','Unlink the edited axis, enter a resolvable nonzero value, then link it again.'),
    'BI-T009':('The reference follows the object being edited.','Apply the relevant Frame component to make it independent, then retry. The operation was rolled back.'),
    'BI-T012':('The requested size could not be retained.','Recenter large mesh coordinates or use a better-conditioned reference. The operation was rolled back.'),
    'BI-M003':('The Better Item geometry stage was edited.','Undo the node changes or restore its original node group before editing Dimensions.'),
    'BI-M005':('Realize instances before measuring geometry.','Add Realize Instances upstream in Geometry Nodes so all geometry can be measured.'),
}


class Diagnostic(str):
    """String compatibility for logs/tests, with explicit display severity."""
    def __new__(cls,error):
        if isinstance(error,cls):return error
        raw=str(error) if isinstance(error,(BetterItemError,str)) else '[BI-V002] %s: %s'%(type(error).__name__,error)
        severity=getattr(error,'severity','ERROR' if not isinstance(error,(BetterItemError,str)) else 'WARNING')
        if severity=='ERROR' and isinstance(error,BaseException) and error.__traceback__ is not None:
            raw+='\n'+''.join(traceback.format_exception(type(error),error,error.__traceback__))
        obj=super().__new__(cls,raw)
        obj.severity=severity
        cause=error
        while isinstance(getattr(cause,'__cause__',None),BetterItemError):cause=cause.__cause__
        display=str(cause) if isinstance(cause,BetterItemError) else raw
        obj.pending=isinstance(cause,ReferencePending)
        code=display[1:display.index(']')] if display.startswith('[BI-') and ']' in display else ''
        body=re.sub(r'\[BI-[A-Z]\d{3}\]\s*','',display).strip()
        obj.summary,obj.action=_GUIDANCE.get(code,(body,''))
        if obj.pending:obj.summary,obj.action=body,''
        subject=getattr(error,'subject',None) or getattr(cause,'subject',None)
        if subject:obj.summary='"%s": %s'%(subject,obj.summary)
        if obj.severity=='ERROR':obj.summary,obj.action='The operation could not be completed.','Open Details and include the diagnostic when reporting the problem.'
        return obj


def draw(layout,error,owner,*,clear_operator=None,width=34,configuration=False):
    message=Diagnostic(error)
    box=layout.box();row=box.row(align=True)
    row.alert=message.severity=='ERROR'
    refusal=(getattr(message,'operation',None)+' not applied') if getattr(message,'operation',None) else 'Not applied'
    row.label(text='Setup needed' if message.pending else 'Operation failed' if message.severity=='ERROR' else 'Reference unavailable' if configuration else refusal,
        icon='ERROR' if message.severity=='ERROR' else 'INFO')
    if clear_operator:row.operator(clear_operator,text='',icon='X')
    content=box.column(align=True)
    for paragraph in (message.summary,message.action):
        for line in textwrap.wrap(paragraph,width):content.label(text=line)
    if not message.pending:
        row=box.row(align=True)
        row.prop(owner,'show_diagnostic_details',text='Details',emboss=False,
            icon='TRIA_DOWN' if owner.show_diagnostic_details else 'TRIA_RIGHT')
        if owner.show_diagnostic_details:
            technical=box.column(align=True)
            for paragraph in str(message).splitlines():
                for line in textwrap.wrap(paragraph,width):technical.label(text=line)


def report(operator,error):
    message=Diagnostic(error)
    operator.report({message.severity},message.summary)
