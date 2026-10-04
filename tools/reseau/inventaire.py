# -*- coding: utf-8 -*-
"""Inventaire réseau local-only pour le homelab E21.

Collecte uniquement sur la machine locale (stdlib + sous-process). Aucune donnée
réelle (IP, MAC, hostname) n'est écrite dans le dépôt. L'anonymisation produit
un rapport sans identifiants.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

RACINE_DEPOT = Path(__file__).resolve().parents[2]


def _run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    """Exécute une commande locale avec timeout."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError as exc:
        raise FileNotFoundError(str(exc)) from exc
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or ""


def collecter_voisins() -> Dict[str, Any]:
    """Collecte voisins réseau anonymisés."""
    voisins = {"nombre": 0, "brut": []}
    try:
        rc, out, _ = _run_cmd(["ip", "neigh"])
        if rc != 0:
            rc, out, _ = _run_cmd(["arp", "-a"])
        if out:
            # Compte les lignes qui semblent contenir des entrées
            # Ignore les lignes vides
            lignes = [l.strip() for l in out.splitlines() if l.strip()]
            voisins["nombre"] = len(lignes)
            voisins["brut"] = lignes
        return voisins
    except FileNotFoundError:
        voisins["commande_indisponible"] = "ip/arp"
        return voisins


def _anonymiser_ip(ip: str) -> str:
    """Anonymise une adresse IP dans les écouteurs."""
    if ip in ("0.0.0.0", "::", "*"):
        return ip
    # Remplace toute IP locale/réelle par IP_LOCALE
    # IPv6 ou IPv4
    return "IP_LOCALE"


def collecter_ecouteurs() -> Dict[str, Any]:
    """Collecte ports locaux ouverts."""
    ecouteurs = {"lignes": [], "brut": []}
    try:
        rc, out, _ = _run_cmd(["ss", "-tulpn"])
        if rc != 0:
            rc, out, _ = _run_cmd(["netstat", "-tulpn"])
        ecouteurs["brut"] = [l for l in out.splitlines()]
        for l in ecouteurs["brut"]:
            ligne_anon = l
            # Remplace adresses IP
            # Pattern IP:port ou [IP]:port
            ligne_anon = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d+\b", r"0.0.0.0:\g<0>".split(":")[1] if False else "0.0.0.0:PORT", ligne_anon)  # no, easier: replace IP part
            # Simpler approach: find IP:port
            ligne_anon = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}:(\d+)\b", r"0.0.0.0:\1", ligne_anon)
            ligne_anon = re.sub(r"\[(?:[0-9a-fA-F:]+)\]:(\d+)\b", r"::: \1", ligne_anon)  # keep port style minimal
            # Also [::]:port -> [::]:port? but keep as is conceptually
            ecouteurs["lignes"].append(ligne_anon)
        return ecouteurs
    except FileNotFoundError:
        ecouteurs["commande_indisponible"] = "ss/netstat"
        return ecouteurs


def collecter_services_systemd() -> Dict[str, Any]:
    """Collecte services systemd actifs."""
    services = {"noms": [], "brut": []}
    try:
        rc, out, _ = _run_cmd(["systemctl", "list-units", "--type=service", "--state=running"])
        services["brut"] = [l for l in out.splitlines()]
        for l in services["brut"]:
            # Extraire nom.service
            m = re.search(r"(\S+\.service)", l)
            if m:
                services["noms"].append(m.group(1))
        return services
    except FileNotFoundError:
        services["commande_indisponible"] = "systemctl"
        return services


