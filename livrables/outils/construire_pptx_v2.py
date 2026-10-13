"""Construit Soutenance_E21_V2.pptx à partir du PPT V1 (école) : slides gardées, retouchées, nouvelles, dans le même style."""
import copy
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

V1 = Path(sys.argv[1])
IMG = Path(sys.argv[2])          # dossier des diagrammes PNG
SORTIE = Path(sys.argv[3])

# --- palette et polices de la V1 ---------------------------------------------------------------------------------------
NUIT, ENCRE, GRIS, GRIS_CLAIR = "0B1220", "0F172A", "475569", "94A3B8"
TEAL, TEAL_FONCE = "2DD4BF", "0D9488"
CARTE, CARTE_SOMBRE, BORD = "F4F7FA", "131D31", "E2E8F0"
VERT, VERT_FOND, ROUGE, ROUGE_FOND = "16A34A", "EAF7EE", "DC2626", "FDECEC"
AMBRE, AMBRE_FOND = "B45309", "FEF3C7"
TEXTE_CLAIR = "CBD5E1"
SANS, SEMI, MONO = "Segoe UI", "Segoe UI Semibold", "Consolas"
PIED = "E21 · Agents IA & analyse de risques"


def rgb(h):
    return RGBColor.from_string(h)


prs = Presentation(str(V1))
ORIGINE = list(prs.slides)          # les 29 slides de la V1 (index 0..28)
LAYOUT = prs.slide_layouts[0]


# --- primitives --------------------------------------------------------------------------------------------------------
def nouvelle_slide(sombre=False):
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(NUIT if sombre else "FFFFFF")
    return s


def vider(slide, garder=()):
    """Supprime les formes d'une slide (sauf celles dont le texte est dans `garder`)."""
    for sh in list(slide.shapes):
        t = sh.text_frame.text.strip() if sh.has_text_frame else ""
        if t in garder:
            continue
        sh._element.getparent().remove(sh._element)


def texte(slide, x, y, w, h, contenu, taille=11, couleur=ENCRE, police=SANS, gras=False, align=None, ancre=None, interligne=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = ancre or MSO_ANCHOR.TOP
    paragraphes = contenu if isinstance(contenu, list) else str(contenu).split("\n")
    for i, ligne in enumerate(paragraphes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align:
            p.alignment = align
        if interligne:
            p.line_spacing = interligne
        r = p.add_run()
        r.text = ligne
        r.font.size = Pt(taille)
        r.font.name = police
        r.font.bold = gras
        r.font.color.rgb = rgb(couleur)
    return tb


def boite(slide, x, y, w, h, fond=CARTE, bord=BORD, arrondi=True):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if arrondi else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fond)
    if bord:
        sh.line.color.rgb = rgb(bord)
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    if arrondi:
        sh.adjustments[0] = 0.06
    sh.shadow.inherit = False
    return sh


def entete(slide, kicker, titre, sombre=False):
    texte(slide, 0.5, 0.32, 9.0, 0.25, kicker, 10, TEAL if sombre else TEAL_FONCE, MONO)
    texte(slide, 0.5, 0.55, 9.0, 0.6, titre, 24, "FFFFFF" if sombre else ENCRE, SEMI)


def pied(slide, numero="", sombre=False):
    texte(slide, 0.5, 5.25, 4.0, 0.2, PIED, 8, GRIS_CLAIR, MONO)
    texte(slide, 9.1, 5.25, 0.4, 0.2, str(numero), 8, GRIS_CLAIR, MONO, align=PP_ALIGN.RIGHT)


def notes(slide, contenu):
    from pptx.oxml import parse_xml
    ns = slide.notes_slide
    tf = ns.notes_text_frame
    if tf is None:  # le masque de notes du PPT V1 n'a pas de zone de corps : on la déclare sur la page de notes
        sp = parse_xml(
            '<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/>'
            '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="fr-FR"/></a:p></p:txBody></p:sp>')
        ns.shapes._spTree.append(sp)
        tf = ns.notes_text_frame
    tf.text = contenu


def puces(slide, x, y, w, elements, taille=11, couleur=ENCRE, pas=0.42, sombre=False):
    for i, e in enumerate(elements):
        yy = y + i * pas
        pt = boite(slide, x, yy + 0.07, 0.09, 0.09, TEAL if sombre else TEAL_FONCE, None, arrondi=False)
        texte(slide, x + 0.22, yy, w - 0.22, pas, e, taille, couleur)


def grille(slide, x, y, largeurs, lignes, hauteur=0.4, taille=10, entete_fond=NUIT, premiere_col_gras=True):
    """Tableau fait de cases : la première ligne est l'en-tête."""
    cy = y
    for i, ligne in enumerate(lignes):
        cx = x
        h = hauteur if not isinstance(hauteur, list) else hauteur[i]
        for j, cellule in enumerate(ligne):
            w = largeurs[j]
            if i == 0:
                boite(slide, cx, cy, w, h, entete_fond, None, arrondi=False)
                texte(slide, cx + 0.1, cy, w - 0.2, h, cellule, taille, "FFFFFF", SEMI, ancre=MSO_ANCHOR.MIDDLE)
            else:
                boite(slide, cx, cy, w, h, "FFFFFF" if i % 2 else CARTE, BORD, arrondi=False)
                texte(slide, cx + 0.1, cy, w - 0.2, h, cellule, taille, ENCRE, SEMI if (j == 0 and premiere_col_gras) else SANS,
                      ancre=MSO_ANCHOR.MIDDLE)
            cx += w
        cy += h
    return cy


def image(slide, nom, x, y, w=None, h=None):
    chemin = IMG / nom
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(chemin), Inches(x), Inches(y), **kw)


