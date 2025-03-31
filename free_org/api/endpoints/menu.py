from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from free_org.db import get_session, MenuItem, InventoryItem, ConcessionStand
from free_org.db.models.menu_inventory import MenuItemInventory

router = APIRouter()


class InventoryItemList(BaseModel):
    inventory_item_ids: List[int]


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


@router.get("/{menu_item_id}")
async def get_menu_item(menu_item_id: int, session: Session = Depends(get_session)):
    """
    Get a specific menu item by ID, including its linked inventory items.

    - **menu_item_id**: The ID of the menu item to retrieve
    """
    item = session.get(MenuItem, menu_item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Get the inventory items for this menu item
    links = session.exec(select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_item_id)).all()
    inventory_item_ids = [link.inventory_item_id for link in links]

    inventory_items = []
    if inventory_item_ids:
        inventory_items = session.exec(select(InventoryItem).where(InventoryItem.id.in_(inventory_item_ids))).all()

    # Convert to dict for adding inventory items
    item_dict = item.model_dump()
    item_dict["inventory_items"] = [inv.model_dump() for inv in inventory_items]

    return item_dict


@router.post("/", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    menu_item: MenuItem,
    inventory_items: InventoryItemList = Body(default=None),
    session: Session = Depends(get_session),
):
    """
    Create a new menu item with linked inventory items.

    - **menu_item**: The menu item details
    - **inventory_items**: Optional list of inventory item IDs to link to the menu item
    """
    # Check if stand exists if stand_id is provided
    if menu_item.stand_id is not None:
        stand = session.get(ConcessionStand, menu_item.stand_id)
        if not stand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {menu_item.stand_id} not found"
            )

    # Save the new menu item first to get an ID
    session.add(menu_item)
    session.commit()
    session.refresh(menu_item)

    # If inventory items are provided, link them to the menu item
    if inventory_items and inventory_items.inventory_item_ids:
        for inv_id in inventory_items.inventory_item_ids:
            # Verify inventory item exists
            inventory_item = session.get(InventoryItem, inv_id)
            if not inventory_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Inventory item with ID {inv_id} not found",
                )

            # Create the link
            menu_inventory_link = MenuItemInventory(menu_item_id=menu_item.id, inventory_item_id=inv_id)
            session.add(menu_inventory_link)

        # After adding all inventory links, check availability
        # Set menu item availability based on all linked inventory items
        menu_item.is_available = all(
            session.get(InventoryItem, inv_id).is_available for inv_id in inventory_items.inventory_item_ids
        )

        session.add(menu_item)
        session.commit()
        session.refresh(menu_item)

    return menu_item


@router.put("/{menu_item_id}", response_model=MenuItem)
async def update_menu_item(
    menu_item_id: int,
    updated_item: MenuItem,
    inventory_items: InventoryItemList = Body(default=None),
    session: Session = Depends(get_session),
):
    """
    Update an existing menu item and its linked inventory items.

    - **menu_item_id**: The ID of the menu item to update
    - **updated_item**: The updated menu item details
    - **inventory_items**: Optional list of inventory item IDs to link to the menu item
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

    # Update menu item attributes (excluding relationships)
    item_data = updated_item.model_dump(exclude_unset=True, exclude={"menu_item_inventories"})
    for key, value in item_data.items():
        setattr(db_item, key, value)

    # If inventory items are provided, update the links
    if inventory_items is not None:
        # Remove existing links
        existing_links = session.exec(
            select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_item_id)
        ).all()
        for link in existing_links:
            session.delete(link)

        # Add new links
        if inventory_items.inventory_item_ids:
            for inv_id in inventory_items.inventory_item_ids:
                # Verify inventory item exists
                inventory_item = session.get(InventoryItem, inv_id)
                if not inventory_item:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Inventory item with ID {inv_id} not found",
                    )

                # Create the link
                menu_inventory_link = MenuItemInventory(menu_item_id=menu_item_id, inventory_item_id=inv_id)
                session.add(menu_inventory_link)

        # After updating inventory links, update menu item availability
        # Check all linked inventory items
        session.commit()  # Commit to ensure links are saved
        session.refresh(db_item)

        # The should_display property will check availability of all linked inventory items

    # Save changes
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{menu_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(menu_item_id: int, session: Session = Depends(get_session)):
    """
    Delete a menu item and its inventory links.

    - **menu_item_id**: The ID of the menu item to delete
    """
    item = session.get(MenuItem, menu_item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Delete all inventory links first
    links = session.exec(select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_item_id)).all()
    for link in links:
        session.delete(link)

    # Then delete the menu item
    session.delete(item)
    session.commit()
    return None


# Placing the inventory items endpoint higher in the routing hierarchy
# to ensure it's matched before potentially conflicting routes


# Specific path routes must be declared BEFORE more general path routes
# to prevent FastAPI from matching the wrong route


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
    # (is_available = True AND linked inventory items are available)
    query = select(MenuItem).where((MenuItem.stand_id == stand_id) & (MenuItem.is_available == True))

    menu_items = session.exec(query).all()

    # Filter out items where any linked inventory is below threshold
    # The should_display property checks all linked inventory items
    displayable_items = [item for item in menu_items if item.should_display]

    return displayable_items


@router.get("/{menu_item_id}/inventory_items", response_model=List[InventoryItem])
def get_menu_item_inventory_items(menu_item_id: int, session: Session = Depends(get_session)):
    """
    Get all inventory items linked to a specific menu item.

    - **menu_item_id**: The ID of the menu item
    """
    # Verify menu item exists
    menu_item = session.get(MenuItem, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Get the inventory item IDs linked to this menu item
    links = session.exec(select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_item_id)).all()

    inventory_item_ids = [link.inventory_item_id for link in links]

    # If no inventory items are linked, return an empty list
    if not inventory_item_ids:
        return []

    # Get the inventory items
    inventory_items = session.exec(select(InventoryItem).where(InventoryItem.id.in_(inventory_item_ids))).all()

    return inventory_items


@router.post("/{menu_item_id}/inventory", status_code=status.HTTP_200_OK)
async def link_inventory_items(
    menu_item_id: int, inventory_items: InventoryItemList, session: Session = Depends(get_session)
):
    """
    Link inventory items to a menu item.

    - **menu_item_id**: The ID of the menu item to link
    - **inventory_items**: List of inventory item IDs to link to the menu item
    """
    # Verify menu item exists
    menu_item = session.get(MenuItem, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Link inventory items
    for inv_id in inventory_items.inventory_item_ids:
        # Verify inventory item exists
        inventory_item = session.get(InventoryItem, inv_id)
        if not inventory_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item with ID {inv_id} not found",
            )

        # Check if link already exists
        existing_link = session.exec(
            select(MenuItemInventory).where(
                (MenuItemInventory.menu_item_id == menu_item_id) & (MenuItemInventory.inventory_item_id == inv_id)
            )
        ).first()

        if not existing_link:
            # Create the link
            menu_inventory_link = MenuItemInventory(menu_item_id=menu_item_id, inventory_item_id=inv_id)
            session.add(menu_inventory_link)

    # Commit the changes
    session.commit()

    # Refresh the menu item to update relationships
    session.refresh(menu_item)

    return {"success": True, "message": "Inventory items linked successfully"}


@router.delete("/{menu_item_id}/inventory/{inventory_item_id}", status_code=status.HTTP_200_OK)
async def unlink_inventory_item(menu_item_id: int, inventory_item_id: int, session: Session = Depends(get_session)):
    """
    Unlink an inventory item from a menu item.

    - **menu_item_id**: The ID of the menu item
    - **inventory_item_id**: The ID of the inventory item to unlink
    """
    # Verify menu item exists
    menu_item = session.get(MenuItem, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Find the link
    link = session.exec(
        select(MenuItemInventory).where(
            (MenuItemInventory.menu_item_id == menu_item_id)
            & (MenuItemInventory.inventory_item_id == inventory_item_id)
        )
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item with ID {inventory_item_id} is not linked to menu item with ID {menu_item_id}",
        )

    # Delete the link
    session.delete(link)
    session.commit()

    return {"success": True, "message": "Inventory item unlinked successfully"}


# Define query-based endpoints first to ensure they are matched before path param routes
@router.get("/_query/inventory-items-by-menu", response_model=List[InventoryItem])
def get_inventory_items_for_menu(
    menu_item_id: int = Query(..., description="The ID of the menu item"), session: Session = Depends(get_session)
):
    """
    Alternative endpoint to get all inventory items linked to a specific menu item using query parameters.
    This endpoint uses a query parameter instead of a path parameter to avoid routing conflicts.

    - **menu_item_id**: The ID of the menu item as a query parameter
    """
    # Verify menu item exists
    menu_item = session.get(MenuItem, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with ID {menu_item_id} not found")

    # Get the inventory item IDs linked to this menu item
    links = session.exec(select(MenuItemInventory).where(MenuItemInventory.menu_item_id == menu_item_id)).all()

    inventory_item_ids = [link.inventory_item_id for link in links]

    # If no inventory items are linked, return an empty list
    if not inventory_item_ids:
        return []

    # Get the inventory items
    inventory_items = session.exec(select(InventoryItem).where(InventoryItem.id.in_(inventory_item_ids))).all()

    return inventory_items
