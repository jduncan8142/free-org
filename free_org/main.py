import os
import sys
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
from sqlmodel import Session, select

# Add the parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import application components
from free_org.db import init_db, get_session, ConcessionStand, MenuItem
from free_org.api import api_router

# Create FastAPI app instance
app = FastAPI(
    title="Concession Stand Inventory",
    description="Inventory tracking system for parent organization concession stands",
    version="0.1.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory path (free_org)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Create directories if they don't exist
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files for web UI
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up Jinja2 templates for web UI
templates = Jinja2Templates(directory=templates_dir)

# Include the API router
app.include_router(api_router, prefix="/api")


# Database initialization event
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web application interface."""
    return templates.TemplateResponse("index.html", {"request": request, "title": "Concession Stand Inventory"})


@app.get("/stands", response_class=HTMLResponse)
async def stands_page(request: Request):
    """Serve the stands management page."""
    return templates.TemplateResponse(
        "stands.html",
        {"request": request, "title": "Manage Concession Stands"},
    )


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    """Serve the inventory management page."""
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "title": "Manage Inventory"},
    )


@app.get("/transfers", response_class=HTMLResponse)
async def transfers_page(request: Request):
    """Serve the inventory transfer page."""
    return templates.TemplateResponse(
        "transfers.html",
        {"request": request, "title": "Transfer Inventory"},
    )


@app.get("/inventory/add", response_class=HTMLResponse)
async def add_inventory_page(request: Request):
    """Serve the add inventory item page."""
    return templates.TemplateResponse(
        "inventory_add.html",
        {"request": request, "title": "Inventory Management"},
    )


@app.get("/menu", response_class=HTMLResponse)
async def menu_page(request: Request):
    """Serve the menu management page."""
    return templates.TemplateResponse(
        "menu.html",
        {"request": request, "title": "Manage Menu Items"},
    )


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    """Serve the transactions page."""
    return templates.TemplateResponse(
        "transactions.html",
        {"request": request, "title": "View Transactions"},
    )


@app.get("/displays", response_class=HTMLResponse)
async def displays_management_page(request: Request):
    """Serve the display management page."""
    return templates.TemplateResponse(
        "displays.html",
        {"request": request, "title": "Manage TV Displays"},
    )


@app.get("/pos", response_class=HTMLResponse)
async def pos_page(request: Request):
    """Serve the point of sale page for multiple-item transactions."""
    return templates.TemplateResponse(
        "pos.html",
        {"request": request, "title": "Point of Sale"},
    )


@app.get("/display/{stand_id}", response_class=HTMLResponse)
async def tv_display(request: Request, stand_id: int, session: Session = Depends(get_session)):
    """
    Serve the TV display for a specific stand.
    This endpoint is used by Raspberry Pi computers to display menus.

    - **stand_id**: The ID of the stand to display menu for
    """
    # Get stand info
    stand = session.get(ConcessionStand, stand_id)
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")

    # Get menu items for this stand that should be displayed
    query = select(MenuItem).where((MenuItem.stand_id == stand_id) & (MenuItem.is_available == True))

    menu_items = session.exec(query).all()

    # Filter displayable and featured items
    items = []
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
                items.append(display_item)

    # Render the display template
    return templates.TemplateResponse(
        "display.html",
        {
            "request": request,
            "stand_id": stand_id,
            "stand_name": stand.name,
            "stand_location": stand.location,
            "items": items,
            "featured_items": featured_items,
            "current_time": datetime.now().strftime("%I:%M:%S %p"),
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "online", "message": "Concession Stand Inventory system is running"}


if __name__ == "__main__":
    uvicorn.run("free_org.main:app", host="0.0.0.0", port=8000, reload=True)
