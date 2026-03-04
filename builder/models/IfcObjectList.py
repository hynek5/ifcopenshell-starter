from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from .IfcObject import IfcObject
from .IfcType import IfcType


class IfcObjectList:
    """Collection of ElementRequests parsed from CSV."""

    def __init__(self):
        self._items: list[IfcObject] = []

    def append(self, request: IfcObject) -> None:
        self._items.append(request)

    def __iter__(self) -> Iterator[IfcObject]:
        return iter(self._items)

    def filter_by_type(self, ifc_type: IfcType) -> Iterator[IfcObject]:
        return (r for r in self._items if r.ifc_type == ifc_type)

    def total_count(self) -> int:
        return sum(r.uhc for r in self._items)

    @classmethod
    def from_csv(cls, filepath: str | Path) -> IfcObjectList:
        object_list = cls()
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                request = IfcObject(
                    name=row["name"].strip(),
                    uhc=int(row["uhc"]),
                    ifc_type=IfcType.from_str(row["type"]),
                    loc_x=float(row["loc_x"]),
                    loc_y=float(row["loc_y"]),
                    dim_x=float(row["dim_x"]),
                    dim_y=float(row["dim_y"]),
                )
                object_list.append(request)
        return object_list

