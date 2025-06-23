import requests
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import pandas as pd
from xml.etree.ElementTree import Element, ElementTree

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_XML_CACHE = "overpass_result.xml"

#ici on exclut les ids des éléments que l'on ne veut pas traiter(gare parisienne avec 2 uic)
EXCLUDED_IDS = {
}

query = """
[out:xml][timeout:1800];
area["ISO3166-1"="FR"][admin_level=2]->.fr;
(
  node["railway"](area.fr);
  way["railway"](area.fr);
);
out meta center;
>;
out meta qt;
"""

# On télécharge le fichier XML depuis Overpass API
response = requests.post(OVERPASS_URL, data={'data': query})
response.raise_for_status()
xml_data = response.content
with open(OVERPASS_XML_CACHE, "wb") as f:
    f.write(xml_data)

# --- PARSING XML ---
# On parse le fichier XML pour extraire les nœuds et les éléments de type "way"
root = ET.fromstring(xml_data)
nodes_dict = {}
features = []

for node in root.findall("node"):
    nid = int(node.attrib["id"])
    lon = float(node.attrib["lon"])
    lat = float(node.attrib["lat"])
    nodes_dict[nid] = (lon, lat)

for elem in root:
    if elem.tag not in ["node", "way"]:
        continue

    eid = int(elem.attrib["id"])
    if eid in EXCLUDED_IDS:
        continue

    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in elem.findall("tag")}

    railway = tags.get("railway")
    operator = tags.get("operator", "")

    if railway not in {"station", "halt"}:
        continue
    if operator and "sncf" not in operator.lower():
        continue

    obj = dict(tags)
    obj.update({
        "osm_id": eid,
        "osm_type": elem.tag,
        "version": int(elem.attrib.get("version", 1)),
        "timestamp": elem.attrib.get("timestamp"),
        "changeset": elem.attrib.get("changeset"),
        "uid": elem.attrib.get("uid"),
        "user": elem.attrib.get("user")
    })

    if elem.tag == "node":
        obj["geometry"] = Point(float(elem.attrib["lon"]), float(elem.attrib["lat"]))
        features.append(obj)

    elif elem.tag == "way":
        nd_refs = [int(nd.attrib["ref"]) for nd in elem.findall("nd")]
        coords = [nodes_dict[n] for n in nd_refs if n in nodes_dict]

        geometry = None
        if len(coords) >= 3 and coords[0] == coords[-1]:
            try:
                polygon = Polygon(coords)
                geometry = polygon.centroid
            except:
                pass
        elif coords:
            try:
                linestring = LineString(coords)
                geometry = linestring.centroid
            except:
                pass

        if geometry:
            obj["geometry"] = geometry
            features.append(obj)


# --- JOINTURE AVEC data.geojson ---
#on réalise la jointure avec le fichier CSV enrichi

gdf_osm = gpd.GeoDataFrame(features, crs="EPSG:4326")
gdf_base = gpd.read_file("data/data.csv") 


gdf_base["UIC"] = gdf_base["UIC"].astype(str)
gdf_osm["uic_ref"] = gdf_osm["uic_ref"].astype(str)

# Jointure sur UIC (enri) et uic_ref (osm)
gdf_merged = gdf_base.merge(
    gdf_osm,
    left_on="UIC",
    right_on="uic_ref",
    how="left",
    suffixes=('', '_osm')
)

# --- MODIFICATION DIRECTE DU FICHIER XML ---
tree = ET.parse(OVERPASS_XML_CACHE)
root = tree.getroot()

# Indexer les données enrichies par osm_id
enriched_data = {
    int(row["osm_id"]): row
    for _, row in gdf_merged.iterrows()
    if pd.notna(row.get("osm_id"))
}

# Tags à ajouter depuis la base enrichie
wanted_tags = {
    "name",
    "railway:ref",
    
    "ref:FR:sncf:resarail"
}

excluded_tags = {"geometry", "osm_id", "osm_type", "version", "timestamp", "changeset", "user", "uid"}

mod_count = 0

