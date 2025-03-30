import pytest
from fastapi import status


def test_get_all_menu_items(client, test_data):
    """Test retrieving all menu items."""
    response = client.get("/api/menu/")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    assert any(item["id"] == test_data["menu_item"].id for item in items)


def test_get_all_menu_items_with_filters(client, test_data):
    """Test retrieving menu items with various filters."""
    # Test stand_id filter
    stand_id = test_data["stand"].id
    response = client.get(f"/api/menu/?stand_id={stand_id}")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert all(item["stand_id"] == stand_id for item in items)

    # Test available_only filter
    response = client.get("/api/menu/?available_only=true")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert all(item["is_available"] for item in items)

    # Test featured_only filter
    response = client.get("/api/menu/?featured_only=true")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert all(item["is_featured"] for item in items)

    # Test pagination
    response = client.get("/api/menu/?skip=0&limit=5")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) <= 5


def test_get_menu_item(client, test_data):
    """Test retrieving a specific menu item by ID."""
    item_id = test_data["menu_item"].id
    response = client.get(f"/api/menu/{item_id}")
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["id"] == item_id
    assert item["name"] == test_data["menu_item"].name
    assert item["price"] == test_data["menu_item"].price
    assert item["stand_id"] == test_data["stand"].id
    assert item["inventory_item_id"] == test_data["inventory_item"].id


