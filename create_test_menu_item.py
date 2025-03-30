import requests
import json

# Create a new menu item with linked inventory items
url = "http://localhost:8000/api/menu/"
headers = {"Content-Type": "application/json"}
data = {
    "name": "Cheeseburger Combo",
    "price": 9.50,
    "description": "Burger with cheese and side items",
    "stand_id": 1,
    "is_available": True,
    "is_featured": True,
    "inventory_item_ids": [1, 2]  # Link to burger patty and bun
}

response = requests.post(url, headers=headers, json=data)
print(f"Status code: {response.status_code}")
try:
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error parsing response: {e}")
    print(f"Raw response: {response.text}")