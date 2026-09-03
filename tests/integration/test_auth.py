from tests.conftest import auth_headers

def test_admin_login(client, admin_token):
    assert admin_token is not None

def test_register_requires_admin(client):
    response = client.post("/api/v1/auth/register",
        json={"full_name": "Sneaky", "email": "sneaky@test.com", "phone": "9555555555", "password": "Test@1234", "role": "INSURANCE_AGENT"})
    assert response.status_code == 401

def test_admin_registers_all_three_staff_roles(client, agent_token, claims_officer_token, finance_officer_token):
    assert agent_token is not None
    assert claims_officer_token is not None
    assert finance_officer_token is not None

def test_refresh_token_issues_new_access_token(client, admin_token):
    login = client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": "Admin@12345"})
    refresh_token = login.json()["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_customer_self_registers_no_token_needed(client):
    response = client.post("/api/v1/customers",
        json={"full_name": "Self Reg", "email": "selfreg@test.com", "phone": "9888888888", "password": "Test@1234",
              "date_of_birth": "1990-01-01", "identification_number": "ID-SELF-001"})
    assert response.status_code == 201
    assert response.json()["data"]["created_by"] is None

def test_underage_customer_blocked(client):
    from datetime import date
    recent_year = date.today().year - 5
    response = client.post("/api/v1/customers",
        json={"full_name": "Too Young", "email": "young@test.com", "phone": "9777777777", "password": "Test@1234",
              "date_of_birth": f"{recent_year}-01-01", "identification_number": "ID-YOUNG-001"})
    assert response.status_code == 422

def test_activation_blocks_self_change(client, admin_token):
    me = client.get("/api/v1/auth/me", headers=auth_headers(admin_token)).json()["data"]
    response = client.put(f"/api/v1/auth/{me['id']}/activation", json={"is_active": False}, headers=auth_headers(admin_token))
    assert response.status_code == 400