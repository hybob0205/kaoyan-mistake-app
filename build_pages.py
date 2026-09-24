"""Prepare only public, static frontend files for GitHub Pages."""
from pathlib import Path
import shutil
import base64
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'
OUT.mkdir(exist_ok=True)
for name in ('index.html', 'app.css', 'app.js', 'manifest.webmanifest', 'sw.js'):
    shutil.copy2(ROOT / name, OUT / name)
(OUT / 'icons').mkdir(exist_ok=True)
for name in ('icon-192.png', 'icon-512.png', 'apple-touch-icon.png'):
    data = (ROOT / 'icons' / (name + '.b64')).read_text(encoding='ascii')
    (OUT / 'icons' / name).write_bytes(base64.b64decode(data))
(OUT / '.nojekyll').write_text('', encoding='utf-8')
(OUT / '404.html').write_text((OUT / 'index.html').read_text(encoding='utf-8'), encoding='utf-8')
print('Prepared static frontend in site/ (no .env or server code).')
