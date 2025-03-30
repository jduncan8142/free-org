from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

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
    inventory_item_id: Optional[int] = Field(default=None, foreign_key="inventory_items.id")
    
    # Relationships
    stand: Optional["ConcessionStand"] = Relationship(back_populates="menu_items")
    inventory_item: Optional["InventoryItem"] = Relationship(back_populates="menu_items")
    transactions: List["Transaction"] = Relationship(back_populates="menu_item")
    
    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name='{self.name}', price=${self.price:.2f})>"
    
    @property
    def should_display(self) -> bool:
        """
        Determine if this item should be displayed on menus.
        Returns False if item is not available or if linked inventory is below threshold.
        """
        if not self.is_available:
            return False
        
        if self.inventory_item and not self.inventory_item.is_available:
            return False
            
        return True