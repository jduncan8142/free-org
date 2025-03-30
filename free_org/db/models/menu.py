from typing import Optional, List, ForwardRef
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

# Import the join table
from free_org.db.models.menu_inventory import MenuItemInventory

# Forward references to avoid circular imports
ConcessionStand = ForwardRef("ConcessionStand")
Transaction = ForwardRef("Transaction")


class MenuItem(SQLModel, table=True):
    """Model representing a menu item that can be displayed and sold."""

    __tablename__ = "menu_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float
    image_path: Optional[str] = None  # Path to image for display on TVs
    is_available: bool = Field(default=True)  # Controlled by inventory threshold
    is_featured: bool = Field(default=False)  # For featured items on displays
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign keys
    stand_id: Optional[int] = Field(default=None, foreign_key="concession_stands.id")
    # Removed direct inventory_item_id field in favor of many-to-many relationship

    # Relationships
    stand: Optional["ConcessionStand"] = Relationship(back_populates="menu_items")
    # Replaced direct inventory_item relationship with many-to-many
    menu_item_inventories: List[MenuItemInventory] = Relationship(back_populates="menu_item")
    transactions: List["Transaction"] = Relationship(back_populates="menu_item")

    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name='{self.name}', price=${self.price:.2f})>"

    @property
    def should_display(self) -> bool:
        """
        Determine if this item should be displayed on menus.
        Returns False if item is not available or if ANY linked inventory is below threshold.
        """
        if not self.is_available:
            return False

        # Check all linked inventory items - if ANY are unavailable, return False
        for link in self.menu_item_inventories:
            if not link.inventory_item.is_available:
                return False

        # All inventory items are available
        return True
