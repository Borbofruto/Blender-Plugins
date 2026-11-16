"""No add-on: reproduce quit with no current window after file reload."""
import bpy,sys
from pathlib import Path
root=Path(__file__).parent
bpy.context.preferences.view.show_splash=False

def run():
 area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
 with bpy.context.temp_override(area=area,region=region):
  path=str(root/'no-addon-reopen.blend');bpy.ops.wm.save_as_mainfile(filepath=path);bpy.ops.wm.open_mainfile(filepath=path)
 print('NO ADDON; current window is None:',bpy.context.window is None,flush=True)
 if '--safe' in sys.argv:
  window=next(iter(bpy.context.window_manager.windows))
  with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
 else:bpy.ops.wm.quit_blender()
 return None
bpy.app.timers.register(run,first_interval=1)
