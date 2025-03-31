import requests
import json

# First, get existing inventory items to ensure we have valid IDs
print("Fetching existing inventory items...")
inventory_response = requests.get("http://localhost:8000/api/inventory/")
inventory_items = inventory_response.json()

if not inventory_items:
    print("No inventory items found. Please create some inventory items first.")
    exit(1)

print(f"Found {len(inventory_items)} inventory items")
for item in inventory_items:
    print(f"ID: {item['id']}, Name: {item['name']}")

# Get existing menu items
print("\nFetching existing menu items...")
menu_response = requests.get("http://localhost:8000/api/menu/")
menu_items = menu_response.json()

if not menu_items:
    print("No menu items found. Please create some menu items first.")
    exit(1)

print(f"Found {len(menu_items)} menu items")
for item in menu_items:
    print(f"ID: {item['id']}, Name: {item['name']}")

# Prompt user to select a menu item to link (in this example we'll just use the first one)
menu_item_id = menu_items[0]["id"]
print(f"\nUsing menu item ID {menu_item_id} ({menu_items[0]['name']})")

# Prompt user to select inventory items to link (in this example we'll use first two if available)
inventory_item_ids = [item["id"] for item in inventory_items[:2]]
print(f"Using inventory item IDs: {inventory_item_ids}")

# Get the current menu item details to update
item_url = f"http://localhost:8000/api/menu/{menu_item_id}"
menu_item_response = requests.get(item_url)
menu_item_data = menu_item_response.json()

# Prepare the update data - keep all existing fields but add inventory_item_ids
update_data = menu_item_data.copy()
# Add inventory_item_ids field directly in the update_data
update_data["inventory_item_ids"] = inventory_item_ids

# Link the inventory items to the menu item using PUT endpoint
link_url = f"http://localhost:8000/api/menu/{menu_item_id}"
headers = {"Content-Type": "application/json"}

print(f"\nLinking inventory items {inventory_item_ids} to menu item {menu_item_id}...")
link_response = requests.put(link_url, headers=headers, json=update_data)
print(f"Status code: {link_response.status_code}")
try:
    print(f"Response: {link_response.json()}")
except Exception as e:
    print(f"Error parsing response: {e}")
    print(f"Raw response: {link_response.text}")

# Verify the link by fetching the menu item details
verify_url = f"http://localhost:8000/api/menu/{menu_item_id}"
verify_response = requests.get(verify_url)
print(f"\nVerifying menu item {menu_item_id} has linked inventory items...")
print(f"Status code: {verify_response.status_code}")
try:
    menu_item_details = verify_response.json()
    print(f"Menu item details: {json.dumps(menu_item_details, indent=2)}")

    # Check for inventory_items in the response
    if "inventory_items" in menu_item_details:
        inventory_items = menu_item_details["inventory_items"]
        print(f"Linked inventory items: {len(inventory_items)}")
        for item in inventory_items:
            print(f"  - ID: {item['id']}, Name: {item['name']}")
    else:
        print("No inventory_items field found in the response.")
except Exception as e:
    print(f"Error parsing response: {e}")
    print(f"Raw response: {verify_response.text}")

print("\nDone!")
