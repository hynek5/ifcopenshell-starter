

## Bathroom Pipeline (build_bathroom + calc_flow)

Two scripts work together to build a bathroom IFC model and calculate drain load.

### Input files (in project root)

| File | Purpose |
|---|---|
| `layout.csv` | Bathroom elements — id, name, IFC type, position (x/y), dimensions |
| `connections.csv` | Drain connections — `from_id,to_id` pairs |
| `uhc_library.csv` | UHC (Unit Hydraulic Capacity) lookup by device name |

### Step 1 — Build the IFC model

Reads the three CSVs and writes an IFC4 file with all elements, pipe geometry, and `Pset_SanitaryLoad` properties.

```bash
python build_bathroom.py              # outputs output.ifc
python build_bathroom.py my_bath.ifc  # custom output path
```

### Step 2 — Calculate drain load

Loads the IFC, finds the Stack Pipe (element with no outgoing connection), walks upstream via `IfcRelConnectsElements`, sums UHC, and prints a load report with recommended pipe diameter.

```bash
python calc_flow.py              # reads output.ifc by default
python calc_flow.py my_bath.ifc  # custom IFC path
```

Example output:
```
--- Load Report ---

Toilet: 4 UHC
Washbasin: 3 UHC
...
---------------------------
Total Load on Stack Pipe: 22 UHC
Minimum Recommended Diameter: 75mm (Based on simple table)
```

---
