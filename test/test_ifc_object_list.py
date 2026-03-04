from pathlib import Path
from builder.models.IfcObjectList import IfcObjectList
from builder.models.IfcType import IfcType

CSV_PATH = Path(__file__).parent / "test_data" / "objects.csv"


def test_from_csv_row_count():
    result = IfcObjectList.from_csv(CSV_PATH)
    assert len(list(result)) == 2


def test_from_csv_names_and_quantities():
    items = list(IfcObjectList.from_csv(CSV_PATH))
    assert items[0].name == "Toilet"
    assert items[0].uhc == 6
    assert items[1].name == "Washbasin"
    assert items[1].uhc == 2


def test_from_csv_ifc_types():
    items = list(IfcObjectList.from_csv(CSV_PATH))
    assert items[0].ifc_type == IfcType.SANITARY_TERMINAL
    assert items[1].ifc_type == IfcType.SANITARY_TERMINAL