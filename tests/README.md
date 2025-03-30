# API Testing for Free-Org

This directory contains automated tests for all the API endpoints in the Free-Org application.

## Test Structure

The tests are organized by API endpoint:

- `test_transactions.py` - Tests for transaction API endpoints
- `test_stands.py` - Tests for concession stands and windows API endpoints
- `test_inventory.py` - Tests for inventory management API endpoints
- `test_menu.py` - Tests for menu items API endpoints
- `test_display.py` - Tests for display/TV menu API endpoints

Each test file follows the same pattern:
- Tests for retrieving data (GET endpoints)
- Tests for creating data (POST endpoints)
- Tests for updating data (PUT endpoints)
- Tests for deleting data (DELETE endpoints)
- Tests for specialized endpoints (e.g., inventory adjustments, inventory transfers)
- Tests for error handling and validation

## Test Environment

The tests use pytest with FastAPI's TestClient and an in-memory SQLite database:

- `conftest.py` contains shared fixtures including:
  - Database setup with in-memory SQLite
  - Test data fixtures for stands, windows, inventory, menu items, and transactions
  - FastAPI TestClient setup with dependency overrides

All tests run in isolation with a fresh database for each test, ensuring tests don't interfere with each other.

## Running the Tests

To run all tests:

```bash
pytest
```

To run tests for a specific API:

```bash
pytest tests/test_transactions.py
```

To run a specific test:

```bash
pytest tests/test_transactions.py::test_create_transaction
```

To run tests with verbose output:

```bash
pytest -v
```

## Test Coverage

The tests cover:

1. **Basic CRUD Operations**
   - Create, read, update, and delete for all resources
   - Filtering and pagination

2. **Validation and Error Handling**
   - Invalid IDs
   - Validation constraints
   - Business rules

3. **Business Logic**
   - Inventory thresholds affecting menu item availability
   - Inventory adjustments and transfers
   - Transaction processing with inventory updates

4. **Data Relationships**
   - Stand-to-window relationships
   - Menu item to inventory relationships
   - Cross-entity validation

## Test Data

Each test gets a fresh set of test data via fixtures in `conftest.py`. This includes:

- A test stand
- A test window
- A test inventory item
- A test menu item
- A test transaction

Tests that need additional data or specific conditions create that data within the test function.

## Dependencies

- pytest
- FastAPI
- SQLModel
- pytest-cov (optional, for coverage reports)

## Generating Coverage Reports

To generate a test coverage report:

```bash
pytest --cov=free_org
```

For an HTML coverage report:

```bash
pytest --cov=free_org --cov-report=html
```

This will create an `htmlcov` directory with the coverage report.