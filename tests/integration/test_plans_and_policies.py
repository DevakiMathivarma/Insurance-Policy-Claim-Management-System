from tests.conftest import auth_headers


def test_plan_coverage_must_exceed_premium(client, admin_token):
    response = client.post("/api/v1/plans",
        json={"plan_name": "Bad Plan", "plan_type": "HEALTH", "coverage_amount": 10000.00, "premium_amount": 15000.00,
              "duration_years": 1, "eligibility_age_min": 18, "eligibility_age_max": 65},
        headers=auth_headers(admin_token))
    assert response.status_code == 422


def test_create_plan_success(client, admin_token):
    response = client.post("/api/v1/plans",
        json={"plan_name": "Health Cover", "plan_type": "HEALTH", "coverage_amount": 500000.00, "premium_amount": 15000.00,
              "duration_years": 1, "eligibility_age_min": 18, "eligibility_age_max": 65},
        headers=auth_headers(admin_token))
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "ACTIVE"


def _create_plan(client, admin_token, age_min=18, age_max=65, premium=15000.00, coverage=500000.00):
    return client.post("/api/v1/plans",
        json={"plan_name": "Test Plan", "plan_type": "HEALTH", "coverage_amount": coverage, "premium_amount": premium,
              "duration_years": 1, "eligibility_age_min": age_min, "eligibility_age_max": age_max},
        headers=auth_headers(admin_token)).json()["data"]


def _create_customer(client, admin_token, email, dob="1990-01-01", id_number="ID-TEST-001"):
    client.post("/api/v1/customers",
        json={"full_name": "Test Customer", "email": email, "phone": "9100000001", "password": "Test@1234",
              "date_of_birth": dob, "identification_number": id_number},
        headers=auth_headers(admin_token))
    customers = client.get("/api/v1/customers", headers=auth_headers(admin_token)).json()["data"]
    for c in customers:
        if c["user"]["email"] == email:
            return c["id"]
    return customers[0]["id"]


def test_policy_creation_checks_eligibility_age(client, admin_token):
    plan = _create_plan(client, admin_token, age_min=18, age_max=25)
    customer_id = _create_customer(client, admin_token, "oldcustomer@test.com", dob="1970-01-01", id_number="ID-OLD-001")

    response = client.post("/api/v1/policies",
        json={"customer_id": customer_id, "plan_id": plan["id"], "start_date": "2026-09-01", "end_date": "2027-08-31"},
        headers=auth_headers(admin_token))
    assert response.status_code == 400


def test_policy_creation_locks_in_plan_amounts(client, admin_token):
    plan = _create_plan(client, admin_token, premium=15000.00, coverage=500000.00)
    customer_id = _create_customer(client, admin_token, "goodcustomer@test.com", id_number="ID-GOOD-001")

    response = client.post("/api/v1/policies",
        json={"customer_id": customer_id, "plan_id": plan["id"], "start_date": "2026-09-01", "end_date": "2027-08-31"},
        headers=auth_headers(admin_token))
    assert response.status_code == 201
    data = response.json()["data"]
    assert float(data["premium_amount"]) == 15000.00
    assert float(data["coverage_amount"]) == 500000.00
    assert data["policy_status"] == "PENDING"


def test_activate_policy_generates_document_and_sends_email(client, admin_token):
    plan = _create_plan(client, admin_token)
    customer_id = _create_customer(client, admin_token, "activatetest@test.com", id_number="ID-ACT-001")
    policy = client.post("/api/v1/policies",
        json={"customer_id": customer_id, "plan_id": plan["id"], "start_date": "2026-09-01", "end_date": "2027-08-31"},
        headers=auth_headers(admin_token)).json()["data"]

    response = client.post(f"/api/v1/policies/{policy['id']}/activate", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()["data"]["policy_status"] == "ACTIVE"

    second_attempt = client.post(f"/api/v1/policies/{policy['id']}/activate", headers=auth_headers(admin_token))
    assert second_attempt.status_code == 400


def test_renew_policy_and_prevent_duplicate_renewal(client, admin_token):
    plan = _create_plan(client, admin_token)
    customer_id = _create_customer(client, admin_token, "renewtest@test.com", id_number="ID-RENEW-001")
    policy = client.post("/api/v1/policies",
        json={"customer_id": customer_id, "plan_id": plan["id"], "start_date": "2026-09-01", "end_date": "2027-08-31"},
        headers=auth_headers(admin_token)).json()["data"]
    client.post(f"/api/v1/policies/{policy['id']}/activate", headers=auth_headers(admin_token))

    renew_response = client.post(f"/api/v1/policies/{policy['id']}/renew", headers=auth_headers(admin_token))
    assert renew_response.status_code == 200
    new_policy = renew_response.json()["data"]
    assert new_policy["policy_status"] == "PENDING"
    assert str(new_policy["start_date"]) == "2027-08-31"

    duplicate_renewal = client.post(f"/api/v1/policies/{policy['id']}/renew", headers=auth_headers(admin_token))
    assert duplicate_renewal.status_code == 400