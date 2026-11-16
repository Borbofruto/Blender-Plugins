"""Check the existing 173 fixture in a fresh process; run after that test.

--source PATH selects the parent of better_item; --fixture PATH selects the
saved test_better_item_173.blend. Without arguments use repository conventions.
"""
import sys
import json
from pathlib import Path

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent
source = sys.argv[sys.argv.index('--source') + 1] if '--source' in sys.argv else str(root.parents[1] / 'src')
fixture = Path(sys.argv[sys.argv.index('--fixture') + 1]) if '--fixture' in sys.argv else root / 'test_better_item_173.blend'
sys.path.insert(0, source)
import bpy
import addon_utils

addon_utils.enable('better_item')
assert fixture.is_file(), 'Run test_better_item_173.py before this fresh-process check'
bpy.ops.wm.open_mainfile(filepath=str(fixture))
s = bpy.context.scene.better_item
assert s.distribution_method == 'ENDPOINT' and s.distribution_mode == 'VOLUME'
assert not s.distribution_live
s.distribution_method = 'OFFSET'
assert s.distribution_mode == 'GEOMETRY'
s.distribution_method = 'ENDPOINT'
assert s.distribution_mode == 'VOLUME'
result = dict(passed=True, blender=bpy.app.version_string, fixture=fixture.name,
              endpoint='VOLUME', offset='GEOMETRY', live=False, fresh_process=True)
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('177 FRESH PLACEMENT PERSISTENCE PASSED', json.dumps(result))
