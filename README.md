# FREE ORG - Concessions Stand Inventory Management System

Free Org is a Python 3.13 application for managing concession stand processes and inventory. The system helps staff and volunteers manage inventory across multiple stands, track sales, and automatically update digital signage and menu displays.

## Features

- **Inventory Management:** Track food, drinks, and supplies across multiple concession stands.
- **Multiple Stands Support:** Manage multiple concession stands each with their own inventory.
- **Menu Displays:** Automatically update digital signage and menus in real time as inventory changes.
- **Sales Tracking:** Record transactions with both cash and Square credit card payments
- **Responsive Web UI:** Works on smartphones, tablets, and desktop computers
- **Inventory Transfer:** Easily move inventory between stands when needed

## Technology Stack

- **Backend:** Python 3.13 + FastAPI
- **Database:** SQLite with SQLModel (SQLAlchemy + Pydantic)
- **Frontend:** Bootstrap 5, jQuery, JavaScript
- **Display System:** Raspberry Pi computers connected to TVs

## Setup Instructions

### Prerequisites

- Python 3.13
- Pipenv (for dependency management)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/concession-stand-inventory.git
   cd concession-stand-inventory
   ```

2. Install dependencies:

   ```bash
   pipenv install
   ```

3. Activate the virtual environment:

   ```bash
   pipenv shell
   ```

4. Run the application:

   ```bash
   cd free_org
   python main.py
   ```

5. Access the web interface:
   - Main dashboard: http://localhost:8000/
   - API documentation: http://localhost:8000/docs

## TV Display Setup (for Raspberry Pi)

1. Install a modern web browser on your Raspberry Pi
2. Configure the browser to launch in kiosk mode (fullscreen)
3. Point the browser to: `http://[server-ip]:8000/display/[stand-id]`
4. The display will automatically update when inventory changes

## API Documentation

The API is self-documented using Swagger UI, available at `/docs` endpoint when the server is running.

Key endpoints:

- `/api/stands` - Manage concession stands
- `/api/inventory` - Track and update inventory items
- `/api/menu` - Manage menu items displayed on TVs
- `/api/transactions` - Record and retrieve sales data
- `/api/display` - Specialized endpoints for TV displays

## Development

To run the application in development mode:

```bash
cd free_org
python main.py
```

The server will reload automatically when code changes are detected.

## License

[MIT License](LICENSE)
