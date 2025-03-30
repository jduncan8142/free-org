import pytest
from fastapi import status

from free_org.db.models.inventory import ItemType, ItemUnit


def test_get_all_inventory(client, test_data):
    """Test retrieving all inventory items."""
    response = client.get("/api/inventory/")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    assert any(item["id"] == test_data["inventory_item"].id for item in items)


def test_get_all_inventory_with_filters(client, test_data):
    """Test retrieving inventory items with various filters."""
    # Test stand_id filter
    stand_id = test_data["stand"].id
    response = client.get(f"/api/inventory/?stand_id={stand_id}")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert all(item["stand_id"] == stand_id for item in items)

    # Test item_type filter
    response = client.get(f"/api/inventory/?item_type={ItemType.FOOD}")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert all(item["item_type"] == ItemType.FOOD for item in items)

    # Test available_only filter
    response = client.get("/api/inventory/?available_only=true")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert all(item["quantity"] > item["minimum_threshold"] for item in items)

    # Test pagination
    response = client.get("/api/inventory/?skip=0&limit=5")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) <= 5


def test_get_inventory_item(client, test_data):
    """Test retrieving a specific inventory item by ID."""
    item_id = test_data["inventory_item"].id
    response = client.get(f"/api/inventory/{item_id}")
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["id"] == item_id
    assert item["name"] == test_data["inventory_item"].name
    assert item["item_type"] == test_data["inventory_item"].item_type
    assert item["unit"] == test_data["inventory_item"].unit
    assert item["quantity"] == test_data["inventory_item"].quantity


