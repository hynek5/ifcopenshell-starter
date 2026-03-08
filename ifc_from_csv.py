"""
ifc_from_csv.py — Read a CSV of building elements and write an IFC file.

CSV format:
    name,uhc,type,loc_x,loc_y,dim_x,dim_y
    Toilet,6,IfcSanitaryTerminal,1.0,1.0,0.7,0.4

Usage:
    python ifc_from_csv.py input.csv output.ifc
"""

import csv
import io
import sys

import ifcopenshell
import ifcopenshell.api.root as root
import ifcopenshell.api.unit as unit
import ifcopenshell.api.context as context
import ifcopenshell.api.aggregate as aggregate
import ifcopenshell.api.spatial as spatial
import ifcopenshell.api.geometry as geometry


# ---------------------------------------------------------------------------
# Step 1 — Data classes
# ---------------------------------------------------------------------------

class Element:
    """One row from the CSV."""
    def __init__(self, name, quantity, ifc_type, loc_x, loc_y, dim_x, dim_y):
        self.name = name
        self.quantity = int(quantity)
        self.ifc_type = ifc_type
        self.loc_x = float(loc_x)
        self.loc_y = float(loc_y)
        self.dim_x = float(dim_x)
        self.dim_y = float(dim_y)


# ---------------------------------------------------------------------------
# Step 2 — CSV data (inline) and parser
# ---------------------------------------------------------------------------

CSV_DATA = """\
name,uhc,type,loc_x,loc_y,dim_x,dim_y
Toilet,6,IfcSanitaryTerminal,1.0,1.0,0.7,0.4
Washbasin,2,IfcSanitaryTerminal,1.0,10.5,0.2,0.4
Pipe,2,IfcFlowSegment,1.0,3.5,0.2,0.4
Drain,2,IfcWasteTerminal,1.0,5.5,0.2,0.4
"""


def parse_csv(text):
    elements = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        element = Element(
            name=row["name"].strip(),
            quantity=row["uhc"],
            ifc_type=row["type"].strip(),
            loc_x=row["loc_x"],
            loc_y=row["loc_y"],
            dim_x=row["dim_x"],
            dim_y=row["dim_y"],
        )
        elements.append(element)
    return elements


# ---------------------------------------------------------------------------
# Step 3 — Build IFC model
# ---------------------------------------------------------------------------

def build_ifc(elements, output_path):
    # Create empty IFC4 file
    ifc_file = ifcopenshell.file(schema="IFC4")

    # Project + units
    project = root.create_entity(ifc_file, ifc_class="IfcProject", name="My Project")
    unit.assign_unit(ifc_file)

    # Representation context (needed for geometry)
    body_context = context.add_context(
        ifc_file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
    )

    # Spatial hierarchy: Project → Site → Building → Storey
    site = root.create_entity(ifc_file, ifc_class="IfcSite", name="Site")
    building = root.create_entity(ifc_file, ifc_class="IfcBuilding", name="Building")
    storey = root.create_entity(ifc_file, ifc_class="IfcBuildingStorey", name="Ground Floor")

    aggregate.assign_object(ifc_file, relating_object=project, products=[site])
    aggregate.assign_object(ifc_file, relating_object=site, products=[building])
    aggregate.assign_object(ifc_file, relating_object=building, products=[storey])

    # Create one IFC entity per element
    for element in elements:
        entity = root.create_entity(ifc_file, ifc_class=element.ifc_type, name=element.name)

        # Simple box geometry using the element's dimensions
        rep = geometry.add_wall_representation(
            ifc_file,
            context=body_context,
            length=element.dim_x,
            height=1.0,
            thickness=element.dim_y,
        )
        geometry.assign_representation(ifc_file, product=entity, representation=rep)

        # Place the element at (loc_x, loc_y)
        geometry.edit_object_placement(
            ifc_file,
            product=entity,
            matrix=[
                [1.0, 0.0, 0.0, element.loc_x],
                [0.0, 1.0, 0.0, element.loc_y],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        )

        # Put the element into the storey
        spatial.assign_container(ifc_file, relating_structure=storey, products=[entity])

        print(f"  Created: {element.name} ({element.ifc_type})")

    ifc_file.write(output_path)
    print(f"\nSaved: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    output_ifc = sys.argv[1] if len(sys.argv) == 2 else "output.ifc"

    print("Using inline CSV data")
    elements = parse_csv(CSV_DATA)
    print(f"Found {len(elements)} elements\n")

    build_ifc(elements, output_ifc)