# IfcOpenShell Starter Project

A Python project demonstrating IFC model creation, traversal, and manipulation
using the IfcOpenShell API.

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows Git Bash)
source venv/Scripts/activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
ifcopenshell-starter/
├── src/
│   ├── 01_hello_wall.py          # Create a minimal IFC with one wall
│   ├── 02_spatial_hierarchy.py   # Full Project→Site→Building→Storey→Elements
│   ├── 03_properties.py          # Adding property sets to elements
│   ├── 04_relationships.py       # Traversing relationships (forward + inverse)
│   ├── 05_query_model.py         # Loading and querying an existing IFC file
│   └── utils.py                  # Shared helper functions
├── output/                       # Generated .ifc files go here
├── requirements.txt
└── README.md
```

## Running

```bash
# Run scripts in order — each builds on concepts from the previous
python src/01_hello_wall.py
python src/02_spatial_hierarchy.py
python src/03_properties.py
python src/04_relationships.py
python src/05_query_model.py
```

Each script writes an `.ifc` file to `output/` that you can open in:
- BlenderBIM / Bonsai
- IFC Open Viewer (browser extension)
- Any IFC-compatible viewer

## Key Concepts

- **Entities**: IFC objects like IfcWall, IfcBuilding, IfcSlab
- **Relationships**: Separate objects that link entities (IfcRelAggregates, etc.)
- **Property Sets**: Key-value metadata attached via IfcRelDefinesByProperties
- **Spatial Hierarchy**: Project → Site → Building → Storey → Elements
- **Inverse Attributes**: API-level reverse lookups (e.g., wall.ContainedInStructure)