def chiffre(slide, x, y, w, h, valeur, legende, fond=CARTE, couleur_valeur=TEAL_FONCE, sombre=False):
    boite(slide, x, y, w, h, CARTE_SOMBRE if sombre else fond, "1C2942" if sombre else BORD)
    texte(slide, x + 0.2, y + 0.18, w - 0.4, 0.6, valeur, 26, TEAL if sombre else couleur_valeur, SEMI)
    texte(slide, x + 0.2, y + 0.85, w - 0.4, h - 0.95, legende, 10.5, TEXTE_CLAIR if sombre else GRIS)


# --- retouches des slides V1 gardées ------------------------------------------------------------------------------------
def remplacer(slide, ancien, nouveau):
    n = 0
    for sh in slide.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if ancien in r.text:
                        r.text = r.text.replace(ancien, nouveau)
                        n += 1
    return n


def kicker_v1(slide):
    """« 04 · DÉMO SHOPIX · RÉSULTAT » devient « V1 · DÉMO SHOPIX · RÉSULTAT » : la frontière école / V2 se lit sur chaque slide."""
    for sh in slide.shapes:
        if sh.has_text_frame and abs(sh.top - Inches(0.32)) < Inches(0.03):
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.text = re.sub(r"^\d\d · ", "V1 · ", r.text)


# 1. couverture
s = ORIGINE[0]
for sh in s.shapes:
    if sh.has_text_frame:
        t = sh.text_frame.text
        if t.startswith("Un système multi-agents"):
            sh.text_frame.paragraphs[0].runs[0].text = ("La V1 rendue en cours, puis la V2 : lecture des documents, chaîne locale, preuves "
                                                         "vérifiées, validation et mise à jour. Le modèle propose, le code vérifie, "
                                                         "l'humain décide.")
            for r in sh.text_frame.paragraphs[0].runs[1:]:
                r.text = ""
        if t.startswith("Soutenance · M2"):
            sh.text_frame.paragraphs[0].runs[0].text = "Soutenance V2 · améliorations hors cours · Octobre 2026"
            for r in sh.text_frame.paragraphs[0].runs[1:]:
                r.text = ""
# mention de l'équipe de la V1 : la V2 est le travail personnel de Melvin, faite à partir du projet de groupe
for sh in s.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("Soutenance V2"):
        sh.top = Inches(4.98)
texte(s, 0.6, 4.64, 5.6, 0.3, "V1 réalisée en groupe avec Lucas HUARD, Jérémy LESSA et David AMARO MONTEIRO", 10, TEXTE_CLAIR)
notes(s, "Ouverture. La V1 est ce que nous avons rendu en cours (23-24 septembre). La V2 est ce que j'ai ajouté ensuite, seul, hors cours : "
         "elle répond point par point à la liste de ce que la V1 reconnaissait ne pas faire. Idée centrale : le modèle propose, le code "
         "vérifie, l'humain décide.")

# 2. plan : reconstruit
s = ORIGINE[1]
vider(s)
entete(s, "PLAN", "Déroulé de la soutenance (45 min)")
parties = [
    ("00", "Cadre", "École (V1) et hors cours (V2) : où passe la frontière", "0 → 2 min"),
    ("01", "Rappel de la V1", "Cas ShoPix, chaîne d'agents, ce qui manquait", "2 → 10 min"),
    ("02", "V2 : architecture et preuves", "Chaîne locale, dossier de connaissance, vérification par le code", "10 → 22 min"),
    ("03", "V2 : validation et mise à jour", "Page de validation, mise à jour incrémentale, essai réel, export", "22 → 32 min"),
    ("04", "Résultats, limites, sécurité", "Mesures, ce qui ne marche pas, risques du système lui-même", "32 → 40 min"),
    ("05", "Démonstration et conclusion", "Parcours en 8 minutes, feuille de route, questions", "40 → 45 min"),
]
for i, (num, titre_p, desc, temps) in enumerate(parties):
    y = 1.35 + i * 0.62
    boite(s, 0.5, y, 9.0, 0.52, CARTE)
    texte(s, 0.7, y + 0.13, 0.5, 0.3, num, 12, TEAL_FONCE, MONO)
    texte(s, 1.25, y + 0.07, 3.3, 0.4, titre_p, 13, ENCRE, SEMI, ancre=MSO_ANCHOR.MIDDLE)
    texte(s, 4.5, y + 0.07, 3.6, 0.4, desc, 10, GRIS, ancre=MSO_ANCHOR.MIDDLE)
    texte(s, 8.2, y + 0.07, 1.2, 0.4, temps, 10, TEAL_FONCE, MONO, align=PP_ALIGN.RIGHT, ancre=MSO_ANCHOR.MIDDLE)
pied(s, 2)
notes(s, "Le déroulé tient en 45 minutes. Le rappel de la V1 est volontairement court : le jury la connaît déjà, l'essentiel est la V2.")

