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
# outils (make, git, pip).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make git \
        tesseract-ocr tesseract-ocr-fra tesseract-ocr-osd \
        libpango-1.0-0 libpangocairo-1.0-0 fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Au démarrage : (re)créer la base Studio depuis .opencode/ si absente/ancienne,
# puis lancer l'interface (accessible depuis le réseau).
RUN printf '#!/bin/sh\nset -e\npython3 -m tools.studio.cli import >/dev/null 2>&1 || true\nexec streamlit run web/app.py --server.headless true --server.address 0.0.0.0 --server.port 8501\n' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

EXPOSE 8501
CMD ["/app/entrypoint.sh"]