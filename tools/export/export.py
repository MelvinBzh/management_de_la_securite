#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export des rapports - générateur de rapport exécutif pour les analyses."""

import argparse
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def markdown_vers_html(md: str) -> str:
    """
    Convertit du markdown minimal en HTML sans évaluer de contenu.
    
    Échappe strictement le texte avec html.escape. Seuls les éléments
    de structure markdown sont interprétés :
    - # → h1..h3
    - | → tables
    - - → listes à puces
    - ``` ``` fences → <pre><code>
    - > → blockquote
    - ** → strong
    - ` → code inline
    """
    lines = md.split('\n')
    html_lines = []
    in_code_block = False
    code_lang = ''
    i = 0
    while i < len(lines):
        line = lines[i]
        # Gestion des blocs de code ``` 
        stripped = line.strip()
        if stripped.startswith('```'):
            if not in_code_block:
                in_code_block = True
                lang = stripped[3:].strip()
                code_lang = f' class="language-{html.escape(lang)}"' if lang else ''
                html_lines.append(f'<pre><code{code_lang}>')
            else:
                in_code_block = False
                html_lines.append('</code></pre>')
            i += 1
            continue
        if in_code_block:
            # Échapper le contenu du bloc de code
            html_lines.append(html.escape(line))
            i += 1
            continue
        # Headers
        if stripped.startswith('# '):
            html_lines.append(f'<h1>{html.escape(stripped[2:])}</h1>')
            i += 1
            continue
        elif stripped.startswith('## '):
            html_lines.append(f'<h2>{html.escape(stripped[3:])}</h2>')
            i += 1
            continue
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{html.escape(stripped[4:])}</h3>')
            i += 1
            continue
        # Horizontal rule
        elif stripped == '---' or stripped == '***' or stripped == '___':
            html_lines.append('<hr>')
            i += 1
            continue
        # Blockquote
        elif stripped.startswith('>'):
            content = stripped[1:].strip()
            html_lines.append(f'<blockquote>{html.escape(content)}</blockquote>')
            i += 1
            continue
        # Table detection
        elif '|' in stripped and not stripped.startswith('|---') and not stripped.startswith('---|') and not stripped.replace('-', '').replace('|', '').replace(':', '').strip() == '':
            # Check if it's not just separator line
            # Look ahead for separator
            is_separator = all(c in '-:|' for c in stripped)
            if is_separator:
                i += 1
                continue
            # Start of table - collect table
            table_lines = []
            # Add current line if it looks like table row
            table_lines.append(stripped)
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line == '':
                    break
                if '|' in next_line:
                    # Check if separator
                    if all(c in '-:|' for c in next_line):
                        j += 1
                        continue  # skip separator
                    table_lines.append(next_line)
                    j += 1
                else:
                    break
            i = j
            # Render table
            html_lines.append('<table>')
            for idx, tline in enumerate(table_lines):
                cells = [c.strip() for c in tline.split('|')]
                # Remove empty cells at ends
                if cells and cells[0] == '':
                    cells = cells[1:]
                if cells and cells[-1] == '':
                    cells = cells[:-1]
                if idx == 0:  # header
                    html_lines.append('<thead><tr>')
                    for cell in cells:
                        # Process inline formatting in header/cells
                        cell_html = _format_inline(cell)
                        html_lines.append(f'<th>{cell_html}</th>')
                    html_lines.append('</tr></thead><tbody>')
                else:
                    html_lines.append('<tr>')
                    for cell in cells:
                        cell_html = _format_inline(cell)
                        html_lines.append(f'<td>{cell_html}</td>')
                    html_lines.append('</tr>')
            html_lines.append('</tbody></table>')
            continue
        # Unordered list
        elif stripped.startswith('- ') or stripped.startswith('* '):
            # Collect consecutive list items
            list_items = []
            j = i
            while j < len(lines):
                nxt = lines[j].strip()
                if nxt.startswith('- ') or nxt.startswith('* '):
                    list_items.append(nxt[2:].strip())
                    j += 1
                elif nxt == '':
                    j += 1  # skip empty line in list
                    # but be conservative - break if followed by non-list
                    k = j
                    # peek
                    pass
                else:
                    break
            i = j
            html_lines.append('<ul>')
            for item in list_items:
                html_lines.append(f'<li>{_format_inline(item)}</li>')
            html_lines.append('</ul>')
            continue
        # Empty line
        elif stripped == '':
            html_lines.append('<br>')
            i += 1
            continue
        # Paragraph
        else:
            html_lines.append(f'<p>{_format_inline(stripped)}</p>')
            i += 1
            continue
    return '\n'.join(html_lines)