# 20. injection : reconstruite (T-11 est exécuté depuis le 04/10)
s = ORIGINE[19]
vider(s)
entete(s, "V1 → V2 · TESTS · INJECTION DE PROMPT", "Injection de prompt : du test statique au test réel")
colonnes = [
    ("24/09 · T-07", "Régression statique", "La consigne cachée d'un document piégé est absente de toutes les sorties. Convention <<<DONNÉES>>>.", CARTE, GRIS),
    ("04/10 · T-11", "Exécution réelle archivée", "Vraie fixture de production : la ligne hostile est conservée mot pour mot comme donnée, détectée, journalisée, "
                                                    "absente de toute consigne. 11 contrôles : « PAS DE CONSIGNE EXÉCUTÉE ».", VERT_FOND, VERT),
    ("À montrer", "Limite assumée", "Cette exécution n'appelle pas le modèle en direct. La démonstration avec le modèle local sur le document "
                                    "piégé est à jouer en séance, puis à archiver.", AMBRE_FOND, AMBRE),
]
for i, (tag, ttl, corps, fond, coul) in enumerate(colonnes):
    x = 0.5 + i * 3.05
    boite(s, x, 1.4, 2.9, 2.75, fond)
    texte(s, x + 0.2, 1.58, 2.5, 0.25, tag, 10, coul, MONO, gras=True)
    texte(s, x + 0.2, 1.92, 2.5, 0.35, ttl, 14, ENCRE, SEMI)
    texte(s, x + 0.2, 2.35, 2.5, 1.7, corps, 10.5, ENCRE)
boite(s, 0.5, 4.3, 9.0, 0.6, NUIT)
texte(s, 0.75, 4.3, 8.5, 0.6, "Choix de conception : la ligne hostile n'est pas supprimée. Un garde-fou qui la retirerait donnerait une fausse impression "
                              "de sécurité ; elle est conservée comme donnée et signalée.", 10.5, "FFFFFF", ancre=MSO_ANCHOR.MIDDLE)
pied(s, 20)
notes(s, "T-07 est une régression statique du 24/09. T-11 a été exécuté le 04/10 sur une vraie fixture : onze contrôles, aucune consigne exécutée. "
         "Limite à dire : aucun appel du modèle en direct n'a été archivé. C'est la démonstration à faire en séance.")

# 23. limites V1 → V2 : reconstruite
s = ORIGINE[22]
vider(s)
entete(s, "V1 → V2 · LIMITES", "Ce que la V1 ne faisait pas, et ce que la V2 fait")
lignes = [
    ["La V1 annonçait…", "En V2", "Statut"],
    ["Pas de lecture automatique des documents", "Sept formats (PDF, OCR, Office, ZIP), tout intrant = donnée", "Fait"],
    ["Pas d'interface, éditeur opencode seul", "Site en quatre étapes, Studio, exports PDF / HTML / ZIP", "Fait"],
    ["Modèle cloud, local « en roadmap »", "Chaîne 100 % locale (Ollama), un modèle par rôle", "Fait"],
    ["Analyse manuelle de référence, test d'injection réel", "Réalisés le 04/10 (9 menaces sur 12 retrouvées ; T-11 archivé)", "Fait"],
    ["Pas de supervision continue", "Mise à jour incrémentale ; pas de supervision temps réel", "Partiel"],
    ["Pas de scan réseau actif, pas d'analyse de code", "Inchangé volontairement", "Non"],
    ["Aucune validation automatique", "Inchangé : `valide_par` humain, décisions conservées", "Renforcé"],
]
grille(s, 0.5, 1.35, [3.6, 4.3, 1.1], lignes, hauteur=0.46, taille=10)
pied(s, 23)
notes(s, "Chaque limite listée en V1 est reprise ici avec son statut. La V2 est la réponse à cette liste : lecture automatique, interface, "
         "chaîne locale, comparaison manuelle, test d'injection. Ce qui reste volontairement hors périmètre : le scan actif et l'analyse de code.")

# 27. feuille de route : reconstruite
s = ORIGINE[26]
vider(s)
entete(s, "V2 · PERSPECTIVES", "Feuille de route : ce qui est fait, ce qui reste")
boite(s, 0.5, 1.35, 4.35, 3.75, VERT_FOND)
texte(s, 0.75, 1.5, 3.5, 0.25, "RÉALISÉ DEPUIS LA SOUTENANCE", 10, VERT, MONO, gras=True)
puces(s, 0.75, 1.9, 3.95, ["Ingestion documentaire et site web", "Chaîne locale avec preuves vérifiées", "Validation humaine, décisions conservées",
                           "Mise à jour sans tout refaire", "Export du dossier complet avec liens"], 10.5, pas=0.62)
boite(s, 5.15, 1.35, 4.35, 3.75, CARTE)
texte(s, 5.4, 1.5, 3.5, 0.25, "À FAIRE", 10, ROUGE, MONO, gras=True)
puces(s, 5.4, 1.9, 3.95, ["Sécuriser le site (authentification, SSH, Ollama)","Fusionner les doublons d'actifs par le code",
                          "Retirer par le code les citations inexistantes", "Calibrer les niveaux (trop de « Critique »)",
                          "Test d'injection en direct avec le modèle local"], 10.5, pas=0.62)
pied(s, 28)
notes(s, "Ce qui a été réalisé répond à la feuille de route V1. Ce qui reste est surtout de la sécurité et de la qualité du jugement du modèle.")

