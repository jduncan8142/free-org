from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from free_org.db.models.window import Window
    from free_org.db.models.inventory import InventoryItem
    from free_org.db.models.menu import MenuItem

    windows: List["Window"] = Relationship(back_populates="stand")


class ConcessionStand(SQLModel, table=True):
    """Model representing a physical concession stand."""

    __tablename__ = "concession_stands"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    location: str
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships - will be defined once other models are created
    inventory_items: List["InventoryItem"] = Relationship(back_populates="stand")
    menu_items: List["MenuItem"] = Relationship(back_populates="stand")

    def __repr__(self) -> str:
        return f"<ConcessionStand(id={self.id}, name='{self.name}', location='{self.location}')>"
