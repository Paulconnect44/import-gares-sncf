
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
├── data.csv               # Fichier CSV enrichi (codes UIC, noms, etc.)
├── overpass\_result\_modified.osm # Export enrichi pour OSM
├── requirements.txt         # Dépendances Python
└── README.md                # Présentation du projet

````


## Auteur

Paul — Étudiant en géomatique, stage chez SNCF Connect & tech 