# 28. conclusion : textes remplacés
s = ORIGINE[27]
remplacer(s, "L’IA propose, l’analyste décide", "Le modèle propose, le code vérifie, l’analyste décide")
for sh in s.shapes:
    if sh.has_text_frame:
        t = sh.text_frame.text.strip()
        cible = {
            "La méthode est dans les skills, pas dans la mémoire du LLM.": "Le code fait ce qui doit être exact : niveau, identifiants, sources.",
            "Chaque risque cite une source ISO 2022 vérifiée ; chaque étape est un commit.": "Chaque phrase renvoie à un extrait exact d'un document, vérifié.",
            "valide_par nominatif ; R-13 réexaminé, R-14 modifié.": "Ses décisions sont conservées quand un document s'ajoute.",
            "« Un audit a trouvé nos erreurs ; elles sont corrigées et verrouillées par des tests. »":
                "« L'essai réel a trouvé trois défauts que les tests ne voyaient pas : ils sont corrigés. Le reste est écrit. »",
            "Reproductible": "Fiable par construction",
            "Traçable": "Traçable à la phrase",
            "Humain décideur": "Humain décideur",
        }.get(t)
        if cible:
            runs = sh.text_frame.paragraphs[0].runs
            runs[0].text = cible
            for r in runs[1:]:
                r.text = ""
notes(s, "Trois messages : le code fait ce qui doit être exact ; chaque phrase renvoie à une preuve ; l'humain décide et ses décisions survivent. "
         "La phrase de fin est une posture : on a testé en vrai, on a trouvé des défauts, on les a corrigés, et on dit ce qui reste.")

# 29. merci
s = ORIGINE[28]
for sh in s.shapes:
    if sh.has_text_frame and sh.text_frame.text.strip().startswith("Analyse ShoPix"):
        runs = sh.text_frame.paragraphs[0].runs
        runs[0].text = "V1 : tag ecole-2026-09-24  ·  V2 : V2-ameliorations.md, DOSSIER-ECRIT-V2.md, EXPLICATIONS-DU-PROJET.md"
        for r in runs[1:]:
            r.text = ""

# --- nouvelles slides ------------------------------------------------------------------------------------------------------
NOUVELLES = {}


def S(nom, sombre=False):
    s = nouvelle_slide(sombre)
    NOUVELLES[nom] = s
    return s


# cadre
s = S("cadre")
entete(s, "00 · CADRE", "Deux productions, une frontière : le 24 septembre")
boite(s, 0.5, 1.35, 4.35, 3.0, CARTE)
texte(s, 0.75, 1.5, 3.8, 0.25, "V1 · ÉCOLE", 10, TEAL_FONCE, MONO, gras=True)
texte(s, 0.75, 1.8, 3.8, 0.3, "23 → 24 septembre · en groupe", 13, ENCRE, SEMI)
puces(s, 0.75, 2.3, 3.8, ["Agents opencode pilotés par consignes", "Cas ShoPix : 14 risques validés", "Dossier et soutenance déposés",
                          "640 lignes de Python (le script du PPT)"], 10.5, pas=0.45)
boite(s, 5.15, 1.35, 4.35, 3.0, NUIT, None)
texte(s, 5.4, 1.5, 3.8, 0.25, "V2 · HORS COURS", 10, TEAL, MONO, gras=True)
texte(s, 5.4, 1.8, 3.8, 0.3, "4 → 12 octobre · seul", 13, "FFFFFF", SEMI)
puces(s, 5.4, 2.3, 3.8, ["Ingestion, site web, pilote, connaissance", "Chaîne 100 % locale, preuves vérifiées", "Validation, exports, mise à jour",
                         "≈ 22 500 lignes de Python, 35 fichiers de tests"], 10.5, "FFFFFF", pas=0.45, sombre=True)
boite(s, 0.5, 4.5, 9.0, 0.55, "EAF1FB")
texte(s, 0.75, 4.5, 8.5, 0.55, "Référence immuable : tag Git ecole-2026-09-24 (commit b7f3155). 144 commits depuis, 184 fichiers, + 35 000 lignes.",
      10.5, ENCRE, ancre=MSO_ANCHOR.MIDDLE)
notes(s, "La frontière est une date et un commit : le 24 septembre à 13h34, juste après le dépôt de la soutenance. Tout ce qui suit est la V2, faite seul, hors cours.")

# déplacement
s = S("deplacement")
entete(s, "V2 · IDÉE CENTRALE", "Le déplacement : de la consigne au code")
lignes = [
    ["Question", "V1 : la consigne", "V2 : le code"],
    ["Qui calcule le niveau de risque ?", "Le modèle, puis un agent contrôle", "Le programme (matrice) ; le modèle ne donne que le jugement"],
    ["Qui pose les identifiants ?", "Le modèle", "Le programme (jamais réutilisés)"],
    ["D'où vient une affirmation ?", "Des référentiels cités", "De l'extrait exact d'un document `[E12]`, vérifié"],
    ["Une source inventée ?", "Un agent de contrôle la signale", "Le programme la retire avant la relecture"],
    ["Qui assemble le registre ?", "Un agent le relit à la main", "Le programme, ligne à ligne (2 min au lieu de 30)"],
]
grille(s, 0.5, 1.35, [2.9, 2.7, 3.4], lignes, hauteur=0.58, taille=10.5)
texte(s, 0.5, 4.95, 9.0, 0.3, "Le modèle garde ce qu'il fait bien : lire, extraire, rédiger, juger un point.", 11, GRIS)
pied(s, "")
notes(s, "C'est le changement de fond. En V1, la fiabilité reposait sur les consignes données aux agents. En V2, tout ce qui doit être exact est fait par le programme. Le modèle propose.")

