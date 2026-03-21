"""
tests/JIT/admin_manage_customers_uc29_jit.py
Just-In-Time test for UC-29: Manage Customers
Simulates the full admin workflow for managing customer accounts.
"""

import uuid
from app.core.database import SessionLocal
from app.core.security import get_password_hash, create_access_token
from app.models.customer import Customer
from app.models.admin import Admin


def _uid():
    return str(uuid.uuid4())[:8]


def _create_admin(db, email: str = None) -> Admin:
    if email is None:
        email = f"admin-{_uid()}@test.com"
    admin = Admin(
        email=email,
        password_hash=get_password_hash("Admin1234!"),
        staff_role="staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _create_customer(db, email: str = None, status: str = "ACTIVE") -> Customer:
    if email is None:
        email = f"customer-{_uid()}@test.com"
    customer = Customer(
        email=email,
        full_name=f"Customer {_uid()}",
        password_hash=get_password_hash("Password1!"),
        phone="+94771234567",
        locale="en",
        email_verified=True,
        status=status,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def test_uc29_admin_manage_customers_full_workflow(client):
    """
    UC-29: Manage Customers
    
    Scenario:
    1. Admin lists all customers
    2. Admin filters customers by status
    3. Admin views a specific customer's details
    4. Admin updates customer status to SUSPENDED
    5. Admin updates customer status back to ACTIVE
    6. Admin attempts to set invalid status (should fail)
    7. Admin attempts to access non-existent customer (should fail)
    """
    
    db = SessionLocal()
    try:
        # Setup: Create admin and customers
        admin = _create_admin(db)
        admin_id = admin.admin_id
        
        customer1 = _create_customer(db, status="ACTIVE")
        customer2 = _create_customer(db, status="PENDING")
        customer3 = _create_customer(db, status="SUSPENDED")
        
        customer1_id = customer1.customer_id
        customer2_id = customer2.customer_id
        customer3_id = customer3.customer_id
    finally:
        db.close()
    
    # Generate admin token
    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Admin lists all customers
    print("\n[UC-29 Step 1] Admin lists all customers")
    response = client.get("/api/v1/admin/customers", headers=headers)
    assert response.status_code == 200, f"Failed to list customers: {response.text}"
    body = response.json()
    assert "items" in body
    assert len(body["items"]) >= 3
    print(f"[OK] Listed {len(body['items'])} customers")
    
    # Step 2: Admin filters customers by status (ACTIVE)
    print("\n[UC-29 Step 2] Admin filters customers by status=ACTIVE")
    response = client.get(
        "/api/v1/admin/customers",
        params={"status": "ACTIVE"},
        headers=headers,
    )
    assert response.status_code == 200, f"Failed to filter customers: {response.text}"
    body = response.json()
    active_customers = body["items"]
    assert all(c["status"] == "ACTIVE" for c in active_customers)
    print(f"[OK] Found {len(active_customers)} ACTIVE customers")
    
    # Step 3: Admin views a specific customer's details
    print(f"\n[UC-29 Step 3] Admin views customer {customer1_id} details")
    response = client.get(
        f"/api/v1/admin/customers/{customer1_id}",
        headers=headers,
    )
    assert response.status_code == 200, f"Failed to get customer detail: {response.text}"
    body = response.json()
    assert body["customer_id"] == customer1_id
    assert body["status"] == "ACTIVE"
    assert "email" in body
    assert "full_name" in body
    print(f"[OK] Retrieved customer: {body['email']} (status: {body['status']})")
    
    # Step 4: Admin updates customer status to SUSPENDED
    print(f"\n[UC-29 Step 4] Admin suspends customer {customer1_id}")
    response = client.put(
        f"/api/v1/admin/customers/{customer1_id}/status",
        json={"status": "SUSPENDED"},
        headers=headers,
    )
    assert response.status_code == 200, f"Failed to suspend customer: {response.text}"
    body = response.json()
    assert body["status"] == "SUSPENDED"
    print(f"[OK] Customer {customer1_id} suspended successfully")
    
    # Verify DB state
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer1_id).first()
        assert customer.status == "SUSPENDED", "Status not persisted in DB"
        print("[OK] Status change persisted in database")
    finally:
        db.close()
    
    # Step 5: Admin updates customer status back to ACTIVE
    print(f"\n[UC-29 Step 5] Admin reactivates customer {customer1_id}")
    response = client.put(
        f"/api/v1/admin/customers/{customer1_id}/status",
        json={"status": "ACTIVE"},
        headers=headers,
    )
    assert response.status_code == 200, f"Failed to reactivate customer: {response.text}"
    body = response.json()
    assert body["status"] == "ACTIVE"
    print(f"[OK] Customer {customer1_id} reactivated successfully")
    
    # Step 6: Admin attempts to set invalid status (should fail)
    print(f"\n[UC-29 Step 6] Admin attempts invalid status update")
    response = client.put(
        f"/api/v1/admin/customers/{customer1_id}/status",
        json={"status": "INVALID_STATUS"},
        headers=headers,
    )
    assert response.status_code in (400, 422), f"Should reject invalid status: {response.text}"
    print("[OK] Invalid status rejected as expected")
    
    # Verify status unchanged
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer1_id).first()
        assert customer.status == "ACTIVE", "Status should remain unchanged after failed update"
        print("[OK] Customer status unchanged after failed update")
    finally:
        db.close()
    
    # Step 7: Admin attempts to access non-existent customer (should fail)
    print("\n[UC-29 Step 7] Admin attempts to access non-existent customer")
    response = client.get(
        "/api/v1/admin/customers/CUS-NOTFOUND",
        headers=headers,
    )
    assert response.status_code == 404, f"Should return 404 for non-existent customer: {response.text}"
    print("[OK] Non-existent customer returns 404 as expected")
    
    # Step 8: Test unauthenticated access (should fail)
    print("\n[UC-29 Step 8] Unauthenticated access should be rejected")
    response = client.get("/api/v1/admin/customers")
    assert response.status_code == 401, f"Should reject unauthenticated access: {response.text}"
    print("[OK] Unauthenticated access rejected")
    
    # Step 9: Test non-admin access (should fail)
    print("\n[UC-29 Step 9] Non-admin access should be rejected")
    customer_token = create_access_token(data={"sub": customer1.email})
    response = client.get(
        "/api/v1/admin/customers",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 401, f"Should reject non-admin access: {response.text}"
    print("[OK] Non-admin access rejected")
    
    # Step 10: Test DISABLED status
    print(f"\n[UC-29 Step 10] Admin disables customer {customer2_id}")
    response = client.put(
        f"/api/v1/admin/customers/{customer2_id}/status",
        json={"status": "DISABLED"},
        headers=headers,
    )
    assert response.status_code == 200, f"Failed to disable customer: {response.text}"
    body = response.json()
    assert body["status"] == "DISABLED"
    print(f"[OK] Customer {customer2_id} disabled successfully")
    
    print("\n" + "="*60)
    print("[OK] UC-29: Manage Customers - ALL TESTS PASSED")
    print("="*60)
