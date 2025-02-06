import json

# Load your data
with open('../../processed_data/cleaned_extracted_relationships.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Prepare nodes and edges
html_nodes = []
html_edges = []
node_ids = set()

# Extract data for nodes and edges
for record in data:
    entity1 = record.get("Entity 1")
    entity2 = record.get("Entity 2")
    relationship = record.get("Relationship Summary", "Unknown relationship")
    threat_level = record.get("Threat Assessment", {}).get("Threat Level", 1)
    threat_type = record.get("Threat Assessment", {}).get("Type", "Unknown Type")
    location1 = record.get("Origin Location 1", "Unknown Location")
    location2 = record.get("Origin Location 2", "Unknown Location")

    # Add Entity 1 node if not already added
    if entity1 not in node_ids:
        node_ids.add(entity1)
        html_nodes.append({
            "id": entity1,
            "label": entity1,
            "shape": "dot",
            "color": "#97c2fc",
            "title": f"{entity1}: Threat Level {threat_level}, Threat Type: {threat_type}, Origin: {location1}",
            "threat_level": threat_level,
            "location": location1,
            "threat_type": threat_type
        })

    # Add Entity 2 node if not already added
    if entity2 not in node_ids:
        node_ids.add(entity2)
        html_nodes.append({
            "id": entity2,
            "label": entity2,
            "shape": "dot",
            "color": "#97c2fc",
            "title": f"{entity2}: Threat Level {threat_level}, Threat Type: {threat_type}, Origin: {location2}",
            "threat_level": threat_level,
            "location": location2,
            "threat_type": threat_type
        })

    # Add edge with threat level information
    html_edges.append({
        "from": entity1,
        "to": entity2,
        "title": relationship,
        "threat_level": threat_level
    })

# Save nodes and edges as JavaScript
with open('graph_data2.js', 'w', encoding='utf-8') as js_file:
    js_file.write(f"const allNodes = {json.dumps(html_nodes, indent=2)};\n")
    js_file.write(f"const allEdges = {json.dumps(html_edges, indent=2)};\n")

print("Data extracted and saved to 'graph_data.js'.")
