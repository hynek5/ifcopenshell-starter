"""
02 - Spatial Hierarchy
======================
Build the full IFC spatial tree and assign elements to storeys.

Demonstrates:
  - IfcRelAggregates  (Project→Site→Building→Storey)
  - IfcRelContainedInSpatialStructure  (Storey→Elements)
  - Inverse attribute traversal (going "up" the tree)

The hierarchy:
  IfcProject
    └── IfcSite
          └── IfcBuilding
                ├── IfcBuildingStorey (Ground Floor, elev=0.0)
                │     ├── IfcWall  "Exterior Wall 01"
                │     ├── IfcWall  "Interior Wall 01"
                │     └── IfcSlab  "Ground Slab"
                └── IfcBuildingStorey (First Floor, elev=3.2)
                      ├── IfcWall  "Exterior Wall 02"
                      └── IfcSlab  "First Floor Slab"
"""
import ifcopenshell
import ifcopenshell.api

from utils import create_empty_project, build_spatial_hierarchy, save_model, print_spatial_tree

print("\n=== 02: Spatial Hierarchy ===\n")

# --- Step 1: Create model with project + units + context ---
model = create_empty_project("Spatial Demo Project")
print("  Created project with units and context")

# --- Step 2: Build the spatial tree ---
hierarchy = build_spatial_hierarchy(
    model,
    site_name="Prague Site",
    building_name="Building A",
    storeys=[
        {"name": "Ground Floor", "elevation": 0.0},
        {"name": "First Floor", "elevation": 3.2},
    ],
)
ground_floor = hierarchy["storeys"][0]
first_floor = hierarchy["storeys"][1]
print("  Built spatial tree: Site → Building → 2 Storeys")

# --- Step 3: Create elements ---
# Ground floor elements
wall_ext_01 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Exterior Wall 01")
wall_int_01 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Interior Wall 01")
slab_ground = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="Ground Slab")

# First floor elements
wall_ext_02 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Exterior Wall 02")
slab_first = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="First Floor Slab")

print("  Created 5 elements (3 walls, 2 slabs)")

# --- Step 4: Assign elements to storeys ---
# This creates IfcRelContainedInSpatialStructure relationships
ifcopenshell.api.run(
    "spatial.assign_container", model,
    relating_structure=ground_floor,
    products=[wall_ext_01, wall_int_01, slab_ground],
)
ifcopenshell.api.run(
    "spatial.assign_container", model,
    relating_structure=first_floor,
    products=[wall_ext_02, slab_first],
)
print("  Assigned elements to storeys via IfcRelContainedInSpatialStructure")

# --- Step 5: Save ---
save_model(model, "02_spatial_hierarchy.ifc")

# --- Step 6: Verify by printing the tree ---
print("\n  Spatial tree:")
print_spatial_tree(model, indent=1)

# --- Step 7: Demonstrate inverse attribute traversal ---
print("\n  --- Inverse attribute demo ---")
print(f"  Starting at: {wall_ext_01.Name} ({wall_ext_01.GlobalId})")

# Go UP: wall → storey (via inverse attribute ContainedInStructure)
for rel in wall_ext_01.ContainedInStructure:
    storey = rel.RelatingStructure
    print(f"  → Contained in: {storey.is_a()} '{storey.Name}' (elev={storey.Elevation})")

    # Go UP: storey → building (via inverse attribute Decomposes)
    for rel2 in storey.Decomposes:
        building = rel2.RelatingObject
        print(f"    → Part of: {building.is_a()} '{building.Name}'")

        # Go UP: building → site
        for rel3 in building.Decomposes:
            site = rel3.RelatingObject
            print(f"      → On site: {site.is_a()} '{site.Name}'")

print("\n  This is how you 'walk up' the spatial tree using inverse attributes.\n")


#not generated code (almost :))
ifcopenshell.api.geometry.add_wall_representation(model, context=ctx, length=6.0, height=3.0, thickness=0.2)


