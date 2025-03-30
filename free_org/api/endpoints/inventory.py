from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from free_org.db import get_session, InventoryItem, ItemType, MenuItem, ConcessionStand
from free_org.db.models.menu_inventory import MenuItemInventory

router = APIRouter()


@router.get("/", response_model=List[InventoryItem])
async def get_all_inventory(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    stand_id: Optional[int] = None,
    item_type: Optional[ItemType] = None,
    available_only: bool = False,
):
    """
    Get all inventory items, with optional filtering.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **stand_id**: Filter by concession stand ID
    - **item_type**: Filter by item type (food, drink, supply)
    - **available_only**: If true, only return items with quantity above threshold
    """
    query = select(InventoryItem)

    # Apply filters
    if stand_id is not None:
        query = query.where(InventoryItem.stand_id == stand_id)

    if item_type is not None:
        query = query.where(InventoryItem.item_type == item_type)

    if available_only:
        query = query.where(InventoryItem.quantity > InventoryItem.minimum_threshold)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    items = session.exec(query).all()
    return items


@router.get("/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: int, session: Session = Depends(get_session)):
    """
    Get a specific inventory item by ID.

    - **item_id**: The ID of the item to retrieve
    """
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item with ID {item_id} not found")
    return item


@router.post("/", response_model=InventoryItem, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(item: InventoryItem, session: Session = Depends(get_session)):
    """
    Create a new inventory item.
    """
    # Check if stand exists if stand_id is provided
    if item.stand_id is not None:
        stand = session.get(ConcessionStand, item.stand_id)
        if not stand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {item.stand_id} not found"
            )

    # Save the new item
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{item_id}", response_model=InventoryItem)
async def update_inventory_item(item_id: int, updated_item: InventoryItem, session: Session = Depends(get_session)):
    """
    Update an existing inventory item.

    - **item_id**: The ID of the item to update
    """
    # Get the existing item
    db_item = session.get(InventoryItem, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item with ID {item_id} not found")

    # Check if stand exists if stand_id is changing
    if updated_item.stand_id is not None and updated_item.stand_id != db_item.stand_id:
        stand = session.get(ConcessionStand, updated_item.stand_id)
        if not stand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concession stand with ID {updated_item.stand_id} not found",
            )

    # Save previous quantity to check for threshold changes
    previous_available = db_item.is_available

    # Update item attributes
    item_data = updated_item.dict(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)

    # Save changes
    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    # Check if availability changed (crossed threshold)
    if previous_available != db_item.is_available:
        # Update menu items if availability changed
        await _update_menu_items_availability(session, db_item)

    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(item_id: int, session: Session = Depends(get_session)):
    """
    Delete an inventory item.

    - **item_id**: The ID of the item to delete
    """
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item with ID {item_id} not found")

    # Find and delete all links to menu items first
    links = session.exec(select(MenuItemInventory).where(MenuItemInventory.inventory_item_id == item_id)).all()

    # Remember which menu items were linked to update their availability later
    menu_item_ids = [link.menu_item_id for link in links]

    # Delete all links
    for link in links:
        session.delete(link)

    # Then delete the inventory item
    session.delete(item)
    session.commit()

    # Update availability of affected menu items
    if menu_item_ids:
        for menu_id in menu_item_ids:
            menu_item = session.get(MenuItem, menu_id)
            if menu_item:
                # Get all remaining linked inventory items
                remaining_links = session.exec(
                    select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_id)
                ).all()

                # If no more links or any linked inventory is unavailable, menu item is unavailable
                if not remaining_links:
                    menu_item.is_available = True  # No ingredients needed, so available
                else:
                    # Check if all linked inventory items are available
                    all_available = True
                    for link in remaining_links:
                        inv_item = session.get(InventoryItem, link.inventory_item_id)
                        if not inv_item or not inv_item.is_available:
                            all_available = False
                            break

                    menu_item.is_available = all_available

                session.add(menu_item)

        session.commit()

    return None


@router.put("/{item_id}/adjust", response_model=InventoryItem)
async def adjust_inventory(
    item_id: int,
    quantity_change: int = Query(..., description="Positive for additions, negative for reductions"),
    session: Session = Depends(get_session),
):
    """
    Adjust inventory quantity, either up or down.

    - **item_id**: The ID of the item to adjust
    - **quantity_change**: Amount to change (positive for additions, negative for reductions)
    """
    # Get the item
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item with ID {item_id} not found")

    # Check if there's enough quantity if reducing
    if quantity_change < 0 and abs(quantity_change) > item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough items. Have {item.quantity}, trying to remove {abs(quantity_change)}",
        )

    # Save previous status to check if threshold was crossed
    previous_available = item.is_available

    # Adjust quantity
    item.quantity += quantity_change

    # Save changes
    session.add(item)
    session.commit()
    session.refresh(item)

    # Check if availability changed (crossed threshold)
    if previous_available != item.is_available:
        # Update menu items if availability changed
        await _update_menu_items_availability(session, item)

    return item


async def _update_menu_items_availability(session: Session, item: InventoryItem):
    """
    Update menu items availability based on inventory levels.
    This ensures menu displays are automatically updated when inventory falls below threshold.

    When inventory becomes unavailable, any menu item that uses it should also be unavailable.
    When inventory becomes available, menu items using it should be checked if all their
    other required inventory items are also available.
    """
    # Find all menu items linked to this inventory item via the join table
    links = session.exec(select(MenuItemInventory).where(MenuItemInventory.inventory_item_id == item.id)).all()

    menu_item_ids = [link.menu_item_id for link in links]

    for menu_id in menu_item_ids:
        menu_item = session.get(MenuItem, menu_id)
        if menu_item:
            if not item.is_available:
                # If this inventory item is unavailable, the menu item becomes unavailable
                menu_item.is_available = False
            else:
                # If this inventory item is available, check all other linked inventory items
                # Only if ALL linked inventory items are available, the menu item is available
                all_links = session.exec(
                    select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_id)
                ).all()

                all_available = True
                for link in all_links:
                    inv_item = session.get(InventoryItem, link.inventory_item_id)
                    if not inv_item or not inv_item.is_available:
                        all_available = False
                        break

                menu_item.is_available = all_available

            session.add(menu_item)

    session.commit()
