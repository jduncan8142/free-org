from sqlmodel import Field, SQLModel, Relationship
import uuid
from typing import List, Optional
from decimal import Decimal


class Org(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    tax_id: Optional[str] = None
    location_types: List["LocationType"] = Relationship(back_populates="org")
    locations: List["Location"] = Relationship(back_populates="org")
    item_types: List["ItemType"] = Relationship(back_populates="org")
    items: List["Item"] = Relationship(back_populates="org")
    unit_of_measures: List["UnitOfMeasure"] = Relationship(back_populates="org")


class User(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    password: str
    pin: int


class LocationType(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="org.id")
    org: Org | None = Relationship(back_populates="location_types")
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    


class Location(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="org.id")
    org: Org | None = Relationship(back_populates="locations")
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    name2: Optional[str] = None
    name3: Optional[str] = None
    name4: Optional[str] = None
    house_number: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    street3: Optional[str] = None
    street4: Optional[str] = None
    street5: Optional[str] = None
    street6: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    building: Optional[str] = None
    floor: Optional[str] = None
    district: Optional[str] = None
    items: List["ItemLocation"] = Relationship(back_populates="location")
    storage_bins: List["StorageBin"] = Relationship(back_populates="location")


class UnitOfMeasure(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="org.id")
    org: Org | None = Relationship(back_populates="unit_of_measures")
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    items: List["Item"] = Relationship(back_populates="unit_of_measure")


class ItemType(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="org.id")
    org: Org | None = Relationship(back_populates="item_types")
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    items: List["Item"] = Relationship(back_populates="item_type")


class Item(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="org.id")
    org: Org | None = Relationship(back_populates="items")
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    item_type_id: uuid.UUID | None = Field(default=None, foreign_key="itemtype.id")
    item_type: ItemType | None = Relationship(back_populates="items")
    unit_of_measure_id: uuid.UUID | None = Field(default=None, foreign_key="unitofmeasure.id")
    unit_of_measure: UnitOfMeasure | None = Relationship(back_populates="items")
    locations: List["ItemLocation"] = Relationship(back_populates="item")


class ItemLocation(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    item_id: uuid.UUID | None = Field(default=None, foreign_key="item.id")
    item: Item | None = Relationship(back_populates="locations")
    location_id: uuid.UUID | None = Field(default=None, foreign_key="location.id")
    location: Location | None = Relationship(back_populates="items")


class ItemUnitOfMeasure(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    item_id: uuid.UUID | None = Field(default=None, foreign_key="item.id")
    primary_unit_of_measure_id: uuid.UUID | None = Field(default=None, foreign_key="unitofmeasure.id")
    secondary_unit_of_measure_id: uuid.UUID | None = Field(default=None, foreign_key="unitofmeasure.id")
    conversion_factor: Optional[Decimal] = Field(default=1, max_digits=32, decimal_places=10)


class StorageBin(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    location_id: uuid.UUID | None = Field(default=None, foreign_key="location.id")
    location: Location | None = Relationship(back_populates="storage_bins")
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    items: List["ItemStorageBin"] = Relationship(back_populates="storage_bin")


class ItemStorageBin(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    item_id: uuid.UUID | None = Field(default=None, foreign_key="item.id")
    item: Item | None = Relationship(back_populates="locations")
    storage_bin_id: uuid.UUID | None = Field(default=None, foreign_key="storagebin.id")
    storage_bin: StorageBin | None = Relationship(back_populates="items")
    quantity: Optional[Decimal] = Field(default=0, max_digits=16, decimal_places=5)
    
