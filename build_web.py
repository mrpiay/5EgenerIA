"""Genera la web de 5EgenerIA (carpeta docs/) a partir de README.md.

Uso: python build_web.py
README.md es la fuente única: contiene toda la propuesta; cada título de nivel 1 (#) es una página,
en el orden de PAGES. Tras editar el texto, basta con volver a ejecutar el script.
"""
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
OUT = ROOT / "docs"

SOURCE = ROOT / "README.md"
# Color común de todas las páginas: azul suave (texto blanco legible sobre él).
ACCENT = "#4a78a8"

# Una entrada por cada título de nivel 1 de README.md, en el mismo orden: (archivo html, etiqueta del menú)
PAGES = [
    ("presentacion.html", "Presentación"),
]


def slugify(value, separator="-"):
    """Anclas al estilo de GitHub, para que los enlaces entre páginas sigan funcionando."""
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return value.replace(" ", separator)


def render(md_text):
    md_text = md_text.replace("\\\n", "<br>\n")  # salto de línea con barra invertida (estilo GitHub)
    html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": slugify}},
    )
    html = html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    html = re.sub(r'(<code class="language-algoritmo">)(.*?)(</code>)',
                  lambda m: m.group(1) + bold_algorithm(m.group(2)) + m.group(3), html, flags=re.S)
    return html


# Palabras clave de los algoritmos, en negrita como en los artículos (solo en el código, no en los comentarios ▷)
ALG_KEYWORDS = r"para cada|para|hasta que|repetir|si|devolver|salir del bucle|detener|GenerarFase|ValorarFase|AjustarReglas"
ALG_LABELS = r"Entrada:|Salida:|Recibe:|Devuelve:"


def bold_algorithm(code):
    lines = []
    for line in code.split("\n"):
        if re.match(r"(Algoritmo|Función) \d+\.", line):
            lines.append(f"<b>{line}</b>")
            continue
        line = re.sub(rf"^({ALG_LABELS})", r"<b>\1</b>", line)
        code_part, sep, comment = line.partition("▷")
        if re.match(r"\s*\d+\s", code_part):  # solo las líneas numeradas
            code_part = re.sub(rf"(?<![\wÀ-ÿ])({ALG_KEYWORDS})(?![\wÀ-ÿ])", r"<b>\1</b>", code_part)
        lines.append(code_part + sep + comment)
    return "\n".join(lines)


def split_page(html):
    """Separa título, resumen (primer blockquote o párrafo destacado) y secciones h2."""
    title = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1)
    html = re.sub(r"<h1[^>]*>.*?</h1>", "", html, count=1, flags=re.S)
    head, *rest = re.split(r"(?=<h2)", html)
    head = head.replace("<hr />", "")
    sections = []
    for part in rest:
        part = part.replace("<hr />", "")
        m = re.match(r'<h2 id="([^"]*)">(.*?)</h2>(.*)', part, re.S)
        sections.append((m.group(1), m.group(2), m.group(3)))
    return title, head, sections


NAME = '<span class="name">5E<span class="gener">gener</span><span class="ia">IA</span></span>'


def brand(html):
    """Muestra el nombre 5EgenerIA como en el logo, solo en el texto (no dentro de etiquetas)."""
    parts = re.split(r"(<[^>]+>)", html)
    return "".join(p if p.startswith("<") else p.replace("5EgenerIA", NAME) for p in parts)


def tiles(body):
    """Convierte los ### de una sección en fichas: título, descripción (primer párrafo) y desarrollo."""
    intro, *chunks = re.split(r"(?=<h3)", body)
    out = []
    for c in chunks:
        c = re.sub(r"<p>", '<p class="desc">', c, count=1)
        out.append(f'<div class="tile">{c}</div>')
    return intro + f'<div class="tiles">{"".join(out)}</div>'


OPEN_JS = """
// Si se llega con un enlace a una sección (#ancla), se abre su desplegable.
const abrir = () => {
  const t = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  const d = t && t.closest("details");
  if (d) { d.open = true; t.scrollIntoView(); }
};
addEventListener("hashchange", abrir);
abrir();
"""


def chunks():
    """Divide README.md en páginas: una por cada título de nivel 1."""
    text = re.sub(r"<!--.*?-->", "", SOURCE.read_text(encoding="utf-8"), flags=re.S)
    parts = [p.strip() for p in re.split(r"(?m)^(?=# )", text) if p.strip().startswith("# ")]
    assert len(parts) == len(PAGES), f"README.md tiene {len(parts)} páginas (#) y PAGES {len(PAGES)}"
    return [re.sub(r"\n---\s*$", "", p) for p in parts]


