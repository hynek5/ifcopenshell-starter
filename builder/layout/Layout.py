"""
layout.py — Creates an IFC model from a list of IfcObjects.
"""
import math

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.root as root
import ifcopenshell.api.unit as unit
import ifcopenshell.api.context as context
import ifcopenshell.api.aggregate as aggregate
import ifcopenshell.api.spatial as spatial
import ifcopenshell.api.geometry as geometry

from models import IfcObject, IfcObjectList


class Layout:
    """
    Creates an IFC model from a list of IfcObjects.

    Usage:
        objects = IfcObjectList.from_csv("elements.csv")
        layout = layout(objects)
        layout.build()
        layout.save("output/layout.ifc")
    """

    def __init__(self, objects: IfcObjectList):
        self.objects = objects
        self.file = None
        self.project = None
        self.site = None
        self.building = None
        self.storey = None
        self.body_context = None

    def _init_model(self) -> None:
        """Create the IFC file with project, spatial hierarchy, and context."""
        self.file = ifcopenshell.file(schema="IFC4")

        # Project
        self.project = root.create_entity(self.file, ifc_class="IfcProject", name="layout Project")
        unit.assign_unit(self.file)

        # Representation context
        self.body_context = context.add_context(
            self.file,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW",
        )

        # Spatial hierarchy: Project → Site → Building → Storey
        self.site = root.create_entity(self.file, ifc_class="IfcSite", name="Site")
        self.building = root.create_entity(self.file, ifc_class="IfcBuilding", name="Building")
        self.storey = root.create_entity(self.file, ifc_class="IfcBuildingStorey", name="Ground Floor")

        aggregate.assign_object(self.file, relating_object=self.project, products=[self.site])
        aggregate.assign_object(self.file, relating_object=self.site, products=[self.building])
        aggregate.assign_object(self.file, relating_object=self.building, products=[self.storey])

    def _create_element(self, obj: IfcObject) -> ifcopenshell.entity_instance:
        """Create a single IFC entity with geometry and placement from an IfcObject."""
        entity = root.create_entity(
            self.file,
            ifc_class=obj.ifc_type.ifc_class,
            name=obj.name,
        )

        rep = self.create_box_representation(obj.dim_x,
                                             obj.dim_y)

        geometry.assign_representation(self.file, product=entity, representation=rep)

        # Placement
        geometry.edit_object_placement(
            self.file,
            product=entity,
            matrix=[
                [1.0, 0.0, 0.0, obj.loc_x],
                [0.0, 1.0, 0.0, obj.loc_y],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        )

        # Assign to storey
        spatial.assign_container(self.file, relating_structure=self.storey, products=[entity])

        return entity

    def validate(self) -> list[str]:
        """Validate the layout before building. Returns list of error messages."""
        raise NotImplementedError

    def build(self) -> None:
        """Initialize the model and create all elements."""
        self._init_model()
        for obj in self.objects:
            self._create_element(obj)

    def save(self, filepath: str) -> None:
        """Write the IFC file to disk."""
        if self.file is None:
            raise RuntimeError("Call build() before save()")
        self.file.write(filepath)

    def create_box_representation(self, dim_x: float, dim_y: float, height: float = 1.0):
        """Create a simple box. Uses wall representation internally."""
        return geometry.add_wall_representation(
            self.file, context=self.body_context,
            length=dim_x, height=height, thickness=dim_y,
        )