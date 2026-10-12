"""Genera 5EgenerIA_propuesta.pdf a partir de la web (docs/).

Estructura: portada (la del index) + índice (cabecera de la Presentación con las secciones
plegadas, que enlazan con cada sección) + secciones desplegadas. Usa Microsoft Edge en modo
headless para imprimir. Antes, regenera la web con `python build_web.py`.

    python build_web.py && python build_pdf.py
"""
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
PDF = ROOT / "5EgenerIA_propuesta.pdf"
EDGE = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]
OUT = Path(tempfile.gettempdir()) / "5egeneria_print.html"

index = (DOCS / 'index.html').read_text(encoding='utf-8')
pres = (DOCS / 'presentacion.html').read_text(encoding='utf-8')

# Portada: logo, título y frase del index
logo = re.search(r'<div class="logo-big".*?</div>', index, re.S).group(0)
title = re.search(r'<main class="landing-banner">.*?<h1>(.*?)</h1>', index, re.S).group(1)
lead = re.search(r'<p class="lead">(.*?)</p>', index, re.S).group(1)

# Presentación: cabecera e introducción
hero = re.search(r'<div class="hero">.*?</div></div>', pres, re.S).group(0)
# De/Para: solo en la portada (la web ya lo lleva en el index)
meta = re.search(r'<p class="meta landing-meta">(.*?)</p>', index, re.S).group(1)
meta = f'<p class="meta">{meta}</p>'
intro = re.search(r'<div class="intro">.*?</div>', pres, re.S).group(0)
main = re.search(r'<main class="wrap">(.*)</main>', pres, re.S).group(1)
cards = re.findall(r'<details class="card">.*?</details>(?=\s*(?:<details class="card">|$))', main, re.S)
if not cards:  # respaldo: partir por apertura de tarjeta
    cards = ['<details class="card">' + c for c in main.split('<details class="card">')[1:]]

# Índice: barras plegadas que enlazan con cada sección
index_bars = []
for c in cards:
    m = re.search(r'<h2 id="([^"]+)">(.*?)</h2>', c, re.S)
    sid, stitle = m.group(1), m.group(2)
    index_bars.append(f'<a class="card idx" href="#{sid}"><span class="idx-bar"><span class="idx-title">{stitle}</span><span class="chev">›</span></span></a>')

# Contenido: secciones y filas del itinerario abiertas
opened = []
for c in cards:
    c = c.replace('<details class="card">', '<details class="card" open>', 1)
    c = c.replace('<details class="itin-row">', '<details class="itin-row" open>')
    opened.append(c)

base = DOCS.as_uri() + '/'
html = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<base href="{base}">
<title>5EgenerIA · Propuesta de colaboración post-TFM</title>
<link rel="stylesheet" href="estilo.css">
<style>
  :root {{ --accent: #4a78a8; }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  @page {{ size: A4; margin: 14mm 12mm 16mm;
    @bottom-center {{ content: counter(page) " / " counter(pages); font: 9pt "Segoe UI", sans-serif; color: #64748b; }} }}
  @page cover {{ margin: 0; @bottom-center {{ content: none; }} }}
  html {{ font-size: 13px; }}
  body {{ background: #fff; }}
  .topbar, footer {{ display: none; }}
  .wrap {{ max-width: none; padding: 0; }}

  /* Portada */
  .cover {{ page: cover; break-after: page; width: 210mm; height: 297mm; position: relative; overflow: hidden;
           text-align: center;
           background: linear-gradient(to bottom, #0f2a4a 0%, #163a63 28%, #5f88b6 48%, #cfe0f1 62%, #fff 76%, #fff 100%); }}
  .cover-top, .cover-bottom {{ position: absolute; left: 22mm; right: 22mm; z-index: 1; }}
  .cover-top {{ top: 62mm; color: #fff; }}
  .cover-bottom {{ top: 104mm; color: #fff; }}
  .cover .logo-big {{ font-size: 64pt; margin: 0; }}
  .cover .logo-big .l::before {{ animation: none; background: #93c5fd; box-shadow: 0 0 .25em .06em rgba(147,197,253,.8); transform: scale(1); }}
  .cover h1 {{ font-size: 15pt; font-weight: 700; margin: 0 0 8mm; color: #93c5fd; letter-spacing: .5px; }}
  .cover .lead {{ font-size: 17pt; line-height: 1.45; margin: 0; }}
  .cover-meta {{ position: absolute; left: 22mm; right: 22mm; bottom: 24mm; z-index: 1; color: #475569; }}
  .cover-meta .meta {{ margin: 0; font-size: 11pt; line-height: 1.6; opacity: 1; }}

  /* Página 2: cabecera + índice de secciones plegadas */
  .portada2 {{ break-after: page; }}
  .hero {{ padding: 0 0 6mm; }}
  a.card.idx {{ display: block; text-decoration: none; margin: 0 0 9px; }}
  .idx-bar {{ display: flex; justify-content: space-between; align-items: center; background: var(--accent); color: #fff;
             border-radius: 4px; padding: 11px 18px; font-weight: 700; font-size: 1.25rem; }}
  .chev {{ font-size: 1.4rem; opacity: .85; }}

  /* Contenido */
  details.card {{ break-inside: auto; }}
  details.card > summary {{ break-after: avoid; }}
  details.card > summary::after, details.card > summary::marker {{ content: none; }}
  pre, img, tr, .itin-row > summary {{ break-inside: avoid; }}
  .itin-row > summary {{ break-after: avoid; }}
  pre {{ font-size: .78rem; white-space: pre; overflow: visible; }}
  .prose img {{ max-width: 86%; }}
</style>
</head>
<body>
<section class="cover">
  <div class="cover-top">{logo}</div>
  <div class="cover-bottom"><h1>{title}</h1><p class="lead">{lead}</p></div>
  <div class="cover-meta">{meta}</div>
</section>
<div class="portada2">
  {hero}
  <main class="wrap">{intro}{''.join(index_bars)}</main>
</div>
<main class="wrap">{''.join(opened)}</main>
</body>
</html>'''
OUT.write_text(html, encoding='utf-8')

edge = next((e for e in EDGE if e.exists()), None)
assert edge, "No se encuentra Microsoft Edge"
subprocess.run([str(edge), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--virtual-time-budget=4000", f"--print-to-pdf={PDF}", OUT.as_uri()],
               check=True, capture_output=True)
print("ok", PDF.name)
