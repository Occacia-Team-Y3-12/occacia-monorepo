# from uuid import uuid4
# import jwt
# import pytest
# from app.core.database import SessionLocal
# from app.core.security import ALGORITHM, SECRET_KEY, get_password_hash
# from app.models.customer import Customer
# from app.models.vendor import Vendor


# # ── Registration ─────────────────────────────────────────────────────

# def test_customer_register_success(client):
#     email = f"user-{uuid4().hex[:8]}@test.com"
#     r = client.post("/api/v1/auth/customers/register", json={
#         "full_name": "Jane Doe",
#         "email": email,
#         "password": "StrongPass123!",
#         "phone": "+94771234567",
#     })
#     assert r.status_code == 201
#     assert r.json()["email"] == email
#     assert r.json()["message"] == "Verification email sent"


# def test_customer_register_duplicate_email(client):
#     email = f"user-{uuid4().hex[:8]}@test.com"
#     payload = {"full_name": "Jane", "email": email, "password": "Pass123!"}
#     client.post("/api/v1/auth/customers/register", json=payload)
#     r = client.post("/api/v1/auth/customers/register", json=payload)
#     assert r.status_code == 400
#     assert r.json()["detail"] == "This email is already registered."


# def test_vendor_register_success(client):
#     r = client.post("/api/v1/auth/vendors/register", json={
#         "business_name": f"Vendor {uuid4().hex[:6]}",
#         "email": f"vendor-{uuid4().hex[:8]}@test.com",
#         "password": "StrongPass123!",
#         "location_base": "Colombo",
#         "phone": "+94771234567",
#     })
#     assert r.status_code == 201


# def test_vendor_register_duplicate_email(client):
#     email = f"vendor-{uuid4().hex[:8]}@test.com"
#     payload = {
#         "business_name": f"Vendor {uuid4().hex[:6]}",
#         "email": email,
#         "password": "Pass123!",
#     }
#     client.post("/api/v1/auth/vendors/register", json=payload)
#     r = client.post("/api/v1/auth/vendors/register", json=payload)
#     assert r.status_code == 400


# # ── Email Verification ───────────────────────────────────────────────

# def test_customer_verify_email_success(client):
#     email = f"user-{uuid4().hex[:8]}@test.com"
#     client.post("/api/v1/auth/customers/register", json={
#         "full_name": "Jane", "email": email, "password": "Pass123!"
#     })
#     db = SessionLocal()
#     token = db.query(Customer).filter(Customer.email == email).first().verification_token
#     db.close()

#     r = client.get("/api/v1/auth/customers/verify-email", params={"token": token})
#     assert r.status_code == 200
#     assert r.json()["message"] == "Email verified successfully"

#     db = SessionLocal()
#     c = db.query(Customer).filter(Customer.email == email).first()
#     assert c.email_verified is True
#     assert c.status == "ACTIVE"
#     db.close()


# def test_customer_verify_email_invalid_token(client):
#     r = client.get("/api/v1/auth/customers/verify-email", params={"token": "bad-token"})
#     assert r.status_code == 400
#     assert r.json()["detail"] == "Invalid verification token."


# def test_customer_verify_email_already_verified(client):
#     email = f"user-{uuid4().hex[:8]}@test.com"
#     client.post("/api/v1/auth/customers/register", json={
#         "full_name": "Jane", "email": email, "password": "Pass123!"
#     })
#     db = SessionLocal()
#     token = db.query(Customer).filter(Customer.email == email).first().verification_token
#     db.close()

#     client.get("/api/v1/auth/customers/verify-email", params={"token": token})
#     r = client.get("/api/v1/auth/customers/verify-email", params={"token": token})
#     assert r.status_code == 200
#     assert r.json()["message"] == "Email already verified"


# def test_vendor_verify_email_success(client):
#     email = f"vendor-{uuid4().hex[:8]}@test.com"
#     client.post("/api/v1/auth/vendors/register", json={
#         "business_name": f"V {uuid4().hex[:6]}",
#         "email": email,
#         "password": "Pass123!",
#     })
#     token = jwt.encode(
#         {"sub": email, "type": "verify_vendor_email"},
#         SECRET_KEY, algorithm=ALGORITHM
#     )
#     r = client.get("/api/v1/auth/vendors/verify-email", params={"token": token})
#     assert r.status_code == 200
#     assert r.json()["message"] == "Email verified successfully"


# # ── Login ────────────────────────────────────────────────────────────

# def test_customer_login_success(client, active_customer):
#     r = client.post("/api/v1/auth/customers/login", data={
#         "username": active_customer.email,
#         "password": "Test1234!",
#     })
#     assert r.status_code == 200
#     assert "access_token" in r.json()
#     assert r.json()["token_type"] == "bearer"


# def test_customer_login_wrong_password(client, active_customer):
#     r = client.post("/api/v1/auth/customers/login", data={
#         "username": active_customer.email,
#         "password": "WrongPass!",
#     })
#     assert r.status_code == 401


# def test_customer_login_unknown_email(client):
#     r = client.post("/api/v1/auth/customers/login", data={
#         "username": "nobody@test.com",
#         "password": "Pass123!",
#     })
#     assert r.status_code == 401


# # ── Password Reset ───────────────────────────────────────────────────

# def test_forgot_password_known_email(client, active_customer):
#     r = client.post("/api/v1/auth/customers/forgot-password",
#                     json={"email": active_customer.email})
#     assert r.status_code == 200
#     assert "reset link" in r.json()["message"].lower()


# def test_forgot_password_unknown_email(client):
#     r = client.post("/api/v1/auth/customers/forgot-password",
#                     json={"email": "nobody@test.com"})
#     assert r.status_code == 200  # Security: same response regardless


# def test_reset_password_invalid_token(client):
#     r = client.post("/api/v1/auth/customers/reset-password",
#                     json={"token": "bad-token", "new_password": "NewPass123!"})
#     assert r.status_code == 400