import pytest
from fastapi import status

from free_org.db.models.inventory import ItemType, ItemUnit


def test_get_all_stands(client, test_data):
    """Test retrieving all concession stands."""
    response = client.get("/api/stands/")
    assert response.status_code == status.HTTP_200_OK
    stands = response.json()
    assert isinstance(stands, list)
    assert len(stands) >= 1
    assert any(stand["id"] == test_data["stand"].id for stand in stands)


def test_get_all_stands_active_only(client, session, test_data):
    """Test retrieving only active stands."""
    # Create an inactive stand
    from free_org.db.models.stand import ConcessionStand
    inactive_stand = ConcessionStand(
        name="Inactive Stand",
        location="Inactive Location",
        is_active=False
    )
    session.add(inactive_stand)
    session.commit()

    # Get only active stands
    response = client.get("/api/stands/?active_only=true")
    assert response.status_code == status.HTTP_200_OK
    stands = response.json()
    assert all(stand["is_active"] for stand in stands)
    assert any(stand["id"] == test_data["stand"].id for stand in stands)
    assert not any(stand["id"] == inactive_stand.id for stand in stands)

    # Cleanup
    session.delete(inactive_stand)
    session.commit()


def test_get_stand(client, test_data):
    """Test retrieving a specific stand by ID."""
    stand_id = test_data["stand"].id
    response = client.get(f"/api/stands/{stand_id}")
    assert response.status_code == status.HTTP_200_OK
    stand = response.json()
    assert stand["id"] == stand_id
    assert stand["name"] == test_data["stand"].name
    assert stand["location"] == test_data["stand"].location


