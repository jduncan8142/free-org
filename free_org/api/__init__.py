"""
API package for the Concession Stand Inventory application.
"""

from fastapi import APIRouter

# Main API router
api_router = APIRouter()

# Import and include all route modules
from free_org.api.endpoints import stands, inventory, menu, transactions, display

# Include all routers
api_router.include_router(stands.router, prefix="/stands", tags=["stands"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(display.router, prefix="/display", tags=["display"])
