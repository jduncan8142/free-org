from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from datetime import datetime, date

from free_org.db import get_session, Transaction, PaymentMethod, MenuItem, InventoryItem

router = APIRouter()


@router.get("/", response_model=List[Transaction])
async def get_all_transactions(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    stand_id: Optional[int] = None,
    payment_method: Optional[PaymentMethod] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """
    Get all transactions, with optional filtering.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **stand_id**: Filter by concession stand ID
    - **payment_method**: Filter by payment method (cash, card)
    - **date_from**: Filter by transactions on or after this date
    - **date_to**: Filter by transactions on or before this date
    """
    query = select(Transaction)

    # Apply filters
    if stand_id is not None:
        query = query.where(Transaction.stand_id == stand_id)

    if payment_method is not None:
        query = query.where(Transaction.payment_method == payment_method)

    if date_from is not None:
        query = query.where(Transaction.created_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to is not None:
        query = query.where(Transaction.created_at <= datetime.combine(date_to, datetime.max.time()))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    transactions = session.exec(query).all()
    return transactions


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: int, session: Session = Depends(get_session)):
    """
    Get a specific transaction by ID.

    - **transaction_id**: The ID of the transaction to retrieve
    """
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction with ID {transaction_id} not found"
        )
    return transaction


@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    menu_item_id: int = Body(...),
    quantity: int = Body(...),
    payment_method: PaymentMethod = Body(...),
    square_transaction_id: Optional[str] = Body(None),
    session: Session = Depends(get_session),
):
    """
    Record a new sales transaction and update inventory.

    - **menu_item_id**: ID of the menu item sold
    - **quantity**: Quantity sold
    - **payment_method**: Method of payment (cash or card)
    - **square_transaction_id**: For card payments via Square, the transaction ID
    """
    # Validate menu item exists
    menu_item = session.get(MenuItem, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Check if menu item is available
    if not menu_item.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Menu item '{menu_item.name}' is not available"
        )

    # If Square payment, ensure transaction ID is provided
    if payment_method == PaymentMethod.CARD and not square_transaction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Square transaction ID required for card payments"
        )

    # Create transaction
    transaction = Transaction.create_from_menu_item(
        menu_item=menu_item,
        quantity=quantity,
        payment_method=payment_method,
        square_transaction_id=square_transaction_id,
    )

    # Save transaction
    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    # Update inventory if menu item is linked to inventory
    if menu_item.inventory_item_id:
        inventory_item = session.get(InventoryItem, menu_item.inventory_item_id)
        if inventory_item:
            # Reduce inventory quantity
            if inventory_item.quantity >= quantity:
                inventory_item.quantity -= quantity

                # Check if it crossed below threshold
                was_available = inventory_item.is_available

                # Save inventory changes
                session.add(inventory_item)
                session.commit()

                # If availability changed, update menu items
                if was_available and not inventory_item.is_available:
                    # Find all menu items using this inventory
                    menu_query = select(MenuItem).where(MenuItem.inventory_item_id == inventory_item.id)
                    for item in session.exec(menu_query).all():
                        item.is_available = False
                        session.add(item)

                    session.commit()
            else:
                # This shouldn't happen with proper validation, but handle just in case
                inventory_item.quantity = 0
                inventory_item.is_available = False
                session.add(inventory_item)
                session.commit()

    return transaction


@router.get("/summary/daily", response_model=dict)
async def get_daily_sales_summary(
    date_from: date = None,
    date_to: date = None,
    stand_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    """
    Get daily sales summary.

    - **date_from**: Start date for summary (defaults to all time)
    - **date_to**: End date for summary (defaults to all time)
    - **stand_id**: Filter by stand ID
    """
    query = select(Transaction)

    # Apply filters
    if stand_id is not None:
        query = query.where(Transaction.stand_id == stand_id)

    if date_from is not None:
        query = query.where(Transaction.created_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to is not None:
        query = query.where(Transaction.created_at <= datetime.combine(date_to, datetime.max.time()))

    transactions = session.exec(query).all()

    # Calculate summaries
    total_sales = sum(t.total_amount for t in transactions)
    cash_sales = sum(t.total_amount for t in transactions if t.payment_method == PaymentMethod.CASH)
    card_sales = sum(t.total_amount for t in transactions if t.payment_method == PaymentMethod.CARD)
    transaction_count = len(transactions)

    # Group by dates
    daily_totals = {}
    for t in transactions:
        day = t.created_at.date().isoformat()
        if day not in daily_totals:
            daily_totals[day] = 0
        daily_totals[day] += t.total_amount

    return {
        "total_sales": round(total_sales, 2),
        "cash_sales": round(cash_sales, 2),
        "card_sales": round(card_sales, 2),
        "transaction_count": transaction_count,
        "daily_totals": daily_totals,
    }