def _format_inline(text: str) -> str:
    """Formate le texte inline (bold, code)."""
    # Escape first
    result = html.escape(text)
    # Bold **text**
    # Simple approach
    while '**' in result:
        # Replace first occurrence pattern
        start = result.find('**')
        if start == -1:
            break
        end = result.find('**', start + 2)
        if end == -1:
            break
        bold_content = result[start + 2:end]
        result = result[:start] + f'<strong>{bold_content}</strong>' + result[end + 2:]
    # Code inline `text`
    while '`' in result:
        start = result.find('`')
        if start == -1:
            break
        end = result.find('`', start + 1)
        if end == -1:
            break
        code_content = result[start + 1:end]
        result = result[:start] + f'<code>{code_content}</code>' + result[end + 1:]
    return result


def exporter(dossier: str, format: str = "pdf", out: Optional[str] = None) -> Path:
    """
    Exporte le rapport d'analyse dans le format demandé.
    
    Args:
        dossier: Chemin vers le dossier d'analyse
        format: Format d'export (md|html|pdf|json)
        out: Dossier de sortie (défaut = dossier d'analyse)
    
    Returns:
        Chemin vers le fichier généré
    
    Raises:
        ValueError: Si le dossier est inexistant ou si des fichiers requis sont manquants
    """
    dossier_path = Path(dossier).resolve()
    
    # Vérifier que le dossier existe
    if not dossier_path.exists() or not dossier_path.is_dir():
        raise ValueError(f"Le dossier d'analyse n'existe pas : {dossier}")
    
    # Fichiers requis
    synthese_path = dossier_path / "SYNTHESE.md"
    registre_md_path = dossier_path / "registre-risques.md"
    
    if not synthese_path.exists():
        raise ValueError(f"Fichier manquant : SYNTHESE.md dans {dossier}")
    if not registre_md_path.exists():
        raise ValueError(f"Fichier manquant : registre-risques.md dans {dossier}")
    
    # Déterminer le dossier de sortie
    if out is None:
        out_path = dossier_path
    else:
        out_path = Path(out).resolve()
        out_path.mkdir(parents=True, exist_ok=True)
    
    format_lower = format.lower()
    
    if format_lower == "md":
        return _export_md(synthese_path, registre_md_path, out_path)
    elif format_lower == "html":
        return _export_html(synthese_path, registre_md_path, out_path)
    elif format_lower == "pdf":
        return _export_pdf(synthese_path, registre_md_path, out_path, dossier_path)
    elif format_lower == "json":
        return _export_json(dossier_path, out_path)
    else:
        raise ValueError(f"Format non supporté : {format}")


def _export_md(synthese_path: Path, registre_md_path: Path, out_path: Path) -> Path:
    """Génère le rapport exécutif au format Markdown."""
    synthese = synthese_path.read_text(encoding='utf-8')
    registre_md = registre_md_path.read_text(encoding='utf-8')
    
    # Construire le rapport
    lines = []
    lines.append(synthese.rstrip())
    lines.append('')
    lines.append('## Registre des risques (14 risques)')
    lines.append('')
    lines.append(registre_md.rstrip())
    lines.append('')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('**Note :** Validation humaine des risques (valide_par) incluse dans le registre.')
    lines.append('Sources : référencées dans le registre des risques (ISO27002, STRIDE, LINDDUN, ATT&CK, ANSSI, CNIL).')
    lines.append('')
    
    rapport_content = '\n'.join(lines)
    output_file = out_path / 'rapport-executif.md'
    output_file.write_text(rapport_content, encoding='utf-8')
    return output_file


def _get_valide_par_info(dossier_path: Path) -> str:
    """Récupère les informations de validation humaine."""
    try:
        registre_json_path = dossier_path / "registre_risques.json"
        if registre_json_path.exists():
            data = json.loads(registre_json_path.read_text(encoding='utf-8'))
            validateurs = set()
            for r in data.get('risques', []):
                if 'valide_par' in r:
                    validateurs.add(r['valide_par'])
            if validateurs:
                return ', '.join(sorted(validateurs))
    except Exception:
        pass
    return "Validation humaine (valide_par) - voir registre des risques"


