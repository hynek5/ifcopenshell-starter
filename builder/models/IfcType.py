from enum import Enum


class IfcType(Enum):
    SANITARY_TERMINAL = "IfcSanitaryTerminal"
    WALL = "IfcWall"
    SLAB = "IfcSlab"
    COLUMN = "IfcColumn"

    @staticmethod
    def from_str(value: str) -> "IfcType":
        value = value.strip()
        for member in IfcType:
            if member.value == value:
                return member
        valid = [m.value for m in IfcType]
        raise ValueError(f"Unsupported type '{value}'. Supported: {valid}")


    @property
    def ifc_class(self) -> str:
        return self.value