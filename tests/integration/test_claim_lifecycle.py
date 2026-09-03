import io
from tests.conftest import auth_headers


def _create_active_policy(client, admin_token, email, id_number, premium=15000.00, coverage=500000.00,
                           start_date="2026-01-01", end_date="2026-12-31"):
    plan = client.post("/api/v1/plans",
        json={"plan_name": "Test Plan", "plan_type": "HEALTH", "coverage_amount": coverage, "premium_amount": premium,
              "duration_years": 1, "eligibility_age_min": 18, "eligibility_age_max": 65},
        headers=auth_headers(admin_token)).json()["data"]

    client.post("/api/v1/customers",
        json={"full_name": "Test Customer", "email": email, "phone": "9100000003", "password": "Test@1234",
              "date_of_birth": "1990-01-01", "identification_number": id_number},
        headers=auth_headers(admin_token))
    customers = client.get("/api/v1/customers", headers=auth_headers(admin_token)).json()["data"]
    customer_id = next(c["id"] for c in customers if c["user"]["email"] == email)

    policy = client.post("/api/v1/policies",
        json={"customer_id": customer_id, "plan_id": plan["id"], "start_date": start_date, "end_date": end_date},
        headers=auth_headers(admin_token)).json()["data"]

    client.post(f"/api/v1/policies/{policy['id']}/premium-payment",
        json={"amount": premium, "payment_method": "UPI", "transaction_id": f"TXN-{id_number}"},
        headers=auth_headers(admin_token))

    policy_check = client.get(f"/api/v1/policies/{policy['id']}", headers=auth_headers(admin_token)).json()["data"]
    return policy_check, customer_id


def test_claim_incident_date_must_be_within_coverage(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "claim1@test.com", "ID-CLM-001")

    response = client.post("/api/v1/claims",
        json={"policy_id": policy["id"], "claim_type": "Hospitalization", "incident_date": "2027-06-01", "claim_amount": 80000.00},
        headers=auth_headers(admin_token))
    assert response.status_code == 400


def test_claim_amount_cannot_exceed_coverage(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "claim2@test.com", "ID-CLM-002", coverage=50000.00)

    response = client.post("/api/v1/claims",
        json={"policy_id": policy["id"], "claim_type": "Hospitalization", "incident_date": "2026-06-01", "claim_amount": 80000.00},
        headers=auth_headers(admin_token))
    assert response.status_code == 400


def test_duplicate_incident_claim_blocked(client, admin_token):
    policy, _ = _create_active_policy(client, admin_token, "claim3@test.com", "ID-CLM-003")

    first = client.post("/api/v1/claims",
        json={"policy_id": policy["id"], "claim_type": "Hospitalization", "incident_date": "2026-06-01", "claim_amount": 80000.00},
        headers=auth_headers(admin_token))
    assert first.status_code == 201

    duplicate = client.post("/api/v1/claims",
        json={"policy_id": policy["id"], "claim_type": "Hospitalization", "incident_date": "2026-06-01", "claim_amount": 50000.00},
        headers=auth_headers(admin_token))
    assert duplicate.status_code == 400


def test_full_claim_lifecycle_draft_to_settled(client, admin_token, claims_officer_token, finance_officer_token):
    policy, _ = _create_active_policy(client, admin_token, "claim4@test.com", "ID-CLM-004")

    claim = client.post("/api/v1/claims",
        json={"policy_id": policy["id"], "claim_type": "Hospitalization", "incident_date": "2026-06-01",
              "claim_amount": 80000.00, "description": "Appendicitis surgery"},
        headers=auth_headers(admin_token)).json()["data"]
    assert claim["status"] == "DRAFT"

    submit_response = client.post(f"/api/v1/claims/{claim['id']}/submit", headers=auth_headers(admin_token))
    assert submit_response.status_code == 200
    assert submit_response.json()["data"]["status"] == "SUBMITTED"

    # try approving before any documents are verified - should be blocked
    early_approve = client.post(f"/api/v1/claims/{claim['id']}/approve", headers=auth_headers(claims_officer_token))
    assert early_approve.status_code == 400

    # upload a document
    file_content = b"%PDF-1.4 fake pdf content for testing"
    upload_response = client.post(f"/api/v1/claims/{claim['id']}/documents",
        data={"document_type": "MEDICAL_REPORT"},
        files={"file": ("medical_report.pdf", io.BytesIO(file_content), "application/pdf")},
        headers=auth_headers(admin_token))
    assert upload_response.status_code == 201
    document_id = upload_response.json()["data"]["id"]

    # try uploading a disallowed file type
    bad_upload = client.post(f"/api/v1/claims/{claim['id']}/documents",
        data={"document_type": "OTHER"},
        files={"file": ("virus.exe", io.BytesIO(b"fake"), "application/octet-stream")},
        headers=auth_headers(admin_token))
    assert bad_upload.status_code == 400

    # verify the document
    verify_response = client.put(f"/api/v1/documents/{document_id}/verify",
        params={"verification_status": "VERIFIED"}, headers=auth_headers(claims_officer_token))
    assert verify_response.status_code == 200

    # create assessment - eligible amount cannot exceed coverage
    bad_assessment = client.post(f"/api/v1/claims/{claim['id']}/assessment",
        json={"eligible_amount": 999999999.00}, headers=auth_headers(claims_officer_token))
    assert bad_assessment.status_code == 400

    assessment = client.post(f"/api/v1/claims/{claim['id']}/assessment",
        json={"eligible_amount": 75000.00, "recommendation": "Approve at reduced amount"},
        headers=auth_headers(claims_officer_token))
    assert assessment.status_code == 201

    # now approval should succeed since the document is verified
    approve_response = client.post(f"/api/v1/claims/{claim['id']}/approve", headers=auth_headers(claims_officer_token))
    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["status"] == "APPROVED"

    # settlement cannot exceed the assessed eligible amount
    bad_settlement = client.post(f"/api/v1/claims/{claim['id']}/settle",
        json={"approved_amount": 999999.00}, headers=auth_headers(finance_officer_token))
    assert bad_settlement.status_code == 400

    settlement = client.post(f"/api/v1/claims/{claim['id']}/settle",
        json={"approved_amount": 75000.00, "payment_reference": "SETTLE-001"}, headers=auth_headers(finance_officer_token))
    assert settlement.status_code == 201
    assert settlement.json()["data"]["settlement_status"] == "COMPLETED"

    claim_check = client.get(f"/api/v1/claims/{claim['id']}", headers=auth_headers(admin_token)).json()["data"]
    assert claim_check["status"] == "SETTLED"

    # cannot settle the same claim twice
    duplicate_settlement = client.post(f"/api/v1/claims/{claim['id']}/settle",
        json={"approved_amount": 75000.00}, headers=auth_headers(finance_officer_token))
    assert duplicate_settlement.status_code == 400