for element in root.findall(".//node") + root.findall(".//way"):
    eid = int(element.attrib["id"])
    if eid not in enriched_data:
        continue

    row = enriched_data[eid]
    modified = False

    # On conserve les tags OSM existants
    existing_tags = {tag.attrib["k"]: tag for tag in element.findall("tag")}

    # Ajout ou mise à jour des tags demandés
    for col in wanted_tags:
        if col in excluded_tags or pd.isna(row.get(col)) or row.get(col) == "":
            continue

        # Supprimer le tag existant si présent
        if col in existing_tags:
            element.remove(existing_tags[col])

        # Ajouter le tag enrichi
        ET.SubElement(element, "tag", {"k": col, "v": str(row[col])})
        modified = True

    if modified:
        element.set("action", "modify")
        mod_count += 1


# --- STATISTIQUES FIABLES SUR LES MODIFICATIONS ---

# 1. Nombre exact d’éléments OSM modifiés (action="modify")
modified_elements = [el for el in root.findall(".//node") + root.findall(".//way") if el.get("action") == "modify"]
total_modified_elements = len(modified_elements)
print(f"{total_modified_elements} éléments OSM modifiés au total.")

# 2. Statistiques par tag enrichi (ajout vs modification)
tag_stats = {col: {"added": 0, "modified": 0} for col in wanted_tags}

for el in modified_elements:
    eid = int(el.attrib["id"])
    enriched_row = enriched_data.get(eid, {})
    # Récupérer la ligne OSM d'origine (avant enrichissement)
    original_row = gdf_osm[gdf_osm["osm_id"] == eid]
    for col in wanted_tags:
        if col in excluded_tags or pd.isna(enriched_row.get(col)) or enriched_row.get(col) == "":
            continue
        enriched_val = str(enriched_row.get(col))
        # Chercher la valeur d'origine
        if not original_row.empty:
            original_val = original_row.iloc[0].get(col)
            if pd.isna(original_val) or original_val == "":
                tag_stats[col]["added"] += 1
            elif str(original_val) != enriched_val:
                tag_stats[col]["modified"] += 1
        else:
            tag_stats[col]["added"] += 1

for tag, stat in tag_stats.items():
    print(f"Tag '{tag}': {stat['added']} ajout(s), {stat['modified']} modification(s).")


# --- FILTRAGE DES ÉLÉMENTS MODIFIÉS ---
modified_elements = [el for el in root.findall(".//node") + root.findall(".//way") if el.get("action") == "modify"]

# Pour sauvegarder uniquement les éléments modifiés dans un nouveau fichier .osm :

new_root = Element("osm", root.attrib)
for el in modified_elements:
    new_root.append(el)

# --- AJOUT DES NŒUDS ASSOCIÉS AUX WAYS MODIFIÉS ---
needed_node_ids = set()
for el in modified_elements:
    if el.tag == "way":
        for nd in el.findall("nd"):
            needed_node_ids.add(nd.attrib["ref"])

# Ajouter les nœuds nécessaires au fichier final
for node in root.findall(".//node"):
    if node.attrib["id"] in needed_node_ids:
        new_root.append(node)

# Ajout d'un tag old_name si le tag name a été modifié
for el in new_root.findall(".//node") + new_root.findall(".//way"):
    if el.get("action") != "modify":
        continue
    eid = int(el.attrib["id"])
    enriched_row = enriched_data.get(eid, {})
    original_row = gdf_osm[gdf_osm["osm_id"] == eid]
    if "name" in wanted_tags and not original_row.empty:
        original_name = original_row.iloc[0].get("name")
        new_name = enriched_row.get("name")
        if pd.notna(original_name) and pd.notna(new_name) and str(original_name) != str(new_name):
            # Supprimer old_name existant s'il y en a un
            for tag in el.findall("tag"):
                if tag.attrib.get("k") == "old_name":
                    el.remove(tag)
            # Ajouter le tag old_name avec l'ancien nom
            ET.SubElement(el, "tag", {"k": "old_name", "v": str(original_name)})

ElementTree(new_root).write("output/overpass_result_modified.osm", encoding="utf-8", xml_declaration=True)