def _export_html(synthese_path: Path, registre_md_path: Path, out_path: Path) -> Path:
    """Génère le rapport exécutif au format HTML."""
    synthese = synthese_path.read_text(encoding='utf-8')
    registre_md = registre_md_path.read_text(encoding='utf-8')
    
    # Construire le contenu markdown
    md_parts = []
    md_parts.append(synthese.rstrip())
    md_parts.append('')
    md_parts.append('## Registre des risques (14 risques)')
    md_parts.append('')
    md_parts.append(registre_md.rstrip())
    md_parts.append('')
    md_parts.append('---')
    md_parts.append('')
    md_parts.append('**Note :** Validation humaine (valide_par) incluse dans le registre.')
    md_parts.append('Sources : référencées dans le registre des risques (ISO27002, STRIDE, LINDDUN, ATT&CK, ANSSI, CNIL).')
    md_parts.append('')
    
    md_content = '\n'.join(md_parts)
    body_html = markdown_vers_html(md_content)
    
    # CSS print-grade avec DejaVu Sans et numérotation de pages
    style = '''
    @page {
        size: A4;
        margin: 2cm 1.5cm 2cm 1.5cm;
        @bottom-center {
            content: counter(page);
            font-family: 'DejaVu Sans', 'Arial', sans-serif;
            font-size: 10pt;
        }
    }
    @media screen {
        body {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
    }
    body {
        font-family: 'DejaVu Sans', 'Arial', 'Helvetica', sans-serif;
        line-height: 1.6;
        color: #333;
        font-size: 10pt;
    }
    h1 {
        font-size: 18pt;
        margin-top: 20pt;
        margin-bottom: 10pt;
        page-break-after: avoid;
    }
    h2 {
        font-size: 14pt;
        margin-top: 16pt;
        margin-bottom: 8pt;
        page-break-after: avoid;
    }
    h3 {
        font-size: 12pt;
        margin-top: 12pt;
        margin-bottom: 6pt;
        page-break-after: avoid;
    }
    p {
        margin: 6pt 0;
        text-align: justify;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 12pt 0;
        font-size: 8pt;
        page-break-inside: auto;
    }
    tr {
        page-break-inside: avoid;
        page-break-after: auto;
    }
    th, td {
        border: 1px solid #333;
        padding: 4pt 6pt;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    code {
        font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
        background-color: #f5f5f5;
        padding: 1pt 3pt;
        font-size: 9pt;
    }
    pre {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        padding: 8pt;
        overflow-x: auto;
        margin: 8pt 0;
        page-break-inside: avoid;
    }
    pre code {
        background-color: transparent;
        padding: 0;
        font-size: 8pt;
    }
    blockquote {
        border-left: 3pt solid #999;
        margin: 8pt 0;
        padding-left: 8pt;
        font-style: italic;
        color: #555;
    }
    ul {
        margin: 6pt 0;
        padding-left: 18pt;
    }
    li {
        margin: 3pt 0;
    }
    hr {
        border: none;
        border-top: 1px solid #ccc;
        margin: 12pt 0;
    }
    '''
    
    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Exécutif - Analyse de Risques</title>
    <style>
{style}
    </style>
</head>
<body>
{body_html}
</body>
</html>'''
    
    output_file = out_path / 'rapport-executif.html'
    output_file.write_text(html_content, encoding='utf-8')
    return output_file


def _export_pdf(synthese_path: Path, registre_md_path: Path, out_path: Path, dossier_path: Path) -> Path:
    """Génère le rapport exécutif au format PDF via WeasyPrint."""
    try:
        import weasyprint
    except ImportError:
        raise ImportError("weasyprint n'est pas installé")
    
    # Générer d'abord le HTML
    synthese = synthese_path.read_text(encoding='utf-8')
    registre_md = registre_md_path.read_text(encoding='utf-8')
    
    md_parts = []
    md_parts.append(synthese.rstrip())
    md_parts.append('')
    md_parts.append('## Registre des risques (14 risques)')
    md_parts.append('')
    md_parts.append(registre_md.rstrip())
    md_parts.append('')
    md_parts.append('---')
    md_parts.append('')
    md_parts.append('**Note :** Validation humaine (valide_par) incluse dans le registre.')
    md_parts.append('Sources : référencées dans le registre des risques (ISO27002, STRIDE, LINDDUN, ATT&CK, ANSSI, CNIL).')
    md_parts.append('')
    
    md_content = '\n'.join(md_parts)
    body_html = markdown_vers_html(md_content)
    
    style = '''
    @page {
        size: A4;
        margin: 2cm 1.5cm 2cm 1.5cm;
        @bottom-center {
            content: counter(page);
            font-family: 'DejaVu Sans', 'Arial', sans-serif;
            font-size: 10pt;
        }
    }
    body {
        font-family: 'DejaVu Sans', 'Arial', 'Helvetica', sans-serif;
        line-height: 1.6;
        color: #333;
        font-size: 10pt;
    }
    h1 { font-size: 18pt; margin-top: 20pt; margin-bottom: 10pt; page-break-after: avoid; }
    h2 { font-size: 14pt; margin-top: 16pt; margin-bottom: 8pt; page-break-after: avoid; }
    h3 { font-size: 12pt; margin-top: 12pt; margin-bottom: 6pt; page-break-after: avoid; }
    p { margin: 6pt 0; text-align: justify; }
    table { border-collapse: collapse; width: 100%; margin: 12pt 0; font-size: 7pt; page-break-inside: auto; }
    tr { page-break-inside: avoid; page-break-after: auto; }
    th, td { border: 1px solid #333; padding: 3pt 4pt; text-align: left; vertical-align: top; }
    th { background-color: #f0f0f0; font-weight: bold; }
    code { font-family: 'DejaVu Sans Mono', 'Courier New', monospace; background-color: #f5f5f5; padding: 1pt 2pt; font-size: 8pt; }
    pre { background-color: #f5f5f5; border: 1px solid #ddd; padding: 6pt; overflow-x: auto; margin: 6pt 0; page-break-inside: avoid; }
    pre code { background-color: transparent; padding: 0; font-size: 7pt; }
    blockquote { border-left: 3pt solid #999; margin: 6pt 0; padding-left: 6pt; font-style: italic; color: #555; }
    ul { margin: 4pt 0; padding-left: 16pt; }
    li { margin: 2pt 0; }
    hr { border: none; border-top: 1px solid #ccc; margin: 10pt 0; }
    '''
    
    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Rapport Exécutif</title>
    <style>{style}</style>
</head>
<body>
{body_html}
</body>
</html>'''
    
    html = weasyprint.HTML(string=html_content)
    output_file = out_path / 'rapport-executif.pdf'
    html.write_pdf(output_file)
    return output_file


def _export_json(dossier_path: Path, out_path: Path) -> Path:
    """Génère le rapport exécutif au format JSON."""
    registre_json_path = dossier_path / "registre_risques.json"
    synthese_path = dossier_path / "SYNTHESE.md"
    
    registre_data = {}
    if registre_json_path.exists():
        registre_data = json.loads(registre_json_path.read_text(encoding='utf-8'))
    
    synthese = ""
    if synthese_path.exists():
        synthese = synthese_path.read_text(encoding='utf-8')
    
    # Déterminer le cas
    cas = ""
    if isinstance(registre_data, dict):
        cas = registre_data.get('cas', '') or registre_data.get('titre', '') or registre_data.get('nom', '')
    if not cas:
        # Essayer de lire depuis description
        desc_path = dossier_path / "00-description.md"
        if desc_path.exists():
            desc = desc_path.read_text(encoding='utf-8')
            # Chercher le titre
            for line in desc.split('\n'):
                if line.strip().startswith('#'):
                    cas = line.strip('# ').strip()
                    break
    
    rapport_json = {
        "cas": cas,
        "genere_le": datetime.now().isoformat(),
        "registre": registre_data,
        "synthese": synthese,
        "export_formats": ["md", "html", "pdf", "json"]
    }
    
    output_file = out_path / 'rapport-executif.json'
    output_file.write_text(json.dumps(rapport_json, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Export des rapports d\'analyse')
    parser.add_argument('dossier_analyse', help='Dossier contenant les fichiers d\'analyse')
    parser.add_argument('--format', choices=['md', 'html', 'pdf', 'json'], default='pdf',
                        help='Format d\'export (défaut: pdf)')
    parser.add_argument('--out', help='Dossier de sortie (défaut: dossier d\'analyse)')
    
    args = parser.parse_args()
    
    try:
        exporter(args.dossier_analyse, args.format, args.out)
        sys.exit(0)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()


def _export_json(dossier_path: Path, out_path: Path) -> Path:
    """Génère le rapport exécutif au format JSON."""
    registre_json_path = dossier_path / "registre_risques.json"
    synthese_path = dossier_path / "SYNTHESE.md"
    
    registre_data = {}
    if registre_json_path.exists():
        registre_data = json.loads(registre_json_path.read_text(encoding='utf-8'))
    
    synthese = ""
    if synthese_path.exists():
        synthese = synthese_path.read_text(encoding='utf-8')
    
    # Déterminer le cas
    cas = ""
    if isinstance(registre_data, dict):
        cas = registre_data.get('cas', '') or registre_data.get('titre', '') or registre_data.get('nom', '') or registre_data.get('analyse', '')
    if not cas:
        # Essayer de lire depuis description
        desc_path = dossier_path / "00-description.md"
        if desc_path.exists():
            desc = desc_path.read_text(encoding='utf-8')
            for line in desc.split('\n'):
                if line.strip().startswith('#'):
                    cas = line.strip('# ').strip()
                    break
    if not cas:
        cas = dossier_path.name
    
    rapport_json = {
        "cas": cas,
        "genere_le": datetime.now().isoformat(),
        "registre": registre_data,
        "synthese": synthese,
        "export_formats": ["md", "html", "pdf", "json"]
    }
    
    output_file = out_path / 'rapport-executif.json'
    output_file.write_text(json.dumps(rapport_json, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_file
