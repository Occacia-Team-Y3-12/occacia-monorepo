# backend/tests/test_vendor_tasks.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.vendor import Vendor
from app.core.security import create_access_token

# TODO: Replace module-level skip once async fixture wiring is finalized for vendor task integration tests.
pytestmark = pytest.mark.skip(reason="Pending async DB fixture wiring for vendor task integration tests")

@pytest.fixture
async def approved_vendor(db: AsyncSession):
    """Create approved vendor for testing"""
    vendor = Vendor(
        business_name="Test Vendor",
        email="vendor@test.com",
        approval_status="APPROVED",
        phone="1234567890",
        is_verified=True
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor

@pytest.fixture
async def vendor_token(approved_vendor):
    """Create auth token for vendor"""
    return create_access_token(data={"sub": str(approved_vendor.id)})

@pytest.fixture
async def sample_tasks(db: AsyncSession, approved_vendor):
    """Create sample tasks for testing"""
    tasks = [
        Task(
            event_id="EVT001",
            name="Birthday Party Planning",
            status="pending_response",
            quantity=1,
            currency="USD"
        ),
        Task(
            event_id="EVT002",
            name="Dinner Reservation",
            status="assigned",
            quantity=1,
            currency="USD"
        ),
        Task(
            event_id="EVT003",
            name="Hospital Visit Flowers",
            status="completed",
            quantity=1,
            currency="USD"
        )
    ]
    for task in tasks:
        db.add(task)
    await db.commit()
    return tasks

async def test_list_vendor_tasks(
    client: AsyncClient,
    approved_vendor,
    vendor_token,
    sample_tasks
):
    """Test successful retrieval of vendor tasks"""
    response = await client.get(
        "/api/v1/vendors/tasks",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify grouping
    assert len(data["pending_response"]) == 1
    assert len(data["assigned"]) == 1
    assert len(data["completed"]) == 1
    assert data["total_count"] == 3

async def test_unapproved_vendor_blocked(
    client: AsyncClient,
    db: AsyncSession
):
    """Test that unapproved vendors cannot access tasks"""
    # Create pending vendor
    vendor = Vendor(
        business_name="Pending Vendor",
        email="pending@test.com",
        approval_status="PENDING",
        phone="1234567891",
        is_verified=True
    )
    db.add(vendor)
    await db.commit()
    
    token = create_access_token(data={"sub": str(vendor.id)})
    
    response = await client.get(
        "/api/v1/vendors/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "pending" in response.json()["detail"].lower()

async def test_empty_state(
    client: AsyncClient,
    approved_vendor,
    vendor_token
):
    """Test empty state when no tasks exist"""
    response = await client.get(
        "/api/v1/vendors/tasks",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert all(len(group) == 0 for group in [
        data["pending_response"],
        data["assigned"],
        data["completed"],
        data["rejected_expired"]
    ])
