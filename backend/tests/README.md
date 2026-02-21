# Backend Test Suite

## Overview

This directory contains comprehensive unit and integration tests for the AI Receptionist backend services.

## Test Coverage

### Current Tests

1. **test_business_templates.py**
   - Business template service tests
   - Template validation and caching
   - Template version management
   - Risk profile validation

2. **test_governance.py**
   - Governance tier logic tests
   - Intent validation tests
   - Risk profile validation
   - Safety trigger tests
   - Autonomy level governance

3. **test_nova_reasoning.py** (NEW)
   - Deterministic safety triggers
   - Emergency detection
   - VIP customer handling
   - Repeat complaint patterns
   - Training context retrieval
   - Response quality evaluation
   - Synthetic training data generation

4. **test_nova_sonic_stream.py** (NEW)
   - Latency tracking
   - Streaming session lifecycle
   - Thinking block filtering
   - System prompt building
   - Tool definitions
   - Queue behavior
   - Conversation history

5. **test_calendar_service.py** (NEW)
   - Google OAuth flow
   - Microsoft OAuth flow
   - Token exchange and refresh
   - Event creation and management
   - Availability checking
   - Two-way calendar sync
   - Built-in calendar operations

## Running Tests

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_nova_reasoning.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_nova_reasoning.py::TestDeterministicTriggers -v
```

### Run Specific Test Method

```bash
pytest tests/test_nova_reasoning.py::TestDeterministicTriggers::test_critical_keyword_detection -v
```

### Run with Coverage Report

```bash
pytest tests/ --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## Test Structure

```
tests/
├── README.md                          # This file
├── test_business_templates.py         # Business template tests
├── test_governance.py                 # Governance logic tests
├── test_nova_reasoning.py             # Nova reasoning engine tests
├── test_nova_sonic_stream.py          # Streaming session tests
└── test_calendar_service.py           # Calendar integration tests
```

## Writing New Tests

### Test Naming Convention

```python
class TestFeatureName:
    """Docstring describing what this class tests"""
    
    def test_specific_behavior(self, fixture_name):
        """Docstring describing what this specific test does"""
        # Arrange
        # Act
        # Assert
        pass
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    """Fixture that provides sample data"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
@patch('app.services.some_service.external_api_call')
async def test_with_mock(mock_api_call):
    mock_api_call.return_value = {"data": "mocked"}
    result = await function_under_test()
    assert result == "mocked"
```

## Test Categories

### Unit Tests

- Test individual functions and methods
- Mock all external dependencies
- Fast execution
- No database interaction required

### Integration Tests

- Test interactions between components
- Use real database (test instance)
- Test API endpoints
- Slower execution

### End-to-End Tests

- Test complete workflows
- Simulate real user scenarios
- Use all real services
- Slowest execution

## Coverage Goals

### Minimum Coverage Targets

- **Core Services**: 80%+
  - nova_reasoning.py
  - nova_sonic.py
  - nova_sonic_stream.py
  - calendar_service.py
  - crm_integration.py

- **Business Logic**: 70%+
  - business_templates.py
  - intent_classifier.py
  - customer_360_service.py

- **API Routes**: 60%+
  - All API v1 endpoints

### Current Coverage Status

| Module | Coverage | Status |
|--------|----------|--------|
| business_template_service.py | 75% | ✅ Good |
| business_templates.py | 70% | ✅ Good |
| nova_reasoning.py | 60% | ⚠️ Needs work |
| nova_sonic_stream.py | 65% | ⚠️ Needs work |
| calendar_service.py | 70% | ✅ Good |
| nova_act.py | 0% | ❌ No tests |
| crm_integration.py | 0% | ❌ No tests |
| payment_service.py | 0% | ❌ No tests |

## Common Patterns

### Testing Error Handling

```python
def test_error_handling():
    with pytest.raises(ValueError, match="expected error message"):
        function_that_raises_error()
```

### Testing Async Generators

```python
@pytest.mark.asyncio
async def test_async_generator():
    async for item in async_generator_function():
        assert item is not None
```

### Testing with Database

```python
@pytest.fixture
def db_session():
    """Create a test database session"""
    # Setup test database
    session = create_test_session()
    yield session
    # Cleanup
    session.close()

def test_with_database(db_session):
    result = db_session.query(Model).first()
    assert result is not None
```

## Continuous Integration

Tests run automatically on:
- Every pull request
- Every push to main branch
- Nightly builds

## Troubleshooting

### Tests Fail Due to Missing Environment Variables

Set up a `.env.test` file:

```env
AWS_ACCESS_KEY_ID=test_key
AWS_SECRET_ACCESS_KEY=test_secret
AWS_REGION=us-east-1
GOOGLE_CLIENT_ID=test_client_id
GOOGLE_CLIENT_SECRET=test_client_secret
```

### Tests Fail Due to Database Connection

Ensure test database is running:

```bash
docker-compose up -d postgres-test
```

### Tests Timeout

Increase timeout in `pytest.ini`:

```ini
[pytest]
timeout = 300
asyncio_mode = auto
```

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update this README with new test files

## Future Test Plans

### Priority 1 (High)
- [ ] nova_act.py tests (Playwright automation)
- [ ] crm_integration.py tests
- [ ] payment_service.py tests
- [ ] API endpoint integration tests

### Priority 2 (Medium)
- [ ] customer_360_service.py tests
- [ ] sentiment_service.py tests
- [ ] churn_service.py tests
- [ ] webhook_service.py tests

### Priority 3 (Low)
- [ ] Frontend E2E tests
- [ ] Load testing
- [ ] Performance benchmarking tests