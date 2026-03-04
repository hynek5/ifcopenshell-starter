import os
import ifcopenshell.api
import ifcopenshell.api.context as context
import ifcopenshell.api.geometry as geometry
import ifcopenshell.api.root as root
import ifcopenshell.api.spatial as spatial
import ifcopenshell.api.aggregate as aggregate

from utils import save_model

file = ifcopenshell.file(schema="IFC4")

# 1. Create project (you have this)
project = ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcProject", name="Hello Wall Project")

# 2. Assign units (you have this)
ifcopenshell.api.run("unit.assign_unit", file)


# Create spatial hierarchy
site = root.create_entity(file, ifc_class="IfcSite", name="Site")
building = root.create_entity(file, ifc_class="IfcBuilding", name="Building")
storey = root.create_entity(file, ifc_class="IfcBuildingStorey", name="Ground Floor")

aggregate.assign_object(file, relating_object=project, products=[site])
aggregate.assign_object(file, relating_object=site, products=[building])
aggregate.assign_object(file, relating_object=building, products=[storey])




# 3. Create representation context (NEW — needed before any geometry)
body_context = context.add_context(
    file,
    context_type="Model",
    context_identifier="Body",
    target_view="MODEL_VIEW",
)

# 4. Create the wall entity (you have this)#
#wall = ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcWall", name="Masonry Wall"
wall =  root.create_entity(file, ifc_class="IfcWall",name="masonary wall")
# Put the wall inside the storey

spatial.assign_container(file, relating_structure=storey, products=[wall])

# 5. Create the 3D shape (NEW)
rep = geometry.add_wall_representation(
    file,
    context=body_context,
    length=6000.0,
    height=3000.0,
    thickness=200,
)

# 6. Attach shape to wall (NEW)
geometry.assign_representation(file, product=wall, representation=rep)

# 7. Place wall in space (NEW — without this it may not show correctly)
geometry.edit_object_placement(file, product=wall)

# 8. Save
# Get the project root (one level up from src/)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

save_model(file, os.path.join(OUTPUT_DIR, "01_hello_wall_v2.ifc"))