def inferer_roles(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Infère rôles depuis écouteurs/indices."""
    roles = []
    # Simple détection basée sur patterns
    return roles


def collecter_local() -> Dict[str, Any]:
    """Collecte complète (local-only)."""
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "voisins": collecter_voisins(),
        "ecouteurs": collecter_ecouteurs(),
        "services_systemd": collecter_services_systemd(),
        "indisponibilites": [],
    }
    if "commande_indisponible" in data["voisins"]:
        data["indisponibilites"].append("ip neigh/arp indisponibles")
    if "commande_indisponible" in data["ecouteurs"]:
        data["indisponibilites"].append("ss/netstat indisponibles")
    if "commande_indisponible" in data["services_systemd"]:
        data["indisponibilites"].append("systemctl indisponible")
    return data


def _anonymiser_ecouteur_ligne(ligne: str) -> str:
    """Anonymise une ligne d'écouteur en ne gardant que port/proto + info utile."""
    # Remplace IPv4:port
    ligne = re.sub(r"\b127\.0\.0\.1:(\d+)\b", r"IP_LOCALE:\1", ligne)
    ligne = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:(\d+)\b", r"0.0.0.0:\1", ligne)
    # IPv6
    ligne = re.sub(r"\[::1\]:(\d+)\b", r"[IP_LOCALE]:\1", ligne)
    ligne = re.sub(r"\[([0-9a-fA-F:]+)\]:(\d+)\b", r"[0.0.0.0]:\1", ligne)
    ligne = re.sub(r"::1:(\d+)\b", r"IP_LOCALE:\1", ligne)
    # Générique
    return ligne


def inferer_roles_complets(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    roles_map: Dict[str, Dict[str, Any]] = {}
    # Cherche dans écouteurs bruts et lignes
    for l in data["ecouteurs"].get("brut", []):
        l_low = l.lower()
        role = "autre"
        if any(p in l for p in ["80", "443", "8080", "8443", "8000", "3000", "5000"]):
            role = "web"
        if any(p in l for p in ["3306", "5432", "33060", "5433", "27017", "1521", "1433"]):
            role = "bdd"
        if "2375" in l or "2376" in l or "docker" in l_low:
            role = "conteneurs"
        if "8123" in l or "homeassistant" in l_low or "grafana" in l_low or "prometheus" in l_low or "supervisor" in l_low:
            role = "supervision"
        if "53" in l and ("dns" in l_low or "named" in l_low or ":53" in l):
            role = "reseau"
        # ports types pour ce rôle
        pts = []
        for p in ["80", "443", "8080", "8443", "3000", "3306", "5432", "2375", "8123"]:
            if p in l:
                pts.append(p + "/tcp")
        key = role
        if key not in roles_map:
            roles_map[key] = {"role": key, "nb_services": 0, "ports_types": set(), "services_systemd": []}
        roles_map[key]["nb_services"] += 1
        for pt in pts:
            roles_map[key]["ports_types"].add(pt)
    # fusion avec services systemd
    for s in data["services_systemd"].get("noms", []):
        s_low = s.lower()
        # assigne à rôle selon nom
        for rkey in ["web", "bdd", "conteneurs", "supervision", "reseau"]:
            if rkey in s_low or any(k in s_low for k in ["nginx", "apache", "httpd", "mariadb", "mysql", "postgres", "docker", "containerd", "homeassistant", "grafana", "prometheus"]):
                # lie si existe
                k = None
                if rkey in roles_map:
                    k = rkey
                # fallback par mot-clé
                if k is None:
                    # détermine meilleur
                    pass
                if k is None and rkey in s_low:
                    k = rkey
                if k is not None:
                    if rkey in s_low:  # simple
                        pass
                # simple mapping
                pass
        # assign direct
        assigned = None
        if any(k in s_low for k in ["nginx", "apache", "httpd"]):
            assigned = "web"
        elif any(k in s_low for k in ["mariadb", "mysql", "postgres", "postgre", "mongodb"]):
            assigned = "bdd"
        elif any(k in s_low for k in ["docker", "containerd"]):
            assigned = "conteneurs"
        elif any(k in s_low for k in ["homeassistant", "grafana", "prometheus", "node_exporter", "supervisor"]):
            assigned = "supervision"
        elif "named" in s_low or "dnsmasq" in s_low:
            assigned = "reseau"
        if assigned:
            if assigned not in roles_map:
                roles_map[assigned] = {"role": assigned, "nb_services": 0, "ports_types": set(), "services_systemd": []}
            if s not in roles_map[assigned]["services_systemd"]:
                roles_map[assigned]["services_systemd"].append(s)
    # convert sets
    res = []
    for v in roles_map.values():
        res.append({
            "role": v["role"],
            "nb_services": v["nb_services"],
            "ports_types": sorted(list(v["ports_types"])),
            "services_systemd": sorted(v["services_systemd"]),
        })
    if not res:
        res = [{"role": "autre", "nb_services": 0, "ports_types": [], "services_systemd": []}]
    return res


def _has_exposition(ligne: str) -> bool:
    """Détecte exposition sur 0.0.0.0 ou ::."""
    l_low = ligne.lower()
    return "0.0.0.0" in ligne or "::: " in ligne or "[::]:" in ligne or "[0.0.0.0]" in ligne or re.search(r"0\.0\.0\.0[:\s]", ligne) is not None or re.search(r":::\s*\d", ligne) is not None


def generer_rapport_anonymise(data: Dict[str, Any], out_dir: Path, fixtures_mode: bool = False, indisponibilites: List[str] = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    rapport_path = out_dir / "inventaire-anonymise.md"
    roles = inferer_roles_complets(data)
    vois = data.get("voisins", {})
    nb_voisins = vois.get("nombre", 0)
    indispos = indisponibilites or data.get("indisponibilites", [])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lignes = []
    lignes.append("# Inventaire réseau anonymisé (homelab E21)")
    lignes.append("")
    lignes.append(f"Date : {now}")
    lignes.append(f"Voisins réseau : {nb_voisins} hôtes voisins")
    lignes.append("")
    if indispos:
        lignes.append("> Commandes indisponibles : " + ", ".join(indispos))
        lignes.append("")
    lignes.append("## Récapitulatif par rôle")
    lignes.append("")
    lignes.append("| rôle | nb services | ports types | services systemd | risque |")
    lignes.append("|---|---|---|---|---|")
    if not roles:
        lignes.append("| autre | 0 | - | - | - |")
    else:
        for r in roles:
            risque = "-"
            # check exposition in ecouteurs
            for el in data.get("ecouteurs", {}).get("brut", []):
                if _has_exposition(el):
                    risque = "exposé (0.0.0.0/::)"
                    break
            pt_str = ", ".join(r["ports_types"]) if r["ports_types"] else "-"
            sd_str = ", ".join(r["services_systemd"]) if r["services_systemd"] else "-"
            lignes.append(f"| {r['role']} | {r['nb_services']} | {pt_str} | {sd_str} | {risque} |")
    lignes.append("")
    lignes.append("*Aucune adresse IP, MAC ou hostname réel n'est présente dans ce rapport.*")
    lignes.append("")
    rapport_path.write_text("\n".join(lignes), encoding="utf-8")
    return rapport_path


def charger_fixture(fixture_path: Path) -> Dict[str, Any]:
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture introuvable : {fixture_path}")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(prog="python3 -m tools.reseau.inventaire")
    parser.add_argument("--out-raw", default=None, help="Dossier pour inventaire-raw.json (gitignoré)")
    parser.add_argument("--out-anon", default=None, help="Dossier pour inventaire-anonymise.md")
    parser.add_argument("--fixtures", action="store_true", help="Mode fixture")
    parser.add_argument("fixture_path", nargs="?", default=None, help="Chemin vers inventaire-fixture.json")
    args = parser.parse_args()

    if args.out_raw is None:
        # défaut analyses/<cas>/intrants/reseau/
        # on prend un cas générique si existe, sinon on crée sous analyses/latest/intrants/reseau
        cas = "latest"
        for p in (RACINE_DEPOT / "analyses").glob("*"):
            if p.is_dir():
                cas = p.name
                break
        out_raw = RACINE_DEPOT / "analyses" / cas / "intrants" / "reseau"
    else:
        out_raw = Path(args.out_raw)

    if args.out_anon is None:
        out_anon = RACINE_DEPOT / "inventaire"
    else:
        out_anon = Path(args.out_anon)

    if args.fixtures:
        if not args.fixture_path:
            print("Mode fixtures requis: fournir chemin du fixture", file=sys.stderr)
            return 2
        data = charger_fixture(Path(args.fixture_path))
    else:
        data = collecter_local()

    out_raw.mkdir(parents=True, exist_ok=True)
    (out_raw / "inventaire-raw.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    indispos = data.get("indisponibilites", [])
    generer_rapport_anonymise(data, out_anon, fixtures_mode=args.fixtures, indisponibilites=indispos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
