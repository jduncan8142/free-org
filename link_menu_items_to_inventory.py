import requests
import json

# Function to fetch inventory items
def get_inventory_items():
    response = requests.get("http://localhost:8000/api/inventory")
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Function to fetch menu items
def get_menu_items():
    response = requests.get("http://localhost:8000/api/menu")
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Main script
if __name__ == "__main__":
    # Fetch existing inventory and menu items
    print("Fetching existing inventory items...")
    inventory_items = get_inventory_items()
    print(f"Found {len(inventory_items)} inventory items")
    for item in inventory_items:
        print(f"ID: {item['id']}, Name: {item['name']}")

    print("Fetching existing menu items...")
    menu_items = get_menu_items()
    print(f"Found {len(menu_items)} menu items")
    for item in menu_items:
        print(f"ID: {item['id']}, Name: {item['name']}")

    # Use the first menu item and first two inventory items for demonstration
    menu_item_id = 1  # Example menu item ID
    if menu_items and len(menu_items) > 0:
        menu_item_id = menu_items[0]["id"]
        print(f"Using menu item ID {menu_item_id} ({menu_items[0]['name']})")

    inventory_item_ids = []
    if inventory_items and len(inventory_items) >= 2:
        inventory_item_ids = [inventory_items[0]["id"], inventory_items[1]["id"]]
        print(f"Using inventory item IDs: {inventory_item_ids}")

    # Link inventory items to menu item
    if menu_item_id and inventory_item_ids:
        # Get the current menu item to update
        response = requests.get(f"http://localhost:8000/api/menu/{menu_item_id}")
        if response.status_code != 200:
            print(f"Error getting menu item: {response.text}")
            exit(1)
        
        menu_item = response.json()
        
        # Prepare the update payload - Keep all existing fields
        update_data = {
            "id": menu_item["id"],
            "name": menu_item["name"],
            "price": menu_item["price"],
            "description": menu_item.get("description", ""),
            "is_available": menu_item.get("is_available", True),
            "is_featured": menu_item.get("is_featured", False),
            "stand_id": menu_item.get("stand_id"),
            "image_path": menu_item.get("image_path")
        }
        
        # Include inventory_items in the request body
        inventory_data = {
            "inventory_item_ids": inventory_item_ids
        }
        
        print(f"Updating menu item {menu_item_id} with inventory items {inventory_item_ids}...")
        
        # Make the PUT request with both objects
        response = requests.put(
            f"http://localhost:8000/api/menu/{menu_item_id}", 
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Make a separate request to link inventory items
        inv_response = requests.put(
            f"http://localhost:8000/api/menu/{menu_item_id}", 
            data=json.dumps(inventory_data),
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Menu update status code: {response.status_code}")
        print(f"Inventory update status code: {inv_response.status_code}")
        
        try:
            print(f"Menu update response: {response.json()}")
            print(f"Inventory update response: {inv_response.json()}")
        except json.JSONDecodeError:
            print(f"Error parsing response: {response.text}")
            print(f"Error parsing inventory response: {inv_response.text}")

    # Verify the menu item now has linked inventory items
    print(f"Verifying menu item {menu_item_id} has linked inventory items...")
    response = requests.get(f"http://localhost:8000/api/menu/{menu_item_id}")
    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        item = response.json()
        print(f"Menu item details: {json.dumps(item, indent=2)}")
        
        if "inventory_items" in item:
            print(f"Found {len(item['inventory_items'])} linked inventory items:")
            for inv_item in item["inventory_items"]:
                print(f"ID: {inv_item['id']}, Name: {inv_item['name']}")
        else:
            print("No inventory_items field found in the response.")

    print("Done!")