"""Markdown -> PDF (WeasyPrint). Usage : python3 md_vers_pdf.py <dossier> fichier1.md fichier2.md ...
Convertisseur volontairement petit : titres, paragraphes, listes, tableaux, citations, code, images, gras, italique, liens."""
import html
import re
import sys
from pathlib import Path

from weasyprint import HTML

CSS = """
@page { size: A4; margin: 20mm 17mm 20mm 17mm;
        @bottom-center { content: counter(page) " / " counter(pages); font: 8pt 'DejaVu Sans'; color: #64748b; }
        @top-right { content: string(titre-doc); font: 8pt 'DejaVu Sans'; color: #64748b; } }
html { font: 9.6pt/1.45 'DejaVu Sans', 'Liberation Sans', sans-serif; color: #0f172a; }
h1 { font-size: 20pt; color: #1f3864; border-bottom: 2px solid #2dd4bf; padding-bottom: 6px; margin: 0 0 14px; string-set: titre-doc content(); }
h2 { font-size: 14pt; color: #1f3864; margin: 20px 0 6px; break-after: avoid; }
h3 { font-size: 11.5pt; color: #0d9488; margin: 14px 0 4px; break-after: avoid; }
h4 { font-size: 10.2pt; color: #1f3864; margin: 10px 0 3px; break-after: avoid; }
h5, h6 { font-size: 9.6pt; color: #334155; margin: 8px 0 3px; break-after: avoid; }
p { margin: 5px 0 7px; }
ul, ol { margin: 4px 0 8px 18px; padding: 0; } li { margin: 2px 0; }
blockquote { margin: 8px 0; padding: 6px 12px; border-left: 3px solid #2dd4bf; background: #f4f7fa; color: #334155; }
blockquote p { margin: 3px 0; }
code { font: 8.4pt 'DejaVu Sans Mono', monospace; background: #eef2f7; padding: 0 3px; border-radius: 3px; }
pre { font: 8pt/1.35 'DejaVu Sans Mono', monospace; background: #0b1220; color: #e2e8f0; padding: 8px 10px; border-radius: 4px; white-space: pre-wrap; }
pre code { background: none; color: inherit; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 8.6pt; break-inside: auto; }
th { background: #0b1220; color: #fff; text-align: left; padding: 5px 6px; font-weight: 600; }
td { border: 1px solid #dbe3ec; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f7f9fc; }
tr { break-inside: avoid; }
img { max-width: 100%; max-height: 120mm; display: block; margin: 8px auto; }
hr { border: 0; border-top: 1px solid #cbd5e1; margin: 14px 0; }
a { color: #0d9488; text-decoration: none; }
"""


def inline(t: str, base: Path) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img alt="{m.group(1)}" src="{(base / m.group(2)).as_uri()}">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return t


def convertir(texte: str, base: Path) -> str:
    sortie, lignes, i = [], texte.split("\n"), 0
    while i < len(lignes):
        l = lignes[i]
        if l.strip().startswith("```"):
            bloc, i = [], i + 1
            while i < len(lignes) and not lignes[i].strip().startswith("```"):
                bloc.append(html.escape(lignes[i]))
                i += 1
            sortie.append("<pre><code>" + "\n".join(bloc) + "</code></pre>")
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", l)
        if m:
            n = len(m.group(1))
            sortie.append(f"<h{n}>{inline(m.group(2), base)}</h{n}>")
            i += 1
            continue
        if re.match(r"^\s*---+\s*$", l):
            sortie.append("<hr>")
            i += 1
            continue
        if l.startswith("|"):
            bloc = []
            while i < len(lignes) and lignes[i].startswith("|"):
                bloc.append(lignes[i])
                i += 1
            cellules = [[c.strip() for c in b.strip().strip("|").split("|")] for b in bloc]
            cellules = [c for c in cellules if not all(re.fullmatch(r":?-{2,}:?", x) for x in c)]
            h = "<table><thead><tr>" + "".join(f"<th>{inline(c, base)}</th>" for c in cellules[0]) + "</tr></thead><tbody>"
            for r in cellules[1:]:
                h += "<tr>" + "".join(f"<td>{inline(c, base)}</td>" for c in r) + "</tr>"
            sortie.append(h + "</tbody></table>")
            continue
        if l.startswith(">"):
            bloc = []
            while i < len(lignes) and lignes[i].startswith(">"):
                bloc.append(re.sub(r"^>\s?", "", lignes[i]))
                i += 1
            sortie.append("<blockquote>" + convertir("\n".join(bloc), base) + "</blockquote>")
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", l)
        if m:
            ordonnee = m.group(2)[0].isdigit()
            items = []
            while i < len(lignes):
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lignes[i])
                if not mm:
                    break
                items.append(inline(mm.group(3), base))
                i += 1
            tag = "ol" if ordonnee else "ul"
            sortie.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
            continue
        if not l.strip():
            i += 1
            continue
        para = [l]
        i += 1
        while i < len(lignes) and lignes[i].strip() and not re.match(r"^(#{1,6}\s|\||>|```|\s*[-*]\s|\s*\d+\.\s|---)", lignes[i]):
            para.append(lignes[i])
            i += 1
        sortie.append("<p>" + inline(" ".join(para), base) + "</p>")
    return "\n".join(sortie)


dossier = Path(sys.argv[1])
for nom in sys.argv[2:]:
    src = dossier / nom
    corps = convertir(src.read_text(encoding="utf-8"), src.parent)
    page = f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{corps}</body></html>"
    sortie = src.with_suffix(".pdf")
    HTML(string=page, base_url=str(src.parent)).write_pdf(str(sortie))
    print(sortie.name, sortie.stat().st_size // 1024, "Ko")