def test_get_inventory_item_not_found(client):
    """Test retrieving an inventory item that doesn't exist."""
    response = client.get("/api/inventory/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_create_inventory_item(client, test_data):
    """Test creating a new inventory item."""
    stand_id = test_data["stand"].id
    item_data = {
        "name": "New Test Item",
        "description": "New Test Description",
        "item_type": ItemType.FOOD,
        "unit": ItemUnit.EACH,
        "quantity": 50,
        "minimum_threshold": 10,
        "unit_cost": 2.5,
        "stand_id": stand_id
    }
    response = client.post("/api/inventory/", json=item_data)
    assert response.status_code == status.HTTP_201_CREATED
    item = response.json()
    assert item["name"] == item_data["name"]
    assert item["description"] == item_data["description"]
    assert item["item_type"] == item_data["item_type"]
    assert item["unit"] == item_data["unit"]
    assert item["quantity"] == item_data["quantity"]
    assert item["minimum_threshold"] == item_data["minimum_threshold"]
    assert item["unit_cost"] == item_data["unit_cost"]
    assert item["stand_id"] == item_data["stand_id"]


def test_create_inventory_item_invalid_stand(client):
    """Test creating an inventory item with an invalid stand ID."""
    item_data = {
        "name": "New Test Item",
        "description": "New Test Description",
        "item_type": ItemType.FOOD,
        "unit": ItemUnit.EACH,
        "quantity": 50,
        "minimum_threshold": 10,
        "unit_cost": 2.5,
        "stand_id": 999  # Non-existent stand ID
    }
    response = client.post("/api/inventory/", json=item_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "stand" in response.json()["detail"].lower()
    assert "not found" in response.json()["detail"].lower()


def test_update_inventory_item(client, test_data):
    """Test updating an existing inventory item."""
    item_id = test_data["inventory_item"].id
    updated_data = {
        "name": "Updated Item Name",
        "description": "Updated Description",
        "quantity": 75,
        "minimum_threshold": 15,
        "unit_cost": 3.5
    }
    response = client.put(f"/api/inventory/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["id"] == item_id
    assert item["name"] == updated_data["name"]
    assert item["description"] == updated_data["description"]
    assert item["quantity"] == updated_data["quantity"]
    assert item["minimum_threshold"] == updated_data["minimum_threshold"]
    assert item["unit_cost"] == updated_data["unit_cost"]


def test_update_inventory_item_not_found(client):
    """Test updating an inventory item that doesn't exist."""
    updated_data = {
        "name": "Updated Item Name",
        "description": "Updated Description",
        "quantity": 75
    }
    response = client.put("/api/inventory/999", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_update_inventory_item_change_stand(client, session, test_data):
    """Test updating an inventory item to change its stand."""
    # Create another stand
    from free_org.db.models.stand import ConcessionStand
    another_stand = ConcessionStand(
        name="Another Stand",
        location="Another Location"
    )
    session.add(another_stand)
    session.commit()
    
    # Update the inventory item to the new stand
    item_id = test_data["inventory_item"].id
    updated_data = {
        "name": "Updated Item Name",
        "stand_id": another_stand.id
    }
    response = client.put(f"/api/inventory/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["stand_id"] == another_stand.id
    
    # Cleanup
    session.delete(another_stand)
    session.commit()


def test_update_inventory_item_invalid_stand(client, test_data):
    """Test updating an inventory item with an invalid stand ID."""
    item_id = test_data["inventory_item"].id
    updated_data = {
        "name": "Updated Item Name",
        "stand_id": 999  # Non-existent stand ID
    }
    response = client.put(f"/api/inventory/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "stand" in response.json()["detail"].lower()
    assert "not found" in response.json()["detail"].lower()


def test_update_inventory_cross_threshold(client, session, test_data):
    """Test updating inventory quantity to cross the availability threshold."""
    # Get the item and set its quantity just above threshold
    item = test_data["inventory_item"]
    menu_item = test_data["menu_item"]
    
    # Save original values for later restoration
    original_quantity = item.quantity
    original_menu_available = menu_item.is_available
    
    # Set item barely above threshold
    item.quantity = item.minimum_threshold + 1
    session.add(item)
    session.commit()
    
    # Set menu item to available
    menu_item.is_available = True
    session.add(menu_item)
    session.commit()
    
    # Update to cross below threshold
    updated_data = {
        "quantity": item.minimum_threshold - 1
    }
    response = client.put(f"/api/inventory/{item.id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that item is now unavailable
    session.refresh(item)
    assert item.quantity < item.minimum_threshold
    assert not item.is_available
    
    # Check that menu item is now unavailable
    session.refresh(menu_item)
    assert not menu_item.is_available
    
    # Restore original values
    item.quantity = original_quantity
    menu_item.is_available = original_menu_available
    session.add(item)
    session.add(menu_item)
    session.commit()


def test_delete_inventory_item(client, session):
    """Test deleting an inventory item."""
    # Create an item to delete
    from free_org.db.models.inventory import InventoryItem
    item_to_delete = InventoryItem(
        name="Item To Delete",
        description="Delete Item Description",
        item_type=ItemType.SUPPLY,
        unit=ItemUnit.EACH,
        quantity=10
    )
    session.add(item_to_delete)
    session.commit()
    item_id = item_to_delete.id

    response = client.delete(f"/api/inventory/{item_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    response = client.get(f"/api/inventory/{item_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_inventory_item_not_found(client):
    """Test deleting an inventory item that doesn't exist."""
    response = client.delete("/api/inventory/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_adjust_inventory(client, session, test_data):
    """Test adjusting inventory quantity up and down."""
    item_id = test_data["inventory_item"].id
    item = test_data["inventory_item"]
    
    # Save original value for later restoration
    original_quantity = item.quantity
    
    # Increase quantity
    increase_amount = 10
    response = client.put(f"/api/inventory/{item_id}/adjust?quantity_change={increase_amount}")
    assert response.status_code == status.HTTP_200_OK
    session.refresh(item)
    assert item.quantity == original_quantity + increase_amount
    
    # Decrease quantity
    decrease_amount = -5
    response = client.put(f"/api/inventory/{item_id}/adjust?quantity_change={decrease_amount}")
    assert response.status_code == status.HTTP_200_OK
    session.refresh(item)
    assert item.quantity == original_quantity + increase_amount + decrease_amount
    
    # Restore original value
    item.quantity = original_quantity
    session.add(item)
    session.commit()


def test_adjust_inventory_not_enough(client, session, test_data):
    """Test adjusting inventory with a reduction larger than the current quantity."""
    item_id = test_data["inventory_item"].id
    item = test_data["inventory_item"]
    
    # Try to decrease more than available
    too_much_decrease = -(item.quantity + 10)
    response = client.put(f"/api/inventory/{item_id}/adjust?quantity_change={too_much_decrease}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not enough" in response.json()["detail"].lower()


def test_adjust_inventory_cross_threshold(client, session, test_data):
    """Test adjusting inventory to cross the availability threshold."""
    item = test_data["inventory_item"]
    menu_item = test_data["menu_item"]
    
    # Save original values for later restoration
    original_quantity = item.quantity
    original_menu_available = menu_item.is_available
    
    # Set item barely above threshold
    item.quantity = item.minimum_threshold + 2
    session.add(item)
    session.commit()
    
    # Set menu item to available
    menu_item.is_available = True
    session.add(menu_item)
    session.commit()
    
    # Adjust to cross below threshold
    decrease_amount = -3  # This should bring it below threshold
    response = client.put(f"/api/inventory/{item.id}/adjust?quantity_change={decrease_amount}")
    assert response.status_code == status.HTTP_200_OK
    
    # Check that item is now unavailable
    session.refresh(item)
    assert item.quantity < item.minimum_threshold
    assert not item.is_available
    
    # Check that menu item is now unavailable
    session.refresh(menu_item)
    assert not menu_item.is_available
    
    # Restore original values
    item.quantity = original_quantity
    menu_item.is_available = original_menu_available
    session.add(item)
    session.add(menu_item)
    session.commit()