"""
03 - Properties
===============
Attach property sets to elements and read them back.

Demonstrates:
  - Creating IfcPropertySet via the pset API
  - Different value types (bool, float, string, int)
  - IfcRelDefinesByProperties relationship
  - Reading properties back with ifcopenshell.util.element
  - Sharing a property set across multiple elements
  - Type properties via IfcRelDefinesByType
"""
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from utils import (
    create_empty_project,
    build_spatial_hierarchy,
    add_properties,
    save_model,
    print_element_properties,
)

print("\n=== 03: Properties ===\n")

# --- Setup: create model with spatial hierarchy and elements ---
model = create_empty_project("Properties Demo")
hierarchy = build_spatial_hierarchy(model, storeys=[
    {"name": "Ground Floor", "elevation": 0.0},
])
storey = hierarchy["storeys"][0]

wall_ext = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Exterior Wall")
wall_int = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Interior Wall")
slab = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="Ground Slab")

ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, products=[wall_ext, wall_int, slab])
print("  Created model with 2 walls and 1 slab")

# --- Step 1: Add a standard property set to the exterior wall ---
add_properties(model, wall_ext, "Pset_WallCommon", {
    "IsExternal": True,
    "ThermalTransmittance": 0.24,       # U-value in W/(m²·K)
    "LoadBearing": True,
    "FireRating": "REI 120",
    "Reference": "EXT-WALL-300",
})
print("  Added Pset_WallCommon to exterior wall")

# --- Step 2: Add custom properties (your own data) ---
add_properties(model, wall_ext, "Pset_UserDefined", {
    "Contractor": "StavbaCZ s.r.o.",
    "PlannedInstallDate": "2026-04-15",
    "CostPerM2": 1850.0,
    "Priority": 1,
})
print("  Added Pset_UserDefined to exterior wall")

# --- Step 3: Add properties to interior wall ---
add_properties(model, wall_int, "Pset_WallCommon", {
    "IsExternal": False,
    "ThermalTransmittance": 0.0,         # interior wall — not relevant
    "LoadBearing": False,
    "FireRating": "EI 60",
    "Reference": "INT-WALL-150",
})
print("  Added Pset_WallCommon to interior wall")

# --- Step 4: Add properties to slab ---
add_properties(model, slab, "Pset_SlabCommon", {
    "IsExternal": False,
    "LoadBearing": True,
    "PitchAngle": 0.0,
    "Reference": "SLAB-250",
})
print("  Added Pset_SlabCommon to slab")

# --- Step 5: Create a wall type and assign both walls to it ---
# This is like OOP: the type is a class, walls are instances
wall_type = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWallType", name="Brick Wall 300mm")
ifcopenshell.api.run("type.assign_type", model, related_objects=[wall_ext, wall_int], relating_type=wall_type)

# Type-level properties (shared by all instances)
add_properties(model, wall_type, "Pset_WallTypeProperties", {
    "Material": "Clay Brick",
    "NominalThickness": 300.0,
    "AcousticRating": "Rw 52 dB",
})
print("  Created IfcWallType and assigned to both walls")

# --- Save ---
save_model(model, "03_properties.ifc")

# --- Step 6: Read everything back ---
print("\n  --- Reading properties back ---")

for element in [wall_ext, wall_int, slab]:
    print_element_properties(model, element)

# --- Step 7: Show the relationship structure ---
print("\n\n  --- How properties connect in the file ---")
for rel in model.by_type("IfcRelDefinesByProperties"):
    pset = rel.RelatingPropertyDefinition
    elements = [e.Name for e in rel.RelatedObjects]
    print(f"  IfcRelDefinesByProperties → Pset: '{pset.Name}' → Elements: {elements}")

for rel in model.by_type("IfcRelDefinesByType"):
    type_entity = rel.RelatingType
    instances = [e.Name for e in rel.RelatedObjects]
    print(f"  IfcRelDefinesByType → Type: '{type_entity.Name}' → Instances: {instances}")

print()
