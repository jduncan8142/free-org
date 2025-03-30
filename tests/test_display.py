import pytest
from fastapi import status


def test_get_menu_display(client, test_data):
    """Test retrieving formatted menu data for display on TVs."""
    stand_id = test_data["stand"].id
    response = client.get(f"/api/display/menu/{stand_id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "stand_name" in data
    assert "stand_location" in data
    assert "items" in data
    assert "featured_items" in data
    
    # Verify stand info is correct
    assert data["stand_name"] == test_data["stand"].name
    assert data["stand_location"] == test_data["stand"].location
    
    # Verify all items are displayable
    all_items = data["items"] + data["featured_items"]
    
    # If our test menu item is available and should be displayed,
    # it should be included in the response
    menu_item = test_data["menu_item"]
    if menu_item.is_available and menu_item.should_display:
        found_item = False
        for item in all_items:
            if item["id"] == menu_item.id:
                found_item = True
                assert item["name"] == menu_item.name
                assert item["price"] == f"${menu_item.price:.2f}"
                assert item["description"] == menu_item.description
                break
        assert found_item, "Menu item should be included in display data"


def test_get_menu_display_stand_not_found(client):
    """Test retrieving display menu for a stand that doesn't exist."""
    response = client.get("/api/display/menu/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_get_menu_display_with_availability(client, session, test_data):
    """Test that the display endpoint correctly handles item availability."""
    stand_id = test_data["stand"].id
    menu_item = test_data["menu_item"]
    
    # Save original value for later restoration
    original_is_available = menu_item.is_available
    
    # First test with available item
    menu_item.is_available = True
    session.add(menu_item)
    session.commit()
    
    response = client.get(f"/api/display/menu/{stand_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    all_items = data["items"] + data["featured_items"]
    item_ids = [item["id"] for item in all_items]
    assert menu_item.id in item_ids
    
    # Then test with unavailable item
    menu_item.is_available = False
    session.add(menu_item)
    session.commit()
    
    response = client.get(f"/api/display/menu/{stand_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    all_items = data["items"] + data["featured_items"]
    item_ids = [item["id"] for item in all_items]
    assert menu_item.id not in item_ids
    
    # Restore original value
    menu_item.is_available = original_is_available
    session.add(menu_item)
    session.commit()


def test_get_menu_display_featured_items(client, session, test_data):
    """Test that featured items are correctly separated in the display data."""
    stand_id = test_data["stand"].id
    menu_item = test_data["menu_item"]
    
    # Save original values for later restoration
    original_is_available = menu_item.is_available
    original_is_featured = menu_item.is_featured
    
    # Make sure the item is available and featured
    menu_item.is_available = True
    menu_item.is_featured = True
    session.add(menu_item)
    session.commit()
    
    response = client.get(f"/api/display/menu/{stand_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Item should be in featured_items
    featured_ids = [item["id"] for item in data["featured_items"]]
    regular_ids = [item["id"] for item in data["items"]]
    assert menu_item.id in featured_ids
    assert menu_item.id not in regular_ids
    
    # Now change to non-featured
    menu_item.is_featured = False
    session.add(menu_item)
    session.commit()
    
    response = client.get(f"/api/display/menu/{stand_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Item should be in regular items
    featured_ids = [item["id"] for item in data["featured_items"]]
    regular_ids = [item["id"] for item in data["items"]]
    assert menu_item.id not in featured_ids
    assert menu_item.id in regular_ids
    
    # Restore original values
    menu_item.is_available = original_is_available
    menu_item.is_featured = original_is_featured
    session.add(menu_item)
    session.commit()


def test_get_active_stands(client, session, test_data):
    """Test retrieving active stands for display selection."""
    response = client.get("/api/display/stands")
    assert response.status_code == status.HTTP_200_OK
    
    stands = response.json()
    assert isinstance(stands, list)
    
    # All stands should be active
    assert all("id" in stand and "name" in stand and "location" in stand for stand in stands)
    
    # Our test stand should be included if it's active
    if test_data["stand"].is_active:
        stand_ids = [stand["id"] for stand in stands]
        assert test_data["stand"].id in stand_ids


def test_get_active_stands_filters_inactive(client, session, test_data):
    """Test that inactive stands are filtered out."""
    # Create an inactive stand
    from free_org.db.models.stand import ConcessionStand
    inactive_stand = ConcessionStand(
        name="Inactive Stand",
        location="Inactive Location",
        is_active=False
    )
    session.add(inactive_stand)
    session.commit()
    
    response = client.get("/api/display/stands")
    assert response.status_code == status.HTTP_200_OK
    
    stands = response.json()
    stand_ids = [stand["id"] for stand in stands]
    assert inactive_stand.id not in stand_ids
    
    # Cleanup
    session.delete(inactive_stand)
    session.commit()


def test_display_health_check(client):
    """Test the display health check endpoint."""
    response = client.get("/api/display/health")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "online"
    assert "service" in data
    assert data["service"] == "menu-display"
    assert "version" in data