def test_get_stand_not_found(client):
    """Test retrieving a stand that doesn't exist."""
    response = client.get("/api/stands/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_create_stand(client):
    """Test creating a new stand."""
    stand_data = {
        "name": "New Test Stand",
        "location": "New Test Location",
        "description": "New Test Description",
        "is_active": True
    }
    response = client.post("/api/stands/", json=stand_data)
    assert response.status_code == status.HTTP_201_CREATED
    stand = response.json()
    assert stand["name"] == stand_data["name"]
    assert stand["location"] == stand_data["location"]
    assert stand["description"] == stand_data["description"]
    assert stand["is_active"] == stand_data["is_active"]
    assert "id" in stand


def test_update_stand(client, test_data):
    """Test updating an existing stand."""
    stand_id = test_data["stand"].id
    updated_data = {
        "name": "Updated Stand Name",
        "location": "Updated Location",
        "description": "Updated Description",
        "is_active": True
    }
    response = client.put(f"/api/stands/{stand_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    stand = response.json()
    assert stand["id"] == stand_id
    assert stand["name"] == updated_data["name"]
    assert stand["location"] == updated_data["location"]
    assert stand["description"] == updated_data["description"]


def test_update_stand_not_found(client):
    """Test updating a stand that doesn't exist."""
    updated_data = {
        "name": "Updated Stand Name",
        "location": "Updated Location",
        "description": "Updated Description",
        "is_active": True
    }
    response = client.put("/api/stands/999", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_stand(client, session):
    """Test deleting a stand."""
    # Create a stand to delete
    from free_org.db.models.stand import ConcessionStand
    stand_to_delete = ConcessionStand(
        name="Stand To Delete",
        location="Delete Location"
    )
    session.add(stand_to_delete)
    session.commit()
    stand_id = stand_to_delete.id

    response = client.delete(f"/api/stands/{stand_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    response = client.get(f"/api/stands/{stand_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_stand_not_found(client):
    """Test deleting a stand that doesn't exist."""
    response = client.delete("/api/stands/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_get_stand_inventory(client, test_data):
    """Test retrieving inventory for a specific stand."""
    stand_id = test_data["stand"].id
    response = client.get(f"/api/stands/{stand_id}/inventory")
    assert response.status_code == status.HTTP_200_OK
    inventory = response.json()
    assert isinstance(inventory, list)
    assert len(inventory) >= 1
    assert any(item["id"] == test_data["inventory_item"].id for item in inventory)


def test_get_stand_inventory_stand_not_found(client):
    """Test retrieving inventory for a stand that doesn't exist."""
    response = client.get("/api/stands/999/inventory")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_get_stand_windows(client, test_data):
    """Test retrieving windows for a specific stand."""
    stand_id = test_data["stand"].id
    response = client.get(f"/api/stands/{stand_id}/windows")
    assert response.status_code == status.HTTP_200_OK
    windows = response.json()
    assert isinstance(windows, list)
    assert len(windows) >= 1
    assert any(window["id"] == test_data["window"].id for window in windows)


def test_get_stand_windows_active_only(client, session, test_data):
    """Test retrieving only active windows for a stand."""
    stand_id = test_data["stand"].id
    
    # Create an inactive window
    from free_org.db.models.window import Window
    inactive_window = Window(
        name="Inactive Window",
        description="Inactive Window Description",
        is_active=False,
        stand_id=stand_id
    )
    session.add(inactive_window)
    session.commit()

    # Get only active windows
    response = client.get(f"/api/stands/{stand_id}/windows?active_only=true")
    assert response.status_code == status.HTTP_200_OK
    windows = response.json()
    assert all(window["is_active"] for window in windows)
    assert any(window["id"] == test_data["window"].id for window in windows)
    assert not any(window["id"] == inactive_window.id for window in windows)

    # Cleanup
    session.delete(inactive_window)
    session.commit()


def test_create_window(client, test_data):
    """Test creating a new window for a stand."""
    stand_id = test_data["stand"].id
    window_data = {
        "name": "New Test Window",
        "description": "New Test Window Description",
        "is_active": True
    }
    response = client.post(f"/api/stands/{stand_id}/windows", json=window_data)
    assert response.status_code == status.HTTP_201_CREATED
    window = response.json()
    assert window["name"] == window_data["name"]
    assert window["description"] == window_data["description"]
    assert window["is_active"] == window_data["is_active"]
    assert window["stand_id"] == stand_id


def test_create_window_stand_not_found(client):
    """Test creating a window for a stand that doesn't exist."""
    window_data = {
        "name": "New Test Window",
        "description": "New Test Window Description",
        "is_active": True
    }
    response = client.post("/api/stands/999/windows", json=window_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_update_window(client, test_data):
    """Test updating an existing window."""
    stand_id = test_data["stand"].id
    window_id = test_data["window"].id
    updated_data = {
        "name": "Updated Window Name",
        "description": "Updated Window Description",
        "is_active": False
    }
    response = client.put(f"/api/stands/{stand_id}/windows/{window_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    window = response.json()
    assert window["id"] == window_id
    assert window["name"] == updated_data["name"]
    assert window["description"] == updated_data["description"]
    assert window["is_active"] == updated_data["is_active"]
    assert window["stand_id"] == stand_id


def test_update_window_not_found(client, test_data):
    """Test updating a window that doesn't exist."""
    stand_id = test_data["stand"].id
    updated_data = {
        "name": "Updated Window Name",
        "description": "Updated Window Description",
        "is_active": False
    }
    response = client.put(f"/api/stands/{stand_id}/windows/999", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_update_window_wrong_stand(client, session, test_data):
    """Test updating a window that belongs to a different stand."""
    # Create another stand
    from free_org.db.models.stand import ConcessionStand
    another_stand = ConcessionStand(
        name="Another Stand",
        location="Another Location"
    )
    session.add(another_stand)
    session.commit()
    
    window_id = test_data["window"].id
    updated_data = {
        "name": "Updated Window Name",
        "description": "Updated Window Description",
        "is_active": False
    }
    
    # Try to update a window from the wrong stand
    response = client.put(f"/api/stands/{another_stand.id}/windows/{window_id}", json=updated_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not belong to" in response.json()["detail"].lower()
    
    # Cleanup
    session.delete(another_stand)
    session.commit()


def test_delete_window(client, session, test_data):
    """Test deleting a window."""
    stand_id = test_data["stand"].id
    
    # Create a window to delete
    from free_org.db.models.window import Window
    window_to_delete = Window(
        name="Window To Delete",
        description="Delete Window Description",
        stand_id=stand_id
    )
    session.add(window_to_delete)
    session.commit()
    window_id = window_to_delete.id

    response = client.delete(f"/api/stands/{stand_id}/windows/{window_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    response = client.get(f"/api/stands/{stand_id}/windows")
    windows = response.json()
    assert not any(window["id"] == window_id for window in windows)


def test_delete_window_not_found(client, test_data):
    """Test deleting a window that doesn't exist."""
    stand_id = test_data["stand"].id
    response = client.delete(f"/api/stands/{stand_id}/windows/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_window_wrong_stand(client, session, test_data):
    """Test deleting a window that belongs to a different stand."""
    window_id = test_data["window"].id
    
    # Create another stand
    from free_org.db.models.stand import ConcessionStand
    another_stand = ConcessionStand(
        name="Another Stand",
        location="Another Location"
    )
    session.add(another_stand)
    session.commit()
    
    # Try to delete a window from the wrong stand
    response = client.delete(f"/api/stands/{another_stand.id}/windows/{window_id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not belong to" in response.json()["detail"].lower()
    
    # Cleanup
    session.delete(another_stand)
    session.commit()


def test_transfer_inventory(client, session, test_data):
    """Test transferring inventory between stands."""
    from_stand_id = test_data["stand"].id
    item_id = test_data["inventory_item"].id
    
    # Create destination stand
    from free_org.db.models.stand import ConcessionStand
    to_stand = ConcessionStand(
        name="Destination Stand",
        location="Destination Location"
    )
    session.add(to_stand)
    session.commit()
    to_stand_id = to_stand.id
    
    # Get initial quantity
    inventory_item = test_data["inventory_item"]
    initial_quantity = inventory_item.quantity
    transfer_quantity = 10
    
    # Perform transfer
    response = client.post(
        f"/api/stands/{from_stand_id}/transfer/{to_stand_id}?item_id={item_id}&quantity={transfer_quantity}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert "successfully transferred" in response.json()["message"].lower()
    
    # Verify source inventory was reduced
    session.refresh(inventory_item)
    assert inventory_item.quantity == initial_quantity - transfer_quantity
    
    # Verify destination inventory was created
    from free_org.db.models.inventory import InventoryItem
    from sqlmodel import select
    query = select(InventoryItem).where(
        (InventoryItem.stand_id == to_stand_id) & 
        (InventoryItem.name == inventory_item.name)
    )
    dest_item = session.exec(query).first()
    assert dest_item is not None
    assert dest_item.quantity == transfer_quantity
    
    # Cleanup
    session.delete(to_stand)
    session.commit()


def test_transfer_inventory_not_enough(client, session, test_data):
    """Test transferring more inventory than available."""
    from_stand_id = test_data["stand"].id
    item_id = test_data["inventory_item"].id
    
    # Create destination stand
    from free_org.db.models.stand import ConcessionStand
    to_stand = ConcessionStand(
        name="Destination Stand",
        location="Destination Location"
    )
    session.add(to_stand)
    session.commit()
    to_stand_id = to_stand.id
    
    # Get inventory quantity and try to transfer more
    inventory_item = test_data["inventory_item"]
    too_much_quantity = inventory_item.quantity + 10
    
    # Attempt transfer
    response = client.post(
        f"/api/stands/{from_stand_id}/transfer/{to_stand_id}?item_id={item_id}&quantity={too_much_quantity}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not enough items" in response.json()["detail"].lower()
    
    # Cleanup
    session.delete(to_stand)
    session.commit()


def test_transfer_to_existing_inventory(client, session, test_data):
    """Test transferring inventory to a stand that already has the same item."""
    from_stand_id = test_data["stand"].id
    item_id = test_data["inventory_item"].id
    inventory_item = test_data["inventory_item"]
    
    # Create destination stand with same inventory item
    from free_org.db.models.stand import ConcessionStand
    from free_org.db.models.inventory import InventoryItem
    
    to_stand = ConcessionStand(
        name="Destination Stand",
        location="Destination Location"
    )
    session.add(to_stand)
    session.commit()
    to_stand_id = to_stand.id
    
    # Create matching inventory item in destination stand
    dest_item = InventoryItem(
        name=inventory_item.name,
        description=inventory_item.description,
        item_type=inventory_item.item_type,
        unit=inventory_item.unit,
        quantity=5,
        minimum_threshold=inventory_item.minimum_threshold,
        unit_cost=inventory_item.unit_cost,
        stand_id=to_stand_id
    )
    session.add(dest_item)
    session.commit()
    initial_dest_quantity = dest_item.quantity
    
    # Perform transfer
    transfer_quantity = 10
    response = client.post(
        f"/api/stands/{from_stand_id}/transfer/{to_stand_id}?item_id={item_id}&quantity={transfer_quantity}"
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Verify destination inventory was increased
    session.refresh(dest_item)
    assert dest_item.quantity == initial_dest_quantity + transfer_quantity
    
    # Cleanup
    session.delete(to_stand)
    session.commit()