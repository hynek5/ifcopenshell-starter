"""
01 - Hello Wall
================
The simplest possible IFC model: a project with one wall.
Demonstrates: model creation, entity creation, saving.

Equivalent to "Hello World" for IFC.
"""
import ifcopenshell
import ifcopenshell.api.geometry as geometry

from utils import save_model

print("\n=== 01: Hello Wall ===\n")

# --- Step 1: Create an empty IFC4 file ---
model = ifcopenshell.file(schema="IFC4")
print("  Created empty IFC4 model")

# --- Step 2: Create a project (mandatory root entity) ---
project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="Hello Wall Project")
print(f"  Created project: {project.Name} (GlobalId: {project.GlobalId})")

# --- Step 3: Assign default units ---
ifcopenshell.api.run("unit.assign_unit", model)
print("  Assigned default SI units")

# 3. Create representation context (NEW — needed before any geometry)
body_context = context.add_context(
    model,
    context_type="Model",
    context_identifier="Body",
    target_view="MODEL_VIEW",
)

# --- Step 4: Create a wall ---
wall = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Masonry Wall")
print(f"  Created wall: {wall.Name} (GlobalId: {wall.GlobalId})")

# --- Step 5: Save ---
path = save_model(model, "01_hello_wall.ifc")

# --- Let's peek at what the raw IFC looks like ---
print("\n  Raw IFC content:")
print("  " + "-" * 60)
with open(path, "r") as f:
    for line in f:
        print(f"  {line.rstrip()}")
print("  " + "-" * 60)

print("\n  Note: The wall exists but has no spatial location")
print("  (not assigned to any storey) and no geometry.")
print("  We'll fix that in the next scripts.\n")

geometry.add_wall_representation(model, context=wall, length=6.0, height=3.0, thickness=0.2)
