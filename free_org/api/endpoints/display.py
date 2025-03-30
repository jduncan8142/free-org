from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from free_org.db import get_session, ConcessionStand, MenuItem

router = APIRouter()


class MenuDisplay(BaseModel):
    """Model representing the data structure for menu displays."""

    stand_name: str
    stand_location: str
    items: List[Dict[str, Any]]
    featured_items: List[Dict[str, Any]]


@router.get("/menu/{stand_id}", response_model=MenuDisplay)
async def get_menu_display(stand_id: int, session: Session = Depends(get_session)):
    """
    Get formatted menu data for display on TVs via Raspberry Pi.
    This endpoint is specifically designed for the TV display interface.

    - **stand_id**: The ID of the stand to get menu for
    """
    # Verify stand exists
    stand = session.get(ConcessionStand, stand_id)
    if not stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {stand_id} not found"
        )

    # Get all available menu items for this stand
    query = select(MenuItem).where((MenuItem.stand_id == stand_id) & (MenuItem.is_available == True))

    menu_items = session.exec(query).all()

    # Filter items that should be displayed
    displayable_items = []
    featured_items = []

    for item in menu_items:
        if item.should_display:
            # Prepare item for display
            display_item = {
                "id": item.id,
                "name": item.name,
                "price": f"${item.price:.2f}",
                "description": item.description,
                "image_path": item.image_path,
            }

            # Separate featured items
            if item.is_featured:
                featured_items.append(display_item)
            else:
                displayable_items.append(display_item)

    # Create response
    return MenuDisplay(
        stand_name=stand.name, stand_location=stand.location, items=displayable_items, featured_items=featured_items
    )


@router.get("/stands", response_model=List[Dict[str, Any]])
async def get_active_stands(session: Session = Depends(get_session)):
    """
    Get list of active concession stands for display selection on Raspberry Pi.
    """
    query = select(ConcessionStand).where(ConcessionStand.is_active == True)
    stands = session.exec(query).all()

    return [{"id": stand.id, "name": stand.name, "location": stand.location} for stand in stands]


@router.get("/health", response_model=Dict[str, str])
async def display_health_check():
    """
    Health check endpoint specifically for display systems.
    Used by Raspberry Pis to verify connection to the server.
    """
    return {"status": "online", "service": "menu-display", "version": "1.0.0"}
