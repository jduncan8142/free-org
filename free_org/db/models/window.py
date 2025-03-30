from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

class Window(SQLModel, table=True):
    """Model representing a service window at a concession stand."""
    
    __tablename__ = "windows"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign keys
    stand_id: int = Field(foreign_key="concession_stands.id")
    
    # Relationships
    stand: "ConcessionStand" = Relationship(back_populates="windows")
    transactions: list["Transaction"] = Relationship(back_populates="window")
    
    def __repr__(self) -> str:
        return f"<Window(id={self.id}, name='{self.name}', stand_id={self.stand_id})>"