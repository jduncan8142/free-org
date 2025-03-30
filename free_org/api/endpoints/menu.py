from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from free_org.db import get_session, MenuItem, InventoryItem, ConcessionStand

router = APIRouter()


@router.get("/", response_model=List[MenuItem])
async def get_all_menu_items(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    stand_id: Optional[int] = None,
    available_only: bool = False,
    featured_only: bool = False,
):
    """
    Get all menu items, with optional filtering.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **stand_id**: Filter by concession stand ID
    - **available_only**: If true, only return available items
    - **featured_only**: If true, only return featured items
    """
    query = select(MenuItem)

    # Apply filters
    if stand_id is not None:
        query = query.where(MenuItem.stand_id == stand_id)

    if available_only:
        query = query.where(MenuItem.is_available == True)

    if featured_only:
        query = query.where(MenuItem.is_featured == True)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    items = session.exec(query).all()
    return items


@router.get("/{menu_item_id}", response_model=MenuItem)
async def get_menu_item(menu_item_id: int, session: Session = Depends(get_session)):
    """
    Get a specific menu item by ID.

    - **menu_item_id**: The ID of the menu item to retrieve
    """
    item = session.get(MenuItem, menu_item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")
    return item


@router.post("/", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
async def create_menu_item(menu_item: MenuItem, session: Session = Depends(get_session)):
    """
    Create a new menu item.
    """
    # Check if stand exists if stand_id is provided
    if menu_item.stand_id is not None:
        stand = session.get(ConcessionStand, menu_item.stand_id)
        if not stand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {menu_item.stand_id} not found"
            )

    # Check if inventory item exists if inventory_item_id is provided
    if menu_item.inventory_item_id is not None:
        inventory_item = session.get(InventoryItem, menu_item.inventory_item_id)
        if not inventory_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item with ID {menu_item.inventory_item_id} not found",
            )

        # Set availability based on inventory availability
        menu_item.is_available = inventory_item.is_available

    # Save the new menu item
    session.add(menu_item)
    session.commit()
    session.refresh(menu_item)
    return menu_item


@router.put("/{menu_item_id}", response_model=MenuItem)
async def update_menu_item(menu_item_id: int, updated_item: MenuItem, session: Session = Depends(get_session)):
    """
    Update an existing menu item.

    - **menu_item_id**: The ID of the menu item to update
    """
    # Get the existing menu item
    db_item = session.get(MenuItem, menu_item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Check if stand exists if stand_id is changing
    if updated_item.stand_id is not None and updated_item.stand_id != db_item.stand_id:
        stand = session.get(ConcessionStand, updated_item.stand_id)
        if not stand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concession stand with ID {updated_item.stand_id} not found",
            )

    # Check if inventory item exists if inventory_item_id is changing
    if updated_item.inventory_item_id is not None and updated_item.inventory_item_id != db_item.inventory_item_id:
        inventory_item = session.get(InventoryItem, updated_item.inventory_item_id)
        if not inventory_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item with ID {updated_item.inventory_item_id} not found",
            )

        # Update availability based on new inventory item's availability
        updated_item.is_available = inventory_item.is_available

    # Update menu item attributes
    item_data = updated_item.dict(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)

    # Save changes
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{menu_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(menu_item_id: int, session: Session = Depends(get_session)):
    """
    Delete a menu item.

    - **menu_item_id**: The ID of the menu item to delete
    """
    item = session.get(MenuItem, menu_item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Delete the menu item
    session.delete(item)
    session.commit()
    return None


@router.get("/stand/{stand_id}/display", response_model=List[MenuItem])
async def get_stand_menu_for_display(stand_id: int, session: Session = Depends(get_session)):
    """
    Get all menu items for a specific stand that should be displayed on TVs.
    This endpoint is used by Raspberry Pi computers to get menu content.

    - **stand_id**: The ID of the stand to get menu items for
    """
    # Verify stand exists
    stand = session.get(ConcessionStand, stand_id)
    if not stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {stand_id} not found"
        )

    # Get all menu items for this stand that should be displayed
    # (is_available = True AND linked inventory item is available)
    query = select(MenuItem).where((MenuItem.stand_id == stand_id) & (MenuItem.is_available == True))

    menu_items = session.exec(query).all()

    # Filter out items whose linked inventory is below threshold
    # This ensures only items with sufficient inventory are displayed
    displayable_items = []
    for item in menu_items:
        # Check if linked to inventory and if so, is that inventory available
        if item.inventory_item_id is None or item.should_display:
            displayable_items.append(item)

    return displayable_items
