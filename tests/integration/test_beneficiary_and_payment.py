from tests.conftest import auth_headers


def _create_active_policy(client, admin_token, email, id_number, premium=15000.00, coverage=500000.00):
    plan = client.post("/api/v1/plans",
        json={"plan_name": "Test Plan", "plan_type": "HEALTH", "coverage_amount": coverage, "premium_amount": premium,
              "duration_years": 1, "eligibility_age_min": 18, "eligibility_age_max": 65},
        headers=auth_headers(admin_token)).json()["data"]

    client.post("/api/v1/customers",
        json={"full_name": "Test Customer", "email": email, "phone": "9100000002", "password": "Test@1234",
              "date_of_birth": "1990-01-01", "identification_number": id_number},
        headers=auth_headers(admin_token))
    customers = client.get("/api/v1/customers", headers=auth_headers(admin_token)).json()["data"]
    customer_id = next(c["id"] for c in customers if c["user"]["email"] == email)

    policy = client.post("/api/v1/policies",
        json={"customer_id": customer_id, "plan_id": plan["id"], "start_date": "2026-09-01", "end_date": "2027-08-31"},
        headers=auth_headers(admin_token)).json()["data"]

    return policy, customer_id


def test_beneficiary_percentage_cannot_exceed_100(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "benef1@test.com", "ID-BEN-001")

    first = client.post(f"/api/v1/policies/{policy['id']}/beneficiaries",
        json={"name": "Spouse", "relationship_type": "Spouse", "percentage": 60.00}, headers=auth_headers(admin_token))
    assert first.status_code == 201

    second = client.post(f"/api/v1/policies/{policy['id']}/beneficiaries",
        json={"name": "Son", "relationship_type": "Son", "percentage": 50.00}, headers=auth_headers(admin_token))
    assert second.status_code == 400


def test_duplicate_beneficiary_blocked(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "benef2@test.com", "ID-BEN-002")

    client.post(f"/api/v1/policies/{policy['id']}/beneficiaries",
        json={"name": "Spouse", "relationship_type": "Spouse", "percentage": 50.00, "identification_number": "ID-SPOUSE-001"},
        headers=auth_headers(admin_token))

    duplicate = client.post(f"/api/v1/policies/{policy['id']}/beneficiaries",
        json={"name": "Spouse", "relationship_type": "Spouse", "percentage": 30.00, "identification_number": "ID-SPOUSE-001"},
        headers=auth_headers(admin_token))
    assert duplicate.status_code == 400


def test_payment_amount_must_match_premium(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "pay1@test.com", "ID-PAY-001", premium=15000.00)

    response = client.post(f"/api/v1/policies/{policy['id']}/premium-payment",
        json={"amount": 5000.00, "payment_method": "UPI", "transaction_id": "TXNTEST001"}, headers=auth_headers(admin_token))
    assert response.status_code == 400


def test_payment_activates_policy_and_locks_transaction_id(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "pay2@test.com", "ID-PAY-002", premium=15000.00)

    payment = client.post(f"/api/v1/policies/{policy['id']}/premium-payment",
        json={"amount": 15000.00, "payment_method": "UPI", "transaction_id": "TXNTEST002"}, headers=auth_headers(admin_token))
    assert payment.status_code == 201

    policy_check = client.get(f"/api/v1/policies/{policy['id']}", headers=auth_headers(admin_token)).json()["data"]
    assert policy_check["policy_status"] == "ACTIVE"

    duplicate_txn = client.post(f"/api/v1/policies/{policy['id']}/premium-payment",
        json={"amount": 15000.00, "payment_method": "UPI", "transaction_id": "TXNTEST002"}, headers=auth_headers(admin_token))
    assert duplicate_txn.status_code == 400