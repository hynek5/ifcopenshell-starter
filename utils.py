"""
Shared utility functions for IFC model creation and inspection.
"""
import os
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def save_model(model: ifcopenshell.file, filename: str) -> str:
    """Save an IFC model to the output directory and return the full path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    model.write(path)
    print(f"  ✓ Saved: {path}")
    return path


# ---------------------------------------------------------------------------
# Model creation helpers
# ---------------------------------------------------------------------------

def create_empty_project(name: str = "My Project") -> ifcopenshell.file:
    """
    Create a new IFC4 model with a project, unit assignment, and context.
    This is the minimal boilerplate every IFC file needs.
    """
    model = ifcopenshell.file(schema="IFC4")

    # Every IFC file needs a project — the root of the spatial tree
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name=name)

    # Assign default units (metres, square metres, etc.)
    ifcopenshell.api.run("unit.assign_unit", model)

    # Create a geometric representation context (needed for any 3D geometry later)
    ifcopenshell.api.run(
        "context.add_context", model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
    )

    return model


def build_spatial_hierarchy(
    model: ifcopenshell.file,
    site_name: str = "Default Site",
    building_name: str = "Default Building",
    storeys: list[dict] | None = None,
) -> dict:
    """
    Build the standard spatial hierarchy:
      Project → Site → Building → Storey(s)

    Args:
        storeys: list of dicts like [{"name": "Ground Floor", "elevation": 0.0}, ...]
                 Defaults to a single ground floor if not provided.

    Returns:
        dict with keys: "site", "building", "storeys" (list)
    """
    if storeys is None:
        storeys = [{"name": "Ground Floor", "elevation": 0.0}]

    project = model.by_type("IfcProject")[0]

    # Create site and aggregate it under the project
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name=site_name)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])

    # Create building and aggregate under site
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name=building_name)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])

    # Create storeys and aggregate under building
    storey_entities = []
    for s in storeys:
        storey = ifcopenshell.api.run(
            "root.create_entity", model,
            ifc_class="IfcBuildingStorey",
            name=s["name"],
        )
        storey.Elevation = s.get("elevation", 0.0)
        storey_entities.append(storey)

    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=storey_entities)

    return {
        "site": site,
        "building": building,
        "storeys": storey_entities,
    }


# ---------------------------------------------------------------------------
# Property helpers
# ---------------------------------------------------------------------------

def add_properties(
    model: ifcopenshell.file,
    element,
    pset_name: str,
    properties: dict,
) -> None:
    """
    Attach a property set with given key-value pairs to an element.

    Args:
        element:    The IFC entity (e.g., IfcWall)
        pset_name:  Name for the property set (e.g., "Pset_WallCommon")
        properties: Dict of property names to values, e.g. {"IsExternal": True, "Width": 0.3}
    """
    pset = ifcopenshell.api.run("pset.add_pset", model, product=element, name=pset_name)
    ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties=properties)


# ---------------------------------------------------------------------------
# Inspection helpers
# ---------------------------------------------------------------------------

def print_spatial_tree(model: ifcopenshell.file, indent: int = 0) -> None:
    """Print the spatial hierarchy of an IFC model as an indented tree."""
    project = model.by_type("IfcProject")[0]
    _print_spatial_node(project, indent)


def _print_spatial_node(element, indent: int) -> None:
    """Recursive helper for print_spatial_tree."""
    prefix = "  " * indent
    print(f"{prefix}├── {element.is_a()} : {element.Name or '(unnamed)'}")

    # Children via IfcRelAggregates (decomposition)
    if hasattr(element, "IsDecomposedBy"):
        for rel in element.IsDecomposedBy:
            for child in rel.RelatedObjects:
                _print_spatial_node(child, indent + 1)

    # Contained elements (products inside a spatial element)
    if hasattr(element, "ContainsElements"):
        for rel in element.ContainsElements:
            for child in rel.RelatedElements:
                child_prefix = "  " * (indent + 1)
                print(f"{child_prefix}├── {child.is_a()} : {child.Name or '(unnamed)'}")


def print_element_properties(model: ifcopenshell.file, element) -> None:
    """Print all property sets and their values for an element."""
    print(f"\n  Properties of {element.is_a()} '{element.Name}':")
    print(f"  GlobalId: {element.GlobalId}")

    psets = ifcopenshell.util.element.get_psets(element)
    if not psets:
        print("  (no property sets)")
        return

    for pset_name, props in psets.items():
        print(f"\n  [{pset_name}]")
        for key, value in props.items():
            if key == "id":
                continue  # skip internal id
            print(f"    {key} = {value}")
