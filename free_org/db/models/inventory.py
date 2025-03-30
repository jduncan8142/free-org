from enum import Enum
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

class ItemType(str, Enum):
    """Enum for inventory item types."""
    FOOD = "food"
    DRINK = "drink"
    SUPPLY = "supply"

class ItemUnit(str, Enum):
    """Enum for inventory item units of measurement."""
    EACH = "each"
    BOX = "box"
    CASE = "case"
    POUND = "pound"
    OUNCE = "ounce"
    GALLON = "gallon"
    LITER = "liter"

class InventoryItem(SQLModel, table=True):
    """Model representing an inventory item in a concession stand."""
    
    __tablename__ = "inventory_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    item_type: ItemType
    unit: ItemUnit
    quantity: int = Field(default=0)
    minimum_threshold: int = Field(default=5)  # Threshold for auto-removing from menu
    unit_cost: float = Field(default=0.0)  # Cost per unit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign key to stand
    stand_id: Optional[int] = Field(default=None, foreign_key="concession_stands.id")
    
    # Relationships
    stand: Optional["ConcessionStand"] = Relationship(back_populates="inventory_items")
    menu_items: List["MenuItem"] = Relationship(back_populates="inventory_item")
    
    def __repr__(self) -> str:
        return f"<InventoryItem(id={self.id}, name='{self.name}', type='{self.item_type}', quantity={self.quantity})>"
    
    @property
    def is_available(self) -> bool:
        """Check if item has sufficient inventory to be on menu."""
        return self.quantity > self.minimum_threshold