# architecture
s = S("architecture")
entete(s, "V2 · ARCHITECTURE", "Quatre blocs, des modèles locaux")
image(s, "d1-architecture.png", 0.55, 1.3, h=3.85)
puces(s, 3.9, 1.45, 5.6, [
    "Site Streamlit : documents, lancer, résultats, validation",
    "Dossier de connaissance : faits à extrait exact, contradictions, couverture",
    "Pilote déterministe : ordre des étapes, reprises, contrôles",
    "Ollama sur un poste à carte de 12 Go : un modèle par rôle",
    "Registre, synthèse, mise à jour : établis par le code",
], 11, pas=0.62)
boite(s, 3.9, 4.65, 5.6, 0.5, NUIT, None)
texte(s, 4.1, 4.65, 5.3, 0.5, "Aucune donnée ne quitte le poste.", 11, TEAL, SEMI, ancre=MSO_ANCHOR.MIDDLE)
notes(s, "Quatre blocs. Le site guide l'analyste. Le dossier de connaissance est la seule source des agents. Le pilote déroule les étapes. Les modèles tournent en local.")

# chaîne
s = S("chaine")
entete(s, "V2 · LA CHAÎNE", "Sept étapes : ce que fait le modèle, ce que fait le code")
image(s, "d2-chaine.png", 0.9, 1.3, w=8.2)
pied(s, "")
notes(s, "Les étapes 1, 3, 4 et 5 sont produites par lots et assemblées par le code. Aux étapes 4 et 5 le modèle n'écrit que le jugement. "
         "Les étapes 6 et 7 n'ont plus d'agent : le registre et les chiffres sont établis par le code.")

# connaissance
s = S("connaissance")
entete(s, "V2 · DOSSIER DE CONNAISSANCE", "Lire les documents avant d'analyser")
vals = [("97 %", "des faits extraits sont des citations exactes (435 sur 447)"), ("86 %", "des relations vérifiées (372 sur 430)"),
        ("96 %", "des questions retrouvent le bon passage parmi les 8 premiers"), ("60–70 %", "de précision des contradictions : c'est bruyant")]
for i, (v, l) in enumerate(vals):
    chiffre(s, 0.5 + i * 2.28, 1.4, 2.1, 1.9, v, l, couleur_valeur=ROUGE if i == 3 else TEAL_FONCE)
boite(s, 0.5, 3.55, 9.0, 1.4, NUIT, None)
texte(s, 0.75, 3.7, 8.5, 0.25, "CE QUE CONTIENT LE DOSSIER", 10, TEAL, MONO, gras=True)
texte(s, 0.75, 4.0, 8.5, 0.9, "Faits à extrait exact · relations typées · contradictions croisées entre documents · couverture « connu / partiel / inconnu » · "
                              "carte d'identité de chaque document (type, fiabilité, date) · passages d'origine.", 11.5, "FFFFFF")
pied(s, "")
notes(s, "Mesures faites sur le corpus Nordval (22 documents). 97 % : le texte cité existe réellement dans le document. "
         "Les contradictions sont bruyantes : environ un signalement sur trois est un faux écart. C'est dit comme tel.")

# preuve
s = S("preuve")
entete(s, "V2 · LA PREUVE", "Une preuve pour chaque phrase")
image(s, "d3-tracabilite.png", 1.42, 1.3, h=3.0)
boite(s, 0.5, 4.45, 9.0, 0.65, CARTE)
texte(s, 0.75, 4.45, 8.5, 0.65, "[E12] renvoie à l'extrait exact. Le code vérifie qu'il existe dans le document. Une citation inexistante est signalée "
                                "(125 lignes sur SanteTech) : le système le dit, il ne le cache pas.", 10.5, ENCRE, ancre=MSO_ANCHOR.MIDDLE)
pied(s, "")
notes(s, "Chaque risque se remonte de la décision de l'analyste jusqu'à la phrase du document. Le contrôle déterministe détecte les citations qui n'existent pas.")

# modèles
s = S("modeles")
entete(s, "V2 · MODÈLES", "Chaîne locale : un modèle par rôle")
lignes = [
    ["Rôle", "Modèle", "Mesure"],
    ["Rédaction, extraction", "qwen3.5:9b", "Appels d'outils 6 sur 6, ≈ 93 jetons / s"],
    ["Secours", "qwen3:8b", "Même famille, plus petit"],
    ["Juge", "gemma4:12b", "Famille différente du rédacteur"],
    ["Vecteurs", "nomic-embed-text", "Recherche par mots et par sens"],
    ["Second avis", "bespoke-minicheck", "Vérification de faits"],
]
grille(s, 0.5, 1.35, [2.1, 1.9, 2.7], lignes, hauteur=0.5, taille=10.5)
boite(s, 7.4, 1.35, 2.1, 3.0, NUIT, None)
texte(s, 7.6, 1.55, 1.75, 2.7, "Une carte de 12 Go\nun modèle chargé à la fois\n\nAucune donnée ne sort du poste", 11, "FFFFFF")
boite(s, 0.5, 4.5, 9.0, 0.6, CARTE)
texte(s, 0.75, 4.5, 8.5, 0.6, "Écartés après mesure : qwen3:14b (déborde de la carte), granite4 (a décrit un seul document), llama3.1, mistral, qwen3-vl (4 appels d'outils sur 6).",
      10, GRIS, ancre=MSO_ANCHOR.MIDDLE)
