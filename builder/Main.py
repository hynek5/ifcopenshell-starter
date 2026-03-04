"""
main.py — Entry point for IFC layout generation.
"""
import sys

from layout import Layout
from models.IfcObjectList import IfcObjectList


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <input.csv> [output.ifc]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/layout.ifc"

    # Parse
    objects = IfcObjectList.from_csv(input_path)
    print(f"Loaded {objects.total_count()} elements from {input_path}")

    # Build
    layout = Layout(objects)
    layout.build()

    # Save
    layout.save(output_path)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()