def fix_links(html, own, where):
    """Los enlaces #ancla que apuntan a otra página pasan a pagina.html#ancla."""
    def sub(m):
        a = m.group(1)
        return m.group(0) if a in own or a not in where else f'href="{where[a]}#{a}"'
    return re.sub(r'href="#([^"]+)"', sub, html)


def studies(body):
    """Itinerario de la Presentación: la tabla de estudios se convierte en filas desplegables.
    Cada fila muestra Estudio · Qué se investiga · Puerta; al abrirla, la descripción del ### correspondiente."""
    intro, *parts = re.split(r"(?=<h3)", body)
    if not parts:
        return body
    m = re.search(r'<div class="table-wrap"><table>.*?</table></div>', intro, re.S)
    rows = re.findall(r"<tr>\s*<td><strong>(E\d+ · .*?)</strong></td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
                      m.group(0), re.S) if m else []
    if not rows:  # solo la sección del itinerario; las demás se dejan tal cual
        return body
    texts = {}
    for part in parts:
        h = re.match(r'<h3[^>]*>(.*?)</h3>(.*)', part, re.S)
        texts[h.group(1).split(" · ")[0].strip()] = h.group(2)
    head = '<div class="itin-head"><span>Estudio</span><span>Qué se investiga</span><span>Puerta para continuar</span></div>'
    items = "".join(
        f'<details class="itin-row"><summary><strong>{name}</strong><span>{what}</span><span>{gate}</span></summary>'
        f'<div class="itin-body">{texts.get(name.split(" · ")[0].strip(), "")}</div></details>'
        for name, what, gate in rows
    )
    pre, _, post = intro.partition(m.group(0)) if m else (intro, "", "")
    return pre + f'<div class="itin">{head}{items}</div>' + post


def page_html(html, html_file, accent, first):
    title, head, sections = split_page(html)
    name, _, subtitle = title.partition(" — ")

    lead, meta = "", ""
    if first:
        # Propuesta: cabecera como las demás ("Propuesta" + "En breve") y De/Para debajo.
        # El título largo y la frase principal solo se muestran en la portada.
        subtitle = "Presentación"
        m = re.search(r"<p><strong>De:</strong>.*?</p>", head, re.S)
        if m:
            meta = m.group(0).replace("<p>", '<p class="meta">', 1)
            head = head.replace(m.group(0), "", 1)
        head = re.sub(r"<p><strong>(?!De:).*?</strong></p>", "", head, count=1, flags=re.S)
    # El blockquote "En breve" va a la cabecera.
    m = re.search(r"<blockquote>(.*?)</blockquote>", head, re.S)
    if m:
        lead = m.group(1)
        head = head.replace(m.group(0), "", 1)

    # El índice "Sección | De qué trata" no se muestra: aporta la descripción breve de cada sección.
    descs = {}
    m = re.search(r'<div class="table-wrap"><table>\s*<thead>\s*<tr>\s*<th>Sección</th>.*?</table></div>', head, re.S)
    if m:
        for sid, d in re.findall(r'<td><a href="#([^"]+)">.*?</a></td>\s*<td>(.*?)</td>', m.group(0), re.S):
            descs[sid] = d
        head = head.replace(m.group(0), "", 1)
    head = head.replace("<p><strong>Contenido</strong></p>", "")

    active = ' class="active"'
    links = [f'<a href="{h}"{active if h == html_file else ""}>{label}</a>' for h, label in PAGES]
    # Presentación y Desarrollo son espacios separados: para pasar de uno a otro se vuelve a la portada (con el logo).
    nav = "" if first else "".join(links[1:])
    if first:
        # Presentación: cada sección es desplegable y está cerrada al cargar; un enlace a #sección la abre.
        cards = "".join(
            f'<details class="card"><summary><h2 id="{sid}">{stitle}</h2></summary>'
            f'<div class="card-body prose">{studies(body)}</div></details>'
            for sid, stitle, body in sections
        )
    else:
        # Desarrollo: cada sección es desplegable, cerrada al cargar; junto al nombre, su descripción breve.
        cards = "".join(
            f'<details class="card"><summary><h2 id="{sid}">{stitle}</h2>'
            f'<span class="sum-desc">{descs.get(sid, "Fuentes citadas en la propuesta." if sid == "referencias" else "")}</span></summary><div class="card-body">'
            f'{tiles(body)}</div></details>'
            for sid, stitle, body in sections
        )
    hero = f"""<div class="hero"><div class="wrap">
  <h1>{subtitle or name}</h1>
  <div class="lead">{brand(lead)}</div>
  {meta}
</div></div>"""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>5EgenerIA · {subtitle or name}</title>
<link rel="stylesheet" href="estilo.css">
<style>:root {{ --accent: {accent}; }}</style>
</head>
<body>
<header class="topbar"><div class="wrap">
  <a class="brand" href="index.html">5E<span class="gener">gener</span><span class="ia">IA</span></a>
  <nav>{nav}</nav>
