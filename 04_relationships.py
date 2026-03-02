"""
04 - Relationships
==================
Deep dive into IFC relationships — forward and inverse traversal,
listing all relationships in a model, and understanding the graph structure.

Demonstrates:
  - All 5 relationship families (Decomposes, Assigns, Connects, Defines, Associates)
  - Forward traversal (from relationship → targets)
  - Inverse traversal (from element → relationships)
  - Material assignment via IfcRelAssociatesMaterial
  - Grouping via IfcRelAssignsToGroup
  - The graph-walking algorithm from the presentation (slide 25)
"""
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from utils import (
    create_empty_project,
    build_spatial_hierarchy,
    add_properties,
    save_model,
)

print("\n=== 04: Relationships ===\n")

# --- Setup ---
model = create_empty_project("Relationships Demo")
hierarchy = build_spatial_hierarchy(model, storeys=[
    {"name": "Ground Floor", "elevation": 0.0},
])
storey = hierarchy["storeys"][0]

# Create several elements
wall_a = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall A")
wall_b = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall B")
slab = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="Floor Slab")
column = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcColumn", name="Column C1")

# Assign to storey (IfcRelContainedInSpatialStructure)
ifcopenshell.api.run(
    "spatial.assign_container", model,
    relating_structure=storey,
    products=[wall_a, wall_b, slab, column],
)
print("  Created 4 elements in one storey")

# --- 1. IfcRelDefinesByProperties (Defines family) ---
add_properties(model, wall_a, "Pset_WallCommon", {"IsExternal": True, "LoadBearing": True})
add_properties(model, wall_b, "Pset_WallCommon", {"IsExternal": False, "LoadBearing": False})
print("  Added property sets (IfcRelDefinesByProperties)")

# --- 2. IfcRelDefinesByType (Defines family) ---
wall_type = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWallType", name="Concrete Wall 200mm")
ifcopenshell.api.run("type.assign_type", model, related_objects=[wall_a, wall_b], relating_type=wall_type)
print("  Assigned wall type (IfcRelDefinesByType)")

# --- 3. IfcRelAssociatesMaterial (Associates family) ---
material = ifcopenshell.api.run("material.add_material", model, name="Concrete C30/37")
ifcopenshell.api.run("material.assign_material", model, products=[wall_a, wall_b], material=material)
print("  Assigned material (IfcRelAssociatesMaterial)")

# --- 4. IfcRelAssignsToGroup (Assigns family) ---
group = ifcopenshell.api.run("group.add_group", model, name="Load-Bearing Elements")
ifcopenshell.api.run("group.assign_group", model, group=group, products=[wall_a, column])
print("  Created group (IfcRelAssignsToGroup)")

# --- Save ---
save_model(model, "04_relationships.ifc")

# =========================================================================
# ANALYSIS: List all relationships in the model
# =========================================================================
print("\n  --- All relationships in the model ---\n")

all_rels = model.by_type("IfcRelationship")
print(f"  Total relationship entities: {len(all_rels)}\n")

# Group by class
from collections import Counter
rel_counts = Counter(rel.is_a() for rel in all_rels)
for cls, count in sorted(rel_counts.items()):
    print(f"  {cls}: {count}")

# =========================================================================
# TRAVERSAL: Walk the graph from Wall A
# =========================================================================
print(f"\n  --- Graph walk starting from '{wall_a.Name}' ---\n")

# 1. Spatial containment (where is it?)
for rel in wall_a.ContainedInStructure:
    print(f"  CONTAINED IN → {rel.RelatingStructure.is_a()} '{rel.RelatingStructure.Name}'")

# 2. Type (what type is it?)
for rel in wall_a.IsTypedBy:
    print(f"  IS TYPE OF   → {rel.RelatingType.is_a()} '{rel.RelatingType.Name}'")

# 3. Properties (what data does it have?)
for rel in wall_a.IsDefinedBy:
    if rel.is_a("IfcRelDefinesByProperties"):
        pset = rel.RelatingPropertyDefinition
        print(f"  DEFINED BY   → {pset.is_a()} '{pset.Name}'")

# 4. Material (what is it made of?)
for rel in wall_a.HasAssociations:
    if rel.is_a("IfcRelAssociatesMaterial"):
        mat = rel.RelatingMaterial
        print(f"  MATERIAL     → {mat.is_a()} '{mat.Name}'")

# 5. Group membership
for rel in wall_a.HasAssignments:
    if rel.is_a("IfcRelAssignsToGroup"):
        print(f"  IN GROUP     → {rel.RelatingGroup.is_a()} '{rel.RelatingGroup.Name}'")

# =========================================================================
# REVERSE: Find all elements that share a material
# =========================================================================
print(f"\n  --- All elements with material '{material.Name}' ---\n")

for rel in model.by_type("IfcRelAssociatesMaterial"):
    if rel.RelatingMaterial == material:
        for element in rel.RelatedObjects:
            print(f"  {element.is_a()} '{element.Name}'")

# =========================================================================
# GENERIC GRAPH WALKER (the algorithm from slide 25)
# =========================================================================
print("\n  --- Generic graph walker ---\n")


def walk_relationships(element, depth: int = 0, visited: set | None = None):
    """
    Walk all relationships from an element, printing what we find.
    This is the algorithm from slide 25:
      Step 1: Start at element
      Step 2: Find all relationships referencing it
      Step 3: Jump to the other side
    """
    if visited is None:
        visited = set()

    element_id = element.id()
    if element_id in visited:
        return
    visited.add(element_id)

    prefix = "  " + "  " * depth
    print(f"{prefix}[{element.is_a()}] {element.Name or element.GlobalId}")

    # Find ALL relationships that reference this element
    # (using inverse_references — the low-level approach)
    for ref in model.get_inverse(element):
        if ref.is_a("IfcRelationship"):
            # Determine the "other side" of the relationship
            info = ref.get_info()
            for attr_name, attr_value in info.items():
                if attr_name.startswith("Relating") and attr_value and attr_value != element:
                    if hasattr(attr_value, "is_a"):
                        print(f"{prefix}  --({ref.is_a()})--→ [{attr_value.is_a()}] "
                              f"{getattr(attr_value, 'Name', '?')}")


print("  Walking from Wall A:")
walk_relationships(wall_a)

print("\n  Walking from Column C1:")
walk_relationships(column)

print()
