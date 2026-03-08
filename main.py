"""
ifc_from_csv.py — Read a CSV of building elements and write an IFC file.

CSV format:
    name,uhc,type,loc_x,loc_y,dim_x,dim_y
    Toilet,6,IfcSanitaryTerminal,1.0,1.0,0.7,0.4

Usage:
    python ifc_from_csv.py input.csv output.ifc
"""

import csv
import math
import os
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
    """One row from the layout CSV (UHC comes from uhc_library.csv)."""
    def __init__(self, id_, name, ifc_type, loc_x, loc_y, dim_x, dim_y):
        self.id = int(id_)
        self.name = name
        self.ifc_type = ifc_type
        self.loc_x = float(loc_x)
        self.loc_y = float(loc_y)
        self.dim_x = float(dim_x)
        self.dim_y = float(dim_y)


# ---------------------------------------------------------------------------
# Step 2 — UHC library and layout
# ---------------------------------------------------------------------------

def load_uhc_library(path="uhc_library.csv"):
    """Read uhc_library.csv and return a dict: device_name -> UHC (int)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"UHC library not found: {path}")
    result = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Device"].strip()
            result[name] = int(row["UHC"])
    return result


def load_layout_csv(path):
    """Read layout CSV (id, name, type, loc_x, loc_y, dim_x, dim_y) and return list of Element."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Layout file not found: {path}")
    elements = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            element = Element(
                id_=row["id"],
                name=row["name"].strip(),
                ifc_type=row["type"].strip(),
                loc_x=row["loc_x"],
                loc_y=row["loc_y"],
                dim_x=row["dim_x"],
                dim_y=row["dim_y"],
            )
            elements.append(element)
    return elements


def load_connections(path):
    """Read connections CSV (from_id, to_id) and return list of (from_id, to_id) tuples."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Connections file not found: {path}")
    connections = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            connections.append((int(row["from_id"]), int(row["to_id"])))
    return connections


# ---------------------------------------------------------------------------
# Step 3 — Build IFC model
# ---------------------------------------------------------------------------

def build_ifc(elements, connections, output_path, uhc_library):
    """Build IFC from layout elements and connections; UHC from uhc_library (device name -> UHC)."""
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

    id_to_element = {e.id: e for e in elements}
    id_to_entity = {}

    # Create one IFC entity per layout element; connections via IfcRelConnectsElements (below)
    for element in elements:
        uhc = uhc_library.get(element.name, 0)

        entity = root.create_entity(ifc_file, ifc_class=element.ifc_type, name=element.name)
        id_to_entity[element.id] = entity

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

        # Property Set Pset_SanitaryLoad: UHC only (connections via IfcElement.ConnectedTo/ConnectedFrom)
        pset = ifcopenshell.api.run("pset.add_pset", ifc_file, product=entity, name="Pset_SanitaryLoad")
        ifcopenshell.api.run("pset.edit_pset", ifc_file, pset=pset, properties={"UHC": uhc})

        print(f"  Created: {element.name} ({element.ifc_type}) UHC={uhc}")

    # Center of the face of element that is closest to (other_x, other_y); z at bottom (all same height)
    def face_center_toward(element, other_x, other_y, z=0.0):
        cx = element.loc_x + element.dim_x / 2
        cy = element.loc_y + element.dim_y / 2
        dx = other_x - cx
        dy = other_y - cy
        if abs(dx) >= abs(dy):
            x = element.loc_x + element.dim_x if dx >= 0 else element.loc_x
            y = element.loc_y + element.dim_y / 2
        else:
            x = element.loc_x + element.dim_x / 2
            y = element.loc_y + element.dim_y if dy >= 0 else element.loc_y
        return (x, y, z)

    # Connection pipes: from center of A's closest face to center of B's closest face
    pipe_thickness = 0.1
    pipe_height = 0.15
    for from_id, to_id in connections:
        a, b = id_to_element[from_id], id_to_element[to_id]
        b_center_xy = (b.loc_x + b.dim_x / 2, b.loc_y + b.dim_y / 2)
        a_center_xy = (a.loc_x + a.dim_x / 2, a.loc_y + a.dim_y / 2)
        start = face_center_toward(a, b_center_xy[0], b_center_xy[1])
        end = face_center_toward(b, a_center_xy[0], a_center_xy[1])
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy) or 0.2
        angle = math.atan2(dy, dx)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        conn_entity = root.create_entity(
            ifc_file, ifc_class="IfcFlowSegment",
            name=f"Pipe {from_id}-{to_id}",
        )
        rep = geometry.add_wall_representation(
            ifc_file, context=body_context,
            length=length, height=pipe_height, thickness=pipe_thickness,
        )
        geometry.assign_representation(ifc_file, product=conn_entity, representation=rep)
        # Place at start (center of A's closest face), local X toward end (center of B's closest face)
        geometry.edit_object_placement(
            ifc_file, product=conn_entity,
            matrix=[
                [cos_a, -sin_a, 0.0, start[0]],
                [sin_a, cos_a, 0.0, start[1]],
                [0.0, 0.0, 1.0, start[2]],
                [0.0, 0.0, 0.0, 1.0],
            ],
        )
        spatial.assign_container(ifc_file, relating_structure=storey, products=[conn_entity])
        print(f"  Connection pipe: {from_id} -> {to_id}")

    # IfcRelConnectsElements: relating (from) drains into related (to); used by calc_flow via IfcElement.ConnectedTo/ConnectedFrom
    for from_id, to_id in connections:
        geometry.connect_element(
            ifc_file,
            relating_element=id_to_entity[from_id],
            related_element=id_to_entity[to_id],
        )
        print(f"  IfcRelConnectsElements: {from_id} -> {to_id}")

    ifc_file.write(output_path)
    print(f"\nSaved: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    output_ifc = sys.argv[1] if len(sys.argv) == 2 else "output.ifc"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    library_path = os.path.join(script_dir, "uhc_library.csv")
    layout_path = os.path.join(script_dir, "layout.csv")
    connections_path = os.path.join(script_dir, "connections.csv")

    uhc_library = load_uhc_library(library_path)
    print(f"UHC library: {uhc_library}")

    elements = load_layout_csv(layout_path)
    connections = load_connections(connections_path)
    print(f"Layout: {len(elements)} elements, {len(connections)} connections\n")

    build_ifc(elements, connections, output_ifc, uhc_library)