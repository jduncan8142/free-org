from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from free_org.db.models.menu import MenuItem
    from free_org.db.models.stand import ConcessionStand
    from free_org.db.models.window import Window

class PaymentMethod(str, Enum):
    """Enum for payment methods."""
    CASH = "cash"
    CARD = "card"  # Via Square

class Transaction(SQLModel, table=True):
    """Model representing a sale transaction."""
    
    __tablename__ = "transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    quantity: int = Field(default=1)
    unit_price: float  # Price at time of transaction
    total_amount: float  # unit_price * quantity
    payment_method: PaymentMethod
    square_transaction_id: Optional[str] = None  # For card transactions via Square
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign keys
    menu_item_id: int = Field(foreign_key="menu_items.id")
    stand_id: int = Field(foreign_key="concession_stands.id")
    window_id: Optional[int] = Field(default=None, foreign_key="windows.id")
    
    # Relationships
    menu_item: "MenuItem" = Relationship(back_populates="transactions")
    stand: "ConcessionStand" = Relationship()
    window: Optional["Window"] = Relationship(back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, amount=${self.total_amount:.2f}, method={self.payment_method})>"
    
    @classmethod
    def create_from_menu_item(cls, menu_item: "MenuItem", quantity: int = 1, 
                              payment_method: PaymentMethod = PaymentMethod.CASH,
                              square_transaction_id: Optional[str] = None,
                              window_id: Optional[int] = None) -> "Transaction":
        """Create a transaction from a menu item."""
        return cls(
            menu_item_id=menu_item.id,
            stand_id=menu_item.stand_id,
            window_id=window_id,
            unit_price=menu_item.price,
            total_amount=menu_item.price * quantity,
            quantity=quantity,
            payment_method=payment_method,
            square_transaction_id=square_transaction_id
        )