def test_get_menu_item_not_found(client):
    """Test retrieving a menu item that doesn't exist."""
    response = client.get("/api/menu/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_create_menu_item(client, test_data):
    """Test creating a new menu item."""
    stand_id = test_data["stand"].id
    inventory_item_id = test_data["inventory_item"].id
    menu_item_data = {
        "name": "New Test Menu Item",
        "description": "New Test Menu Description",
        "price": 15.0,
        "is_featured": True,
        "stand_id": stand_id,
        "inventory_item_id": inventory_item_id
    }
    response = client.post("/api/menu/", json=menu_item_data)
    assert response.status_code == status.HTTP_201_CREATED
    item = response.json()
    assert item["name"] == menu_item_data["name"]
    assert item["description"] == menu_item_data["description"]
    assert item["price"] == menu_item_data["price"]
    assert item["is_featured"] == menu_item_data["is_featured"]
    assert item["stand_id"] == menu_item_data["stand_id"]
    assert item["inventory_item_id"] == menu_item_data["inventory_item_id"]
    # Availability should be inherited from inventory
    assert item["is_available"] == test_data["inventory_item"].is_available


def test_create_menu_item_invalid_stand(client, test_data):
    """Test creating a menu item with an invalid stand ID."""
    inventory_item_id = test_data["inventory_item"].id
    menu_item_data = {
        "name": "New Test Menu Item",
        "description": "New Test Menu Description",
        "price": 15.0,
        "is_featured": True,
        "stand_id": 999,  # Non-existent stand ID
        "inventory_item_id": inventory_item_id
    }
    response = client.post("/api/menu/", json=menu_item_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "stand" in response.json()["detail"].lower()
    assert "not found" in response.json()["detail"].lower()


def test_create_menu_item_invalid_inventory(client, test_data):
    """Test creating a menu item with an invalid inventory item ID."""
    stand_id = test_data["stand"].id
    menu_item_data = {
        "name": "New Test Menu Item",
        "description": "New Test Menu Description",
        "price": 15.0,
        "is_featured": True,
        "stand_id": stand_id,
        "inventory_item_id": 999  # Non-existent inventory item ID
    }
    response = client.post("/api/menu/", json=menu_item_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "inventory item" in response.json()["detail"].lower()
    assert "not found" in response.json()["detail"].lower()


def test_create_menu_item_without_inventory(client, test_data):
    """Test creating a menu item without linking to inventory."""
    stand_id = test_data["stand"].id
    menu_item_data = {
        "name": "New Test Menu Item",
        "description": "New Test Menu Description",
        "price": 15.0,
        "is_featured": True,
        "stand_id": stand_id,
        "is_available": True,
        "inventory_item_id": None
    }
    response = client.post("/api/menu/", json=menu_item_data)
    assert response.status_code == status.HTTP_201_CREATED
    item = response.json()
    assert item["inventory_item_id"] is None
    assert item["is_available"] == menu_item_data["is_available"]


def test_update_menu_item(client, test_data):
    """Test updating an existing menu item."""
    item_id = test_data["menu_item"].id
    updated_data = {
        "name": "Updated Menu Item Name",
        "description": "Updated Menu Description",
        "price": 12.5,
        "is_featured": False
    }
    response = client.put(f"/api/menu/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["id"] == item_id
    assert item["name"] == updated_data["name"]
    assert item["description"] == updated_data["description"]
    assert item["price"] == updated_data["price"]
    assert item["is_featured"] == updated_data["is_featured"]


def test_update_menu_item_not_found(client):
    """Test updating a menu item that doesn't exist."""
    updated_data = {
        "name": "Updated Menu Item Name",
        "price": 12.5
    }
    response = client.put("/api/menu/999", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_update_menu_item_change_stand(client, session, test_data):
    """Test updating a menu item to change its stand."""
    # Create another stand
    from free_org.db.models.stand import ConcessionStand
    another_stand = ConcessionStand(
        name="Another Stand",
        location="Another Location"
    )
    session.add(another_stand)
    session.commit()
    
    # Update the menu item to the new stand
    item_id = test_data["menu_item"].id
    updated_data = {
        "name": "Updated Menu Item Name",
        "stand_id": another_stand.id
    }
    response = client.put(f"/api/menu/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["stand_id"] == another_stand.id
    
    # Cleanup
    session.delete(another_stand)
    session.commit()


def test_update_menu_item_invalid_stand(client, test_data):
    """Test updating a menu item with an invalid stand ID."""
    item_id = test_data["menu_item"].id
    updated_data = {
        "name": "Updated Menu Item Name",
        "stand_id": 999  # Non-existent stand ID
    }
    response = client.put(f"/api/menu/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "stand" in response.json()["detail"].lower()
    assert "not found" in response.json()["detail"].lower()


def test_update_menu_item_change_inventory(client, session, test_data):
    """Test updating a menu item to change its inventory item."""
    # Create another inventory item
    from free_org.db.models.inventory import InventoryItem, ItemType, ItemUnit
    another_inventory = InventoryItem(
        name="Another Inventory Item",
        description="Another Inventory Description",
        item_type=ItemType.FOOD,
        unit=ItemUnit.EACH,
        quantity=20,
        minimum_threshold=5,
        stand_id=test_data["stand"].id
    )
    session.add(another_inventory)
    session.commit()
    
    # Update the menu item to the new inventory item
    item_id = test_data["menu_item"].id
    updated_data = {
        "name": "Updated Menu Item Name",
        "inventory_item_id": another_inventory.id
    }
    response = client.put(f"/api/menu/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["inventory_item_id"] == another_inventory.id
    # Availability should be inherited from the new inventory
    assert item["is_available"] == another_inventory.is_available
    
    # Cleanup
    session.delete(another_inventory)
    session.commit()


def test_update_menu_item_invalid_inventory(client, test_data):
    """Test updating a menu item with an invalid inventory item ID."""
    item_id = test_data["menu_item"].id
    updated_data = {
        "name": "Updated Menu Item Name",
        "inventory_item_id": 999  # Non-existent inventory item ID
    }
    response = client.put(f"/api/menu/{item_id}", json=updated_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "inventory item" in response.json()["detail"].lower()
    assert "not found" in response.json()["detail"].lower()


def test_delete_menu_item(client, session):
    """Test deleting a menu item."""
    # Create a menu item to delete
    from free_org.db.models.menu import MenuItem
    menu_item_to_delete = MenuItem(
        name="Menu Item To Delete",
        description="Delete Menu Item Description",
        price=8.0,
        is_available=True
    )
    session.add(menu_item_to_delete)
    session.commit()
    item_id = menu_item_to_delete.id

    response = client.delete(f"/api/menu/{item_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    response = client.get(f"/api/menu/{item_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_menu_item_not_found(client):
    """Test deleting a menu item that doesn't exist."""
    response = client.delete("/api/menu/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_get_stand_menu_for_display(client, test_data):
    """Test retrieving menu items formatted for display."""
    stand_id = test_data["stand"].id
    response = client.get(f"/api/menu/stand/{stand_id}/display")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert isinstance(items, list)
    
    # All returned items should be available
    assert all(item["is_available"] for item in items)
    
    # All returned items should belong to the specified stand
    assert all(item["stand_id"] == stand_id for item in items)
    
    # If our test data item is available, it should be in the list
    if test_data["menu_item"].should_display:
        assert any(item["id"] == test_data["menu_item"].id for item in items)


def test_get_stand_menu_for_display_stand_not_found(client):
    """Test retrieving display menu for a stand that doesn't exist."""
    response = client.get("/api/menu/stand/999/display")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_get_stand_menu_for_display_with_availability(client, session, test_data):
    """Test that the display endpoint correctly filters out unavailable items."""
    stand_id = test_data["stand"].id
    menu_item = test_data["menu_item"]
    
    # Save original value for later restoration
    original_is_available = menu_item.is_available
    
    # Test with available item
    menu_item.is_available = True
    session.add(menu_item)
    session.commit()
    
    response = client.get(f"/api/menu/stand/{stand_id}/display")
    assert response.status_code == status.HTTP_200_OK
    available_items = response.json()
    available_ids = [item["id"] for item in available_items]
    assert menu_item.id in available_ids
    
    # Test with unavailable item
    menu_item.is_available = False
    session.add(menu_item)
    session.commit()
    
    response = client.get(f"/api/menu/stand/{stand_id}/display")
    assert response.status_code == status.HTTP_200_OK
    unavailable_items = response.json()
    unavailable_ids = [item["id"] for item in unavailable_items]
    assert menu_item.id not in unavailable_ids
    
    # Restore original value
    menu_item.is_available = original_is_available
    session.add(menu_item)
    session.commit()