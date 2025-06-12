---
output:
  pdf_document: default
  html_document: default
---
```markdown
# Importation enrichie des gares ferroviaires françaises (SNCF) dans OpenStreetMap

Ce dépôt contient un script Python permettant d’enrichir des données issues d’OpenStreetMap (OSM) avec des informations issues de bases internes SNCF, notamment les codes UIC et Réseau Ferré.

L’objectif est de produire un fichier `.osm` modifié, prêt à être validé dans JOSM puis soumis à OSM, dans le cadre d’un projet d’harmonisation des identifiants de gares françaises.

---

## Fonctionnalités

- Téléchargement des objets OSM ferroviaires (gares) via Overpass API.
- Nettoyage et filtrage des éléments non pertinents.
- Jointure avec une base enrichie (UIC, noms, codes internes).
- Ajout ou mise à jour de tags OSM standardisés :
  - `ref:FR:uic8`
  - `ref:FR:sncf:resarail`
  - `railway:ref`
- Export final au format `.osm` contenant uniquement les objets modifiés.
- Statistiques détaillées sur les enrichissements réalisés.

---

## Structure du dépôt

```

.
├── import\_gares.py          # Script principal
├── enriv3.csv               # Fichier CSV enrichi (codes UIC, noms, etc.)
├── overpass\_result.xml      # Cache Overpass brut
├── overpass\_result\_modified.osm # Export enrichi pour OSM
├── jointure\_osm\_enri.csv    # Fichier de jointure pour inspection
├── requirements.txt         # Dépendances Python
├── .gitignore               # Fichiers à exclure du dépôt
└── README.md                # Présentation du projet

````

---

## Installation

### Prérequis
- Python 3.9+
- Environnement virtuel recommandé

```bash
python -m venv venv
source venv/bin/activate  # ou .\venv\Scripts\activate sur Windows
pip install -r requirements.txt
````

---

## Utilisation

1. Placer le fichier `enriv3.csv` dans le répertoire racine.
2. Exécuter le script :

```bash
python import_gares.py
```

3. Ouvrir le fichier `overpass_result_modified.osm` dans [JOSM](https://josm.openstreetmap.de/) pour vérification, puis envoi si tout est conforme.



## Auteur

Paul — Étudiant en géomatique, stage chez SNCF Connect & tech 