pied(s, "")
notes(s, "Le choix est mesuré, pas supposé. Le juge est d'une autre famille que le rédacteur : un modèle tend à approuver ses propres erreurs.")

# contrôles par le code
s = S("controles")
entete(s, "V2 · CONTRÔLES PAR LE CODE", "Le code vérifie ce que le modèle propose")
vals = [("15 · 13 · 1", "références inventées retirées par le code aux étapes 3, 5 et 7"), ("0", "niveau de risque écrit par le modèle : il est calculé par la matrice"),
        ("151", "lignes du registre, établies par le code (un agent en avait écrit 9)"), ("2 min", "pour les étapes 6 et 7, au lieu de 30 par un agent")]
for i, (v, l) in enumerate(vals):
    chiffre(s, 0.5 + i * 2.28, 1.4, 2.1, 2.05, v, l)
boite(s, 0.5, 3.7, 9.0, 1.3, CARTE)
texte(s, 0.75, 3.82, 8.5, 0.25, "ORDRE DES CONTRÔLES", 10, TEAL_FONCE, MONO, gras=True)
texte(s, 0.75, 4.12, 8.5, 0.8, "1 · le code : identifiants, sources, nombres introuvables, doublons   →   2 · les citations : l'extrait existe-t-il ?   →   "
                               "3 · le juge d'une autre famille   →   une reprise au plus   →   sinon l'analyste, avec le point précis.", 11, ENCRE)
pied(s, "")
notes(s, "Les chiffres viennent du run complet du 11 octobre sur Nordval. Le registre n'avait que 9 lignes quand un agent le relisait à la main. Le code en produit 151 en deux minutes.")

# validation
s = S("validation")
entete(s, "V2 · VALIDATION HUMAINE", "Page 4 : décider avec le contexte")
puces(s, 0.5, 1.4, 5.2, ["Risques regroupés par niveau", "Contradictions entre documents et questions en premier : elles fixent les faits",
                         "Pour chaque point : la preuve, le document, la valeur proposée", "Accepter · modifier · rejeter · garder A ou B · répondre",
                         "Qui, quand, quoi, pourquoi : conservé", "Décisions conservées quand un document est ajouté"], 11, pas=0.58)
boite(s, 6.0, 1.4, 3.5, 3.4, NUIT, None)
texte(s, 6.25, 1.6, 3.0, 0.25, "VALIDÉE LE 12/10", 10, TEAL, MONO, gras=True)
texte(s, 6.25, 1.95, 3.0, 0.7, "« Elle permet de valider, rien à redire. »", 14, "FFFFFF", SEMI)
texte(s, 6.25, 3.0, 3.0, 1.6, "valide_par reste vide tant qu'un humain n'a pas décidé.\n\nUne ligne modifiée par une mise à jour revient « à confirmer » "
                              "avec l'ancienne décision visible.", 10.5, TEXTE_CLAIR)
pied(s, "")
notes(s, "La page de validation a été réorganisée plusieurs fois à partir de l'usage : cartes sous leur tableau, contradictions et questions en premier, enregistrement par bloc. Elle a été validée par l'analyste le 12 octobre.")

# mise à jour
s = S("miseajour")
entete(s, "V2 · MISE À JOUR", "Ajouter un document sans tout refaire")
image(s, "d4-mise-a-jour.png", 0.55, 1.3, h=3.85)
boite(s, 3.9, 1.4, 5.6, 1.6, NUIT, None)
texte(s, 4.1, 1.52, 5.2, 0.25, "ESSAI RÉEL · SANTETECH + 1 DOCUMENT", 10, TEAL, MONO, gras=True)
texte(s, 4.1, 1.85, 5.2, 0.6, "13 minutes", 28, "FFFFFF", SEMI)
texte(s, 4.1, 2.5, 5.2, 0.5, "3 actifs et 9 risques créés ; 39 actifs et 135 risques identiques à l'octet près.", 10.5, TEXTE_CLAIR)
puces(s, 3.9, 3.25, 5.6, ["Les numéros de preuve ne changent jamais", "Un retrait est seulement proposé, jamais automatique",
                          "Une décision sur une ligne modifiée revient « à confirmer »", "Coupure : reprise sans doublon"], 10.5, pas=0.4)
notes(s, "On compare l'état des documents à l'état déjà appliqué aux livrables, on montre un plan avec des cases, et on n'applique que cela. "
         "Sur SanteTech avec un document ajouté : 13 minutes, trois actifs créés, tout le reste identique.")

# essai réel
s = S("essai")
entete(s, "V2 · ESSAI RÉEL", "L'essai réel a trouvé ce que les tests n'avaient pas vu")
lignes = [
    ["Défaut constaté", "Cause", "Correction"],
    ["125 lignes proposées « à revoir »", "Elles citaient des preuves qui n'ont jamais existé", "Groupe à part, jamais coché d'office"],
    ["9 actifs créés dont du bruit", "« salle serveurs », « prestataire externe »…", "Termes génériques et noms déjà inventoriés écartés"],
    ["Description réécrite à 80 %", "Le nouveau document n'était pas repris", "Description conservée + section « Compléments » par le code"],
]
grille(s, 0.5, 1.35, [2.9, 3.1, 3.0], lignes, hauteur=0.72, taille=10.5)
boite(s, 0.5, 4.4, 4.35, 0.7, ROUGE_FOND)
texte(s, 0.7, 4.4, 4.0, 0.7, "Avant : 32 minutes, 134 éléments proposés", 12, ROUGE, SEMI, ancre=MSO_ANCHOR.MIDDLE)
boite(s, 5.15, 4.4, 4.35, 0.7, VERT_FOND)
texte(s, 5.35, 4.4, 4.0, 0.7, "Après : 13 minutes, 3 éléments retenus", 12, VERT, SEMI, ancre=MSO_ANCHOR.MIDDLE)
notes(s, "Les tests avec de faux modèles étaient verts. L'essai réel avec le vrai modèle a trouvé trois défauts. Ils sont corrigés et couverts par des tests. "
         "À dire clairement : les cas document modifié et document retiré ne sont testés qu'avec de faux modèles.")

# export
s = S("export")
entete(s, "V2 · TRAÇABILITÉ LIVRÉE", "Un dossier unique, avec tous les liens")
for i, (t, d) in enumerate([("HTML autonome", "Sommaire, livrables, une fiche par risque, annexe des preuves"),
                            ("PDF", "Le même dossier, mis en page"), ("ZIP", "HTML, PDF, livrables, tableur du registre, graphe de traçabilité")]):
    x = 0.5 + i * 3.05
    boite(s, x, 1.4, 2.9, 1.5, CARTE)
    texte(s, x + 0.2, 1.55, 2.5, 0.35, t, 14, ENCRE, SEMI)
    texte(s, x + 0.2, 2.0, 2.5, 0.9, d, 10.5, GRIS)
boite(s, 0.5, 3.2, 9.0, 1.0, NUIT, None)
texte(s, 0.75, 3.25, 8.5, 0.9, "document  →  preuve [E12]  →  actif  →  menace  →  évaluation  →  traitement  →  décision de l'analyste", 13, "FFFFFF", SEMI,
      ancre=MSO_ANCHOR.MIDDLE)
texte(s, 0.5, 4.45, 9.0, 0.6, "Chaque identifiant d'un tableau est un lien. Les documents d'origine ne sont jamais inclus : seuls les extraits cités le sont. "
                              "Le contenu est échappé (aucune balise exécutable).", 10.5, GRIS)
pied(s, "")
notes(s, "Le dossier complet est ce qu'on remet à une direction ou à un auditeur : on peut partir d'un risque et arriver à la phrase exacte du document.")

# résultats
s = S("resultats")
entete(s, "V2 · RÉSULTATS", "Résultats mesurés sur deux projets")
lignes = [
    ["Projet", "Documents", "Actifs", "Risques", "Critique", "Remarque"],
    ["ShoPix (V1)", "description écrite", "16", "14", "2", "Validés par un humain"],
    ["Nordval Logistique", "22 (≈ 39 Ko)", "38", "151", "48 %", "≈ 3 h de calcul local"],
    ["SanteTech", "3 (≈ 33 Ko)", "39", "135", "56 %", "Mise à jour : 13 min"],
]
grille(s, 0.5, 1.4, [2.2, 1.7, 0.9, 0.9, 1.0, 2.3], lignes, hauteur=0.62, taille=10.5)
texte(s, 0.5, 4.15, 9.0, 0.9, "Données fictives. Les niveaux sont à relire par l'analyste : la matrice est appliquée à des probabilités et des impacts que le "
                              "petit modèle juge souvent trop hauts. Sur SanteTech, aucun des 135 risques n'était décidé au moment de la production.", 10.5, GRIS)
pied(s, "")
notes(s, "Ces chiffres sont mesurés. Nordval : 22 documents, 38 actifs, 151 risques. SanteTech : 3 documents, 39 actifs, 135 risques. Dans les deux cas la part de risques critiques est trop élevée.")

# ce qui ne marche pas
s = S("limites")
entete(s, "V2 · LIMITES", "Ce qui ne marche pas encore")
items = [("Trop de « Critique »", "48 % (Nordval), 56 % (SanteTech)"), ("Doublons d'actifs", "Le même système en trois lignes ; des rôles pris pour des actifs"),
         ("Citations inexistantes", "Signalées par le contrôle, pas toutes corrigées"), ("Validation lourde", "411 points à valider sur Nordval ; juges stricts"),
         ("Contradictions bruyantes", "60 à 70 % de précision"), ("Lenteur", "≈ 3 h pour un gros cas ; un seul modèle chargé à la fois")]
