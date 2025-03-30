from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from free_org.db import get_session, ConcessionStand, InventoryItem

router = APIRouter()


@router.get("/", response_model=List[ConcessionStand])
async def get_all_stands(
    session: Session = Depends(get_session), skip: int = 0, limit: int = 100, active_only: bool = False
):
    """
    Get all concession stands.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **active_only**: If true, only return active stands
    """
    query = select(ConcessionStand)

    if active_only:
        query = query.where(ConcessionStand.is_active == True)

    query = query.offset(skip).limit(limit)
    stands = session.exec(query).all()
    return stands


@router.get("/{stand_id}", response_model=ConcessionStand)
async def get_stand(stand_id: int, session: Session = Depends(get_session)):
    """
    Get a specific concession stand by ID.

    - **stand_id**: The ID of the stand to retrieve
    """
    stand = session.get(ConcessionStand, stand_id)
    if not stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {stand_id} not found"
        )
    return stand


@router.post("/", response_model=ConcessionStand, status_code=status.HTTP_201_CREATED)
async def create_stand(stand: ConcessionStand, session: Session = Depends(get_session)):
    """
    Create a new concession stand.
    """
    # Save the new stand
    session.add(stand)
    session.commit()
    session.refresh(stand)
    return stand


@router.put("/{stand_id}", response_model=ConcessionStand)
async def update_stand(stand_id: int, updated_stand: ConcessionStand, session: Session = Depends(get_session)):
    """
    Update an existing concession stand.

    - **stand_id**: The ID of the stand to update
    """
    # Get the existing stand
    db_stand = session.get(ConcessionStand, stand_id)
    if not db_stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {stand_id} not found"
        )

    # Update stand attributes
    stand_data = updated_stand.dict(exclude_unset=True)
    for key, value in stand_data.items():
        setattr(db_stand, key, value)

    # Save changes
    session.add(db_stand)
    session.commit()
    session.refresh(db_stand)
    return db_stand


@router.delete("/{stand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stand(stand_id: int, session: Session = Depends(get_session)):
    """
    Delete a concession stand.

    - **stand_id**: The ID of the stand to delete
    """
    stand = session.get(ConcessionStand, stand_id)
    if not stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {stand_id} not found"
        )

    # Delete the stand
    session.delete(stand)
    session.commit()
    return None


@router.get("/{stand_id}/inventory", response_model=List[InventoryItem])
async def get_stand_inventory(stand_id: int, session: Session = Depends(get_session)):
    """
    Get inventory for a specific stand.

    - **stand_id**: The ID of the stand
    """
    # Verify stand exists
    stand = session.get(ConcessionStand, stand_id)
    if not stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Concession stand with ID {stand_id} not found"
        )

    # Get inventory for this stand
    query = select(InventoryItem).where(InventoryItem.stand_id == stand_id)
    inventory = session.exec(query).all()
    return inventory


@router.post("/{from_stand_id}/transfer/{to_stand_id}")
async def transfer_inventory(
    from_stand_id: int, to_stand_id: int, item_id: int, quantity: int, session: Session = Depends(get_session)
):
    """
    Transfer inventory from one stand to another.

    - **from_stand_id**: Source stand ID
    - **to_stand_id**: Destination stand ID
    - **item_id**: ID of the inventory item to transfer
    - **quantity**: Quantity to transfer
    """
    # Verify both stands exist
    from_stand = session.get(ConcessionStand, from_stand_id)
    if not from_stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Source stand with ID {from_stand_id} not found"
        )

    to_stand = session.get(ConcessionStand, to_stand_id)
    if not to_stand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Destination stand with ID {to_stand_id} not found"
        )

    # Get the item to transfer
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item with ID {item_id} not found")

    # Ensure item belongs to source stand
    if item.stand_id != from_stand_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item does not belong to source stand")

    # Ensure enough quantity to transfer
    if item.quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough items to transfer. Have {item.quantity}, need {quantity}",
        )

    # Check if destination stand already has this item
    dest_item_query = select(InventoryItem).where(
        (InventoryItem.stand_id == to_stand_id)
        & (InventoryItem.name == item.name)
        & (InventoryItem.item_type == item.item_type)
    )
    dest_item = session.exec(dest_item_query).first()

    # Transfer the inventory
    item.quantity -= quantity

    if dest_item:
        # Update existing item in destination stand
        dest_item.quantity += quantity
        session.add(dest_item)
    else:
        # Create new item in destination stand
        new_item = InventoryItem(
            name=item.name,
            description=item.description,
            item_type=item.item_type,
            unit=item.unit,
            quantity=quantity,
            minimum_threshold=item.minimum_threshold,
            unit_cost=item.unit_cost,
            stand_id=to_stand_id,
        )
        session.add(new_item)

    session.add(item)
    session.commit()

    return {
        "message": f"Successfully transferred {quantity} of {item.name} from stand {from_stand_id} to stand {to_stand_id}"
    }
