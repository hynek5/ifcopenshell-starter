# ---------------------------------------------------------------------------
# 2. Element request — one parsed line from CSV
# ---------------------------------------------------------------------------
from dataclasses import dataclass

from .IfcType import IfcType


@dataclass
class IfcObject:
    """A single line from the input CSV."""
    name: str
    uhc: int
    loc_x: float
    loc_y: float
    dim_x: float
    dim_y: float
    ifc_type: IfcType

    def instance_names(self) -> list[str]:
        return [f"{self.name} {str(i + 1).zfill(2)}" for i in range(self.uhc)]