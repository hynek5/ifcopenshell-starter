"""
calc_flow.py — Part 3: The Engineer.

Loads an IFC file produced by build_bathroom.py, finds the Stack Pipe (element with no
IfcRelConnectsElements where it is RelatingElement), backtracks via IfcElement.ConnectedFrom
to collect all elements that drain into it, sums their UHC from Pset_SanitaryLoad,
and prints a Load Report with recommended pipe diameter.

Usage:
    python calc_flow.py [path/to/file.ifc]
    (default: output.ifc in script directory)
"""

import os
import sys

import ifcopenshell
import ifcopenshell.util.element


# ---------------------------------------------------------------------------
# Simple UHC -> diameter table (for report)
# ---------------------------------------------------------------------------

def diameter_for_uhc(total_uhc: int) -> int:
    """Return minimum recommended diameter in mm based on total UHC (simple table)."""
    if total_uhc <= 0:
        return 50
    if total_uhc <= 9:
        return 50
    if total_uhc <= 24:
        return 75
    if total_uhc <= 50:
        return 100
    return 125


def _get_connected_to(model, element):
    """Elements this element connects TO (outgoing): RelatingElement = element."""
    out = []
    for ref in model.get_inverse(element):
        if ref.is_a("IfcRelConnectsElements") and ref.RelatingElement == element:
            out.append(ref.RelatedElement)
    return out


def _get_connected_from(model, element):
    """Elements that connect TO this element (incoming): RelatedElement = element."""
    out = []
    for ref in model.get_inverse(element):
        if ref.is_a("IfcRelConnectsElements") and ref.RelatedElement == element:
            out.append(ref.RelatingElement)
    return out


def find_stack_pipe(model, elements_with_pset):
    """Stack pipe = element with Pset_SanitaryLoad that has no outgoing connection (ConnectedTo)."""
    for entity in elements_with_pset:
        if len(_get_connected_to(model, entity)) == 0:
            return entity
    raise ValueError("No Stack Pipe found (no element with empty ConnectedTo)")


def collect_draining_entities(model, stack_entity):
    """BFS from stack backwards via ConnectedFrom: all entities that drain into the stack."""
    draining = set()
    queue = [stack_entity]
    while queue:
        current = queue.pop(0)
        if current in draining:
            continue
        draining.add(current)
        for other in _get_connected_from(model, current):
            if other not in draining:
                queue.append(other)
    draining.discard(stack_entity)
    return draining


def run_calc_flow(ifc_path: str) -> None:
    model = ifcopenshell.open(ifc_path)

    # entity -> {name, uhc} for all products with Pset_SanitaryLoad
    elements_with_pset = []
    entity_to_data = {}
    for product in model.by_type("IfcProduct"):
        psets = ifcopenshell.util.element.get_psets(product)
        if "Pset_SanitaryLoad" not in psets or "UHC" not in psets.get("Pset_SanitaryLoad", {}):
            continue
        uhc = int(psets["Pset_SanitaryLoad"].get("UHC", 0))
        name = getattr(product, "Name", None) or product.is_a()
        elements_with_pset.append(product)
        entity_to_data[product] = {"name": name, "uhc": uhc}

    if not elements_with_pset:
        print("No elements with Pset_SanitaryLoad found.")
        return

    stack = find_stack_pipe(model, elements_with_pset)
    draining = collect_draining_entities(model, stack)

    total_uhc = sum(entity_to_data[e]["uhc"] for e in draining)
    diameter_mm = diameter_for_uhc(total_uhc)

    # --- Load Report ---
    print("\n--- Load Report ---\n")
    for entity in sorted(draining, key=lambda e: (entity_to_data[e]["name"], id(e))):
        data = entity_to_data[entity]
        if data["uhc"] > 0:
            print(f"{data['name']}: {data['uhc']} UHC\n")
    print("---------------------------\n")
    print(f"Total Load on Stack Pipe: {total_uhc} UHC\n")
    print(f"Minimum Recommended Diameter: {diameter_mm}mm (Based on simple table)\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_ifc = os.path.join(script_dir, "output.ifc")
    ifc_path = sys.argv[1] if len(sys.argv) >= 2 else default_ifc

    if not os.path.isfile(ifc_path):
        print(f"Error: IFC file not found: {ifc_path}")
        sys.exit(1)

    print(f"Input: {ifc_path}")
    run_calc_flow(ifc_path)
