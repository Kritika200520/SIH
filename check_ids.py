import re

with open(r'c:\Users\karti\OneDrive\Desktop\SIH-main\dashboard\app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

with open(r'c:\Users\karti\OneDrive\Desktop\SIH-main\dashboard\index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

ids_in_js = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", app_js))

missing_ids = []
for dom_id in ids_in_js:
    if f'id="{dom_id}"' not in index_html and f"id='{dom_id}'" not in index_html:
        missing_ids.append(dom_id)

if missing_ids:
    print('MISSING IDs in HTML:', missing_ids)
else:
    print('All IDs found!')

