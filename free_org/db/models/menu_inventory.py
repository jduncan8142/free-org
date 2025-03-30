from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class MenuItemInventory(SQLModel, table=True):
    """Join table for many-to-many relationship between menu items and inventory items."""
    
    __tablename__ = "menu_item_inventory"
    
    menu_item_id: int = Field(foreign_key="menu_items.id", primary_key=True)
    inventory_item_id: int = Field(foreign_key="inventory_items.id", primary_key=True)
    quantity_required: int = Field(default=1)  # How many units of this inventory item are needed
    
    # Define relationships to both sides
    menu_item: "MenuItem" = Relationship(back_populates="menu_item_inventories")
    inventory_item: "InventoryItem" = Relationship(back_populates="menu_item_inventories")