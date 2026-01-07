from fastapi.testclient import TestClient
from app.main import app
import random
import string

# 1. THE ROBOT BROWSER (It acts like Chrome, but headless)
client = TestClient(app)

def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def test_create_vendor_success():
    print("\n🤖 ROBOT: Preparing to register a new vendor...")

    # 2. THE DYNAMIC PAYLOAD (Unique every time)
    rand_id = generate_random_string()
    payload = {
        "business_name": f"Auto Test Biz {rand_id}",
        "business_type": "Automation",
        "email": f"robot_{rand_id}@occacia.com",
        "contact_number": "+94770000000",
        "address": "123 Virtual Street"
    }

    # 3. THE ATTACK (Send POST request)
    response = client.post("/vendors/", json=payload)

    # 4. THE INSPECTION (Did it work?)
    # Check if the door opened (200 OK or 201 Created)
    assert response.status_code in [200, 201], f"Failed! Got: {response.text}"
    
    data = response.json()
    print(f"✅ SUCCESS! Created Vendor ID: {data['id']}")

    # Verify the stamps on the passport
    assert data["email"] == payload["email"]
    assert data["status"] == "Pending Approval"
    assert "id" in data
    assert "created_at" in data

def test_duplicate_vendor_failure():
    # 1. Create a vendor first
    rand_id = generate_random_string()
    payload = {
        "business_name": "Duplicate Biz",
        "business_type": "Test",
        "email": f"dup_{rand_id}@test.com",
        "contact_number": "123",
        "address": "123"
    }
    client.post("/vendors/", json=payload)

    # 2. Try to create the SAME vendor again
    print(f"🤖 ROBOT: Attempting to break security with duplicate email: {payload['email']}")
    response = client.post("/vendors/", json=payload)

    # 3. Expect a REJECTION (400 Bad Request)
    assert response.status_code == 400
    print("🛡️ SECURITY: Duplicate blocked successfully!")