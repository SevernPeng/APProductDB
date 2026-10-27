import json
import re
from pathlib import Path

page = Path('../output/ekit-ap361.html').read_text(encoding='utf-8')
match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', page, re.I | re.S)
print('payload found', bool(match))
if match:
    payload = json.loads(match.group(1))
    print('array entries', len(payload))
    for index, item in enumerate(payload):
        if isinstance(item, dict) and 'pictureUrl' in item:
            print('object index', index, 'keys', list(item.keys())[:25])
            for key in ('name', 'productName', 'model', 'modelName', 'pictureUrl', 'originalPictures', 'abbreviatedPicture'):
                ref = item.get(key)
                if isinstance(ref, int) and 0 <= ref < len(payload):
                    print(key, ref, repr(payload[ref])[:250])