for i, (t, d) in enumerate(items):
    x = 0.5 + (i % 3) * 3.05
    y = 1.4 + (i // 3) * 1.75
    boite(s, x, y, 2.9, 1.55, ROUGE_FOND if i < 3 else AMBRE_FOND)
    texte(s, x + 0.2, y + 0.18, 2.5, 0.35, t, 13, ENCRE, SEMI)
    texte(s, x + 0.2, y + 0.65, 2.5, 0.85, d, 10.5, GRIS)
pied(s, "")
notes(s, "On les dit avant qu'on nous les demande. Aucune de ces limites n'est cachée : chacune a un chiffre et elle est dans le dossier écrit.")

# sécurité
s = S("securite")
entete(s, "V2 · SÉCURITÉ DU SYSTÈME", "Les risques de notre propre système")
boite(s, 0.5, 1.35, 4.35, 3.15, VERT_FOND)
texte(s, 0.75, 1.5, 3.8, 0.25, "TRAITÉ", 10, VERT, MONO, gras=True)
puces(s, 0.75, 1.9, 3.95, ["Hallucination : preuve vérifiée, sources retirées", "Injection : tout intrant est une donnée", "Fuite : chaîne 100 % locale",
                           "Excès d'autonomie : le code seul écrit les livrables", "Dépendance : modèles remplaçables"], 10.5, pas=0.5)
boite(s, 5.15, 1.35, 4.35, 3.15, ROUGE_FOND)
texte(s, 5.4, 1.5, 3.8, 0.25, "NON CORRIGÉ · REPORTÉ", 10, ROUGE, MONO, gras=True)
puces(s, 5.4, 1.9, 3.95, ["Site sans authentification, port 8501 ouvert", "SSH root par mot de passe", "Ollama exposé sur le réseau local",
                          "Conteneur exécuté en root", "Shell de l'orchestrateur manuel ouvert"], 10.5, pas=0.5)
boite(s, 0.5, 4.65, 9.0, 0.5, NUIT, None)
texte(s, 0.75, 4.65, 8.5, 0.5, "Aucune donnée réelle n'est traitée : le système n'est pas présenté comme prêt pour un usage réel.", 11, TEAL, SEMI,
      ancre=MSO_ANCHOR.MIDDLE)
pied(s, "")
notes(s, "Le sujet demande les risques de notre propre système. Les risques propres à l'IA sont traités par des mesures concrètes. "
         "La sécurité de l'application elle-même n'est pas durcie : c'est dit, et c'est la première chose à faire avant tout usage réel.")

# démonstration
s = S("demo")
entete(s, "V2 · DÉMONSTRATION", "Huit minutes, rien de long en direct")
lignes = [
    ["Min", "Écran", "Message"],
    ["0 – 1", "Page 1 · Documents déjà déposés", "Tout format ; tout est une donnée"],
    ["1 – 3", "Connaissances : un fait, son extrait, une contradiction", "La preuve existe, le désaccord est visible"],
    ["3 – 5", "Page 3 · Registre, fiche d'un risque, clic sur une preuve", "document → preuve → risque"],
    ["5 – 7", "Page 4 · Décider un risque, une contradiction, une question", "L'humain décide, avec le contexte"],
    ["7 – 8", "Page 2 · Mise à jour proposée ; MISE-A-JOUR.md", "3 créations, le reste identique"],
]
grille(s, 0.5, 1.35, [1.0, 4.4, 3.6], lignes, hauteur=0.55, taille=10.5)
boite(s, 0.5, 4.8, 9.0, 0.38, AMBRE_FOND)
texte(s, 0.7, 4.8, 8.6, 0.38, "Plan B : le dossier complet exporté (HTML) s'ouvre sans serveur, avec tous les liens.", 10.5, AMBRE, SEMI, ancre=MSO_ANCHOR.MIDDLE)
pied(s, "")
notes(s, "Ne rien lancer d'long en direct : la carte graphique est lente et peut être occupée. Préparer un projet déjà analysé et un dossier déjà exporté.")

# --- ordre final et suppression des slides V1 abandonnées -------------------------------------------------------------------------------
ordre = [
    ORIGINE[0], ORIGINE[1], NOUVELLES["cadre"],
    ORIGINE[2], ORIGINE[3], ORIGINE[4], ORIGINE[5], ORIGINE[8], ORIGINE[12], ORIGINE[16], ORIGINE[22],
    NOUVELLES["deplacement"], NOUVELLES["architecture"], NOUVELLES["chaine"], NOUVELLES["connaissance"], NOUVELLES["preuve"],
    NOUVELLES["modeles"], ORIGINE[21], NOUVELLES["controles"], NOUVELLES["validation"], NOUVELLES["miseajour"], NOUVELLES["essai"],
    NOUVELLES["export"], NOUVELLES["resultats"], ORIGINE[19], NOUVELLES["limites"], NOUVELLES["securite"],
    ORIGINE[26], ORIGINE[27], NOUVELLES["demo"], ORIGINE[28],
]
for sl in ordre:
    if sl in ORIGINE and sl not in (ORIGINE[0], ORIGINE[1], ORIGINE[19], ORIGINE[22], ORIGINE[26], ORIGINE[27], ORIGINE[28]):
        kicker_v1(sl)
lst = prs.slides._sldIdLst
toutes = {s.slide_id: el for s, el in zip(list(prs.slides), list(lst))}
garder = [toutes[sl.slide_id] for sl in ordre]
for el in list(lst):
    lst.remove(el)
for el in garder:
    lst.append(el)
for sl_id, el in toutes.items():
    if el not in garder:
        prs.part.drop_rel(el.rId)

# numérotation : la forme « numéro » (9,10 po ; 5,25 po) de chaque slide ; sinon on la crée
for n, sl in enumerate(prs.slides, 1):
    if n == 1:
        continue
    trouve = False
    for sh in sl.shapes:
        if sh.has_text_frame and abs(sh.left - Inches(9.1)) < Inches(0.05) and abs(sh.top - Inches(5.25)) < Inches(0.05):
            r = sh.text_frame.paragraphs[0].runs
            if r:
                r[0].text = str(n)
                trouve = True
    if not trouve:
        texte(sl, 9.1, 5.25, 0.4, 0.2, str(n), 8, GRIS_CLAIR, MONO, align=PP_ALIGN.RIGHT)
        if not any(sh.has_text_frame and sh.text_frame.text.strip() == PIED for sh in sl.shapes):
            texte(sl, 0.5, 5.25, 4.0, 0.2, PIED, 8, GRIS_CLAIR, MONO)

prs.save(str(SORTIE))
print("slides :", len(prs.slides), "->", SORTIE)
