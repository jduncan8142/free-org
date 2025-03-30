import os
import sys
import pytest
from typing import Generator, List, Dict, Any
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

# Add the parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from free_org.db.models import (
    ConcessionStand, 
    InventoryItem, 
    ItemType, 
    ItemUnit, 
    MenuItem, 
    Transaction, 
    PaymentMethod, 
    Window
)
from free_org.api import api_router
from free_org.db import get_session


@pytest.fixture(name="engine")
def engine_fixture():
    """Create a SQLite in-memory database engine for tests."""
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Use static pool for in-memory database
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create a new database session for a test."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    """Create a FastAPI TestClient with a database session."""
    def get_session_override():
        """Override the get_session dependency."""
        return session

    app = FastAPI()
    app.include_router(api_router, prefix="/api")
    app.dependency_overrides[get_session] = get_session_override
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(name="test_stand")
def test_stand_fixture(session):
    """Create a test concession stand."""
    stand = ConcessionStand(
        name="Test Stand",
        location="Test Location",
        description="Test Description",
        is_active=True
    )
    session.add(stand)
    session.commit()
    session.refresh(stand)
    return stand


@pytest.fixture(name="test_window")
def test_window_fixture(session, test_stand):
    """Create a test window for a stand."""
    window = Window(
        name="Test Window",
        description="Test Window Description",
        is_active=True,
        stand_id=test_stand.id
    )
    session.add(window)
    session.commit()
    session.refresh(window)
    return window


@pytest.fixture(name="test_inventory_item")
def test_inventory_item_fixture(session, test_stand):
    """Create a test inventory item."""
    item = InventoryItem(
        name="Test Inventory Item",
        description="Test Inventory Description",
        item_type=ItemType.FOOD,
        unit=ItemUnit.EACH,
        quantity=100,
        minimum_threshold=10,
        unit_cost=5.0,
        stand_id=test_stand.id
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@pytest.fixture(name="test_menu_item")
def test_menu_item_fixture(session, test_stand, test_inventory_item):
    """Create a test menu item."""
    menu_item = MenuItem(
        name="Test Menu Item",
        description="Test Menu Description",
        price=10.0,
        is_available=True,
        is_featured=True,
        stand_id=test_stand.id,
        inventory_item_id=test_inventory_item.id
    )
    session.add(menu_item)
    session.commit()
    session.refresh(menu_item)
    return menu_item


@pytest.fixture(name="test_transaction")
def test_transaction_fixture(session, test_stand, test_menu_item, test_window):
    """Create a test transaction."""
    transaction = Transaction(
        menu_item_id=test_menu_item.id,
        stand_id=test_stand.id,
        window_id=test_window.id,
        quantity=2,
        unit_price=test_menu_item.price,
        total_amount=test_menu_item.price * 2,
        payment_method=PaymentMethod.CASH
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


@pytest.fixture(name="test_data")
def test_data_fixture(test_stand, test_window, test_inventory_item, test_menu_item, test_transaction):
    """Return all test data fixtures in a dictionary."""
    return {
        "stand": test_stand,
        "window": test_window,
        "inventory_item": test_inventory_item,
        "menu_item": test_menu_item,
        "transaction": test_transaction
    }