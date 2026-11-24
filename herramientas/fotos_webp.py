"""Baja las fotos de los pasteles (las que vienen de Bind), las achica y las guarda en WebP.

Lo corre GitHub sola con la acciÃ³n "Fotos WebP" (pestaÃ±a Actions del repositorio).
Resultado: img/w/<producto>.webp y en index.html la lÃ­nea FOTOS_WEBP queda en true.
"""
import io
import json
import os
import re
import sys
import urllib.request

from PIL import Image

PAGINA = 'index.html'
CARPETA = os.path.join('img', 'w')
LADO = 700        # pixeles del lado mÃ¡s largo
CALIDAD = 80

html = open(PAGINA, encoding='utf-8').read()
fotos = {}
for linea in html.splitlines():
    m_id = re.search(r'"id":\s*"([^"]+)"', linea)
    m_f = re.search(r'"foto":\s*"(https://[^"]+)"', linea)
    if m_id and m_f:
        fotos[m_id.group(1)] = m_f.group(1)
if not fotos:
    sys.exit('No encontrÃ© fotos en index.html')

os.makedirs(CARPETA, exist_ok=True)
ok, mal = 0, []
antes = despues = 0
for pid, url in sorted(fotos.items()):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        datos = urllib.request.urlopen(req, timeout=60).read()
        antes += len(datos)
        im = Image.open(io.BytesIO(datos))
        im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
        im.thumbnail((LADO, LADO), Image.LANCZOS)
        if im.mode == 'RGBA':
            fondo = Image.new('RGB', im.size, (255, 255, 255))
            fondo.paste(im, mask=im.split()[3])
            im = fondo
        destino = os.path.join(CARPETA, pid + '.webp')
        im.save(destino, 'WEBP', quality=CALIDAD, method=6)
        despues += os.path.getsize(destino)
        ok += 1
        print(f'âœ“ {pid}: {len(datos)//1024} KB â†’ {os.path.getsize(destino)//1024} KB')
    except Exception as e:  # una foto que falle no detiene las demÃ¡s
        mal.append(pid)
        print(f'âœ— {pid}: {e}')

print(f'\n{ok} fotos listas, {len(mal)} con error. Peso total: {antes//1024} KB â†’ {despues//1024} KB')
if ok:
    nuevo = html.replace('var FOTOS_WEBP=false;', 'var FOTOS_WEBP=true;')
    if nuevo != html:
        open(PAGINA, 'w', encoding='utf-8').write(nuevo)
        print('index.html: FOTOS_WEBP=true')
json.dump({'listas': ok, 'error': mal}, open(os.path.join(CARPETA, 'resumen.json'), 'w'), ensure_ascii=False)