</div></header>
{hero}
<main class="wrap">
  <div class="intro">{brand(head)}</div>
  {brand(cards)}
</main>
<footer><div class="wrap">{NAME} · Javier Piay Pombo · Propuesta de colaboración post-TFM</div></footer>
<script>{OPEN_JS}</script>
</body>
</html>
"""


SKY_JS = """
(() => {
  // Campo de estrellas que avanza hacia el espectador, muy despacio.
  // Lejos: puntos grises y pequeños; al acercarse crecen y se iluminan en blanco.
  const c = document.getElementById("sky"), ctx = c.getContext("2d");
  const N = 260, SPEED = 0.0005, still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let w, h, f, dpr, stars = [];
  const star = (z) => ({ x: Math.random() * 2 - 1, y: Math.random() * 2 - 1, z: z ?? Math.random() });
  const resize = () => {
    dpr = window.devicePixelRatio || 1;
    w = c.width = innerWidth * dpr; h = c.height = innerHeight * dpr;
    f = Math.max(w, h) * 0.5;
  };
  const draw = () => {
    ctx.clearRect(0, 0, w, h);
    for (const s of stars) {
      if (!still) s.z -= SPEED;
      const x = w / 2 + (s.x / s.z) * f, y = h / 2 + (s.y / s.z) * f;
      if (s.z <= 0.02 || x < 0 || x > w || y < 0 || y > h) { Object.assign(s, star(1)); continue; }
      const k = 1 - s.z;                      // 0 lejos, 1 cerca
      const g = Math.round(150 + 105 * k);    // gris -> blanco
      ctx.fillStyle = `rgba(${g},${g + 5 > 255 ? 255 : g + 5},${g + 15 > 255 ? 255 : g + 15},${0.25 + 0.75 * k})`;
      ctx.beginPath();
      ctx.arc(x, y, (0.4 + 2.2 * k * k) * dpr, 0, Math.PI * 2);
      ctx.fill();
    }
    if (!still) requestAnimationFrame(draw);
  };
  resize(); addEventListener("resize", resize);
  stars = Array.from({ length: N }, () => star());
  draw();
})();
"""


def landing_html(html):
    """Portada: solo el banner, centrado y a pantalla completa, con botones a las páginas."""
    title = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1).partition(" — ")[2]
    tagline = re.search(r"<p><strong>(?!De:)(.*?)</strong></p>", html, re.S).group(1)
    buttons = f'<a href="{PAGES[0][0]}">Presentación</a>'
    # Un punto sobre cada letra de GENER: las cinco fases que la IA recorre en secuencia.
    gener = "".join(f'<span class="l" style="--i:{i}">{c}</span>' for i, c in enumerate("gener"))
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>5EgenerIA · {title}</title>
<link rel="stylesheet" href="estilo.css">
</head>
<body class="landing">
<canvas id="sky" class="sky" aria-hidden="true"></canvas>
<main class="landing-banner">
  <div class="logo-big" aria-label="5EgenerIA">5E<span class="gener">{gener}</span><span class="ia">IA</span></div>
  <h1>{title}</h1>
  <p class="lead">{tagline}</p>
  <nav class="landing-nav">{buttons}</nav>
</main>
<script>{SKY_JS}</script>
</body>
</html>
"""


def main():
    OUT.mkdir(exist_ok=True)
    htmls = [render(c) for c in chunks()]
    ids = [set(re.findall(r'id="([^"]+)"', h)) for h in htmls]
    where = {}
    for (html_file, _), page_ids in zip(PAGES, ids):
        for a in page_ids:
            where.setdefault(a, html_file)
    (OUT / "index.html").write_text(landing_html(htmls[0]), encoding="utf-8")
    print("ok index.html")
    (OUT / "estilo.css").write_text((ROOT / "web_estilo.css").read_text(encoding="utf-8"), encoding="utf-8")
    for img in ROOT.glob("*.svg"):  # diagramas referenciados desde README.md
        (OUT / img.name).write_text(img.read_text(encoding="utf-8"), encoding="utf-8")
    for i, ((html_file, _), html) in enumerate(zip(PAGES, htmls)):
        html = fix_links(html, ids[i], where)
        (OUT / html_file).write_text(page_html(html, html_file, ACCENT, first=(i == 0)), encoding="utf-8")
        print("ok", html_file)


if __name__ == "__main__":
    main()
