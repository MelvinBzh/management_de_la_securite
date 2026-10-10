# Image de l'application E21 « Des agents IA pour analyser les risques ».
#
# Construction : docker build -t e21 .
# Lancement     : docker run --rm -p 8501:8501 \
#                   -v "$PWD/stockage_local:/app/stockage_local" \
#                   -v "$PWD/analyses:/app/analyses" \
#                   e21
# Accès        : http://<ip-du-serveur>:8501
#
# Nom des volumes : analyses/ (+ intrants gitignorés) et stockage_local/
# (base source de vérité) restent sur l'hôte ; .opencode/ est embarqué dans
# l'image (les agents/skills déployés par le Studio sont donc perdus à la
# reconstruction — monter aussi un volume .opencode si besoin, l'image fait
# alors l'import initial depuis les fichiers du dépôt au démarrage).

FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Dépendances système : OCR (tesseract FR/EN/OSD), Polices, Pango (PDF WeasyPrint),
# outils (make, git, pip), runtime du binaire opencode (libstdc++, certificats).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make git curl ca-certificates libstdc++6 \
        tesseract-ocr tesseract-ocr-fra tesseract-ocr-osd \
        libpango-1.0-0 libpangocairo-1.0-0 fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# opencode CLI (binaire autonome : Node n'est pas requis) — c'est lui qui exécute
# la chaîne d'agents depuis le bouton « Lancer la chaîne » de l'interface.
# Version FIGÉE (`OPENCODE_VERSION`) : une mise à jour silencieuse a déjà changé le comportement
# des permissions d'écriture (1.18.34 → 1.18.35). Pour monter de version : la changer ici, relancer
# `make test-web` et la chaîne sur un petit cas, puis committer.
# Si le réseau du serveur bloque le téléchargement, construire avec
# `--build-arg INSTALL_OPENCODE=0` : l'application fonctionne, seul le lancement
# de la chaîne depuis l'interface est indisponible.
ARG INSTALL_OPENCODE=1
ARG OPENCODE_VERSION=1.18.35
RUN if [ "$INSTALL_OPENCODE" = "1" ]; then \
        set -eux; \
        curl -fsSL https://opencode.ai/install | bash -s -- --version "$OPENCODE_VERSION"; \
        ln -sf /root/.opencode/bin/opencode /usr/local/bin/opencode; \
        opencode --version; \
    else \
        echo "opencode non installé (INSTALL_OPENCODE=0) — la chaîne ne sera pas lançable."; \
    fi

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Au démarrage : (re)créer la base Studio depuis .opencode/ si absente/ancienne,
# puis lancer l'interface (accessible depuis le réseau).
RUN printf '#!/bin/sh\nset -e\npython3 -m tools.studio.cli import >/dev/null 2>&1 || true\nexec streamlit run web/app.py --server.headless true --server.address 0.0.0.0 --server.port 8501\n' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

EXPOSE 8501
CMD ["/app/entrypoint.sh"]