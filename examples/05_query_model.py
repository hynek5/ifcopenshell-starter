"""
05 - Query Model
================
Load an existing IFC file and run various queries on it.

Demonstrates:
  - Opening an IFC file
  - Querying by type (model.by_type)
  - Querying by GlobalId (model.by_guid)
  - Filtering elements by properties
  - Counting elements by class
  - Extracting data into a summary report
  - ifcopenshell.util.element utilities

Run this AFTER 04_relationships.py (it loads that output file).
"""
import os
from collections import Counter

import ifcopenshell
import ifcopenshell.util.element

from utils import OUTPUT_DIR, print_spatial_tree, print_element_properties

print("\n=== 05: Query Model ===\n")

# --- Load the model from script 04 ---
ifc_path = os.path.join(OUTPUT_DIR, "04_relationships.ifc")
if not os.path.exists(ifc_path):
    print(f"  ERROR: File not found: {ifc_path}")
    print("  Please run 04_relationships.py first.")
    exit(1)

model = ifcopenshell.open(ifc_path)
print(f"  Loaded: {ifc_path}")
print(f"  Schema: {model.schema}")
print(f"  Total entities: {len(list(model))}")

# =========================================================================
# Query 1: List all entity types and their counts
# =========================================================================
print("\n  --- Entity type summary ---\n")

type_counts = Counter(entity.is_a() for entity in model)
for cls, count in sorted(type_counts.items()):
    print(f"  {cls}: {count}")

# =========================================================================
# Query 2: Find all elements by type
# =========================================================================
print("\n  --- All walls ---\n")

walls = model.by_type("IfcWall")
print(f"  Found {len(walls)} walls:")
for wall in walls:
    print(f"    {wall.Name} (GlobalId: {wall.GlobalId})")

print("\n  --- All slabs ---\n")

slabs = model.by_type("IfcSlab")
print(f"  Found {len(slabs)} slabs:")
for slab in slabs:
    print(f"    {slab.Name} (GlobalId: {slab.GlobalId})")

# =========================================================================
# Query 3: Find element by GlobalId
# =========================================================================
print("\n  --- Lookup by GlobalId ---\n")

# Grab a GlobalId from the first wall and look it up
if walls:
    target_guid = walls[0].GlobalId
    found = model.by_guid(target_guid)
    print(f"  Searched for: {target_guid}")
    print(f"  Found: {found.is_a()} '{found.Name}'")

# =========================================================================
# Query 4: Find elements by property value
# =========================================================================
print("\n  --- Find all external walls (IsExternal=True) ---\n")

external_walls = []
for wall in model.by_type("IfcWall"):
    psets = ifcopenshell.util.element.get_psets(wall)
    # Check across all property sets for the IsExternal property
    for pset_name, props in psets.items():
        if props.get("IsExternal") is True:
            external_walls.append(wall)
            break

print(f"  Found {len(external_walls)} external walls:")
for wall in external_walls:
    print(f"    {wall.Name}")

# =========================================================================
# Query 5: Find all load-bearing elements
# =========================================================================
print("\n  --- Find all load-bearing elements ---\n")

load_bearing = []
# Search across ALL product types
for element in model.by_type("IfcProduct"):
    psets = ifcopenshell.util.element.get_psets(element)
    for pset_name, props in psets.items():
        if props.get("LoadBearing") is True:
            load_bearing.append(element)
            break

print(f"  Found {len(load_bearing)} load-bearing elements:")
for elem in load_bearing:
    print(f"    {elem.is_a()} '{elem.Name}'")

# =========================================================================
# Query 6: Get type information
# =========================================================================
print("\n  --- Type information ---\n")

for wall in model.by_type("IfcWall"):
    wall_type = ifcopenshell.util.element.get_type(wall)
    type_name = wall_type.Name if wall_type else "(no type)"
    print(f"  {wall.Name} → type: {type_name}")

# =========================================================================
# Query 7: Get material information
# =========================================================================
print("\n  --- Material assignments ---\n")

for wall in model.by_type("IfcWall"):
    material = ifcopenshell.util.element.get_material(wall)
    mat_name = material.Name if material else "(no material)"
    print(f"  {wall.Name} → material: {mat_name}")

# =========================================================================
# Query 8: Print the spatial tree
# =========================================================================
print("\n  --- Spatial tree ---\n")
print_spatial_tree(model, indent=1)

# =========================================================================
# Query 9: Generate a summary report
# =========================================================================
print("\n  --- Summary Report ---\n")

project = model.by_type("IfcProject")[0]
print(f"  Project: {project.Name}")

for site in model.by_type("IfcSite"):
    print(f"  Site: {site.Name}")

for building in model.by_type("IfcBuilding"):
    print(f"  Building: {building.Name}")

for storey in model.by_type("IfcBuildingStorey"):
    # Count elements in this storey
    element_count = 0
    for rel in storey.ContainsElements:
        element_count += len(rel.RelatedElements)
    print(f"  Storey: {storey.Name} (elev={storey.Elevation}) → {element_count} elements")

print(f"\n  Total walls:   {len(model.by_type('IfcWall'))}")
print(f"  Total slabs:   {len(model.by_type('IfcSlab'))}")
print(f"  Total columns: {len(model.by_type('IfcColumn'))}")

# Count relationships
rels = model.by_type("IfcRelationship")
print(f"  Total relationships: {len(rels)}")

# Groups
for group_rel in model.by_type("IfcRelAssignsToGroup"):
    group = group_rel.RelatingGroup
    members = [e.Name for e in group_rel.RelatedObjects]
    print(f"  Group '{group.Name}': {members}")

print()
