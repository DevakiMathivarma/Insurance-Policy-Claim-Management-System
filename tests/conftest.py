import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_celery_tasks(monkeypatch):
    # every service does a LOCAL import inside its function body
    # (from app.tasks import send_x_email, called right where it's used,
    # not at the top of the file) - this means patching the attribute on
    # the service module does nothing, since each call re-imports the
    # real task fresh from app.tasks. the mock has to target app.tasks
    # itself, where the real task objects actually live.
    class FakeDelay:
        def delay(self, *args, **kwargs):
            return None
    fake_task = FakeDelay()
    task_names = [
        "send_policy_activation_email", "send_premium_payment_success_email", "send_premium_due_reminder_email",
        "send_premium_overdue_email", "send_claim_submission_email", "send_documents_required_email",
        "send_claim_decision_email", "send_claim_settlement_email", "send_policy_expiry_email"
    ]
    for task_name in task_names:
        monkeypatch.setattr(f"app.tasks.{task_name}", fake_task, raising=False)


@pytest.fixture(autouse=True)
def mock_redis_cache(monkeypatch):
    fake_store = {}
    def fake_set_cache(key, value, expire=None):
        fake_store[key] = value
        return True
    def fake_get_cache(key):
        return fake_store.get(key)
    def fake_delete_cache(key):
        fake_store.pop(key, None)
        return True
    for module_path in ["app.services.customer_service", "app.services.plan_service", "app.services.policy_service"]:
        for name, fake in [("set_cache", fake_set_cache), ("get_cache", fake_get_cache), ("delete_cache", fake_delete_cache)]:
            try:
                monkeypatch.setattr(f"{module_path}.{name}", fake)
            except AttributeError:
                pass


@pytest.fixture(autouse=True)
def mock_documents(monkeypatch):
    monkeypatch.setattr("app.services.policy_service.generate_policy_document_pdf", lambda **kwargs: "fake_policy.pdf", raising=False)
    monkeypatch.setattr("app.services.payment_service.generate_policy_document_pdf", lambda **kwargs: "fake_policy.pdf", raising=False)
    monkeypatch.setattr("app.services.settlement_service.generate_settlement_letter_pdf", lambda **kwargs: "fake_settlement.pdf", raising=False)


@pytest.fixture(autouse=True)
def mock_websocket_broadcast(monkeypatch):
    monkeypatch.setattr("app.services.claim_service.broadcast_claim_status_sync", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr("app.services.settlement_service.broadcast_claim_status_sync", lambda *args, **kwargs: None, raising=False)


@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch):
    # the rate_limit() factory runs once at app startup and its inner
    # function is permanently baked into the route, so patching the
    # factory itself does nothing. instead, patch redis_client.get so
    # every request looks like the very first one, which never triggers
    # a 429 - the exact fix learned from the property platform's ci failure
    monkeypatch.setattr("app.utils.rate_limit.redis_client.get", lambda key: None)


@pytest.fixture
def admin_token(client, db_session) -> str:
    from app.models.user import User, UserRole
    from app.utils.hashing import hash_password

    admin = db_session.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if not admin:
        admin = User(full_name="Test Admin", email="admin@example.com", phone="9000000000",
            password_hash=hash_password("Admin@12345"), role=UserRole.SUPER_ADMIN, is_active=True)
        db_session.add(admin)
        db_session.commit()

    response = client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": "Admin@12345"})
    return response.json()["access_token"]


@pytest.fixture
def agent_token(client, admin_token) -> str:
    client.post("/api/v1/auth/register",
        json={"full_name": "Test Agent", "email": "agent@test.com", "phone": "9111111111", "password": "Test@1234", "role": "INSURANCE_AGENT"},
        headers={"Authorization": f"Bearer {admin_token}"})
    response = client.post("/api/v1/auth/login", data={"username": "agent@test.com", "password": "Test@1234"})
    return response.json()["access_token"]


@pytest.fixture
def claims_officer_token(client, admin_token) -> str:
    client.post("/api/v1/auth/register",
        json={"full_name": "Test Claims", "email": "claims@test.com", "phone": "9222222222", "password": "Test@1234", "role": "CLAIMS_OFFICER"},
        headers={"Authorization": f"Bearer {admin_token}"})
    response = client.post("/api/v1/auth/login", data={"username": "claims@test.com", "password": "Test@1234"})
    return response.json()["access_token"]


@pytest.fixture
def finance_officer_token(client, admin_token) -> str:
    client.post("/api/v1/auth/register",
        json={"full_name": "Test Finance", "email": "finance@test.com", "phone": "9333333333", "password": "Test@1234", "role": "FINANCE_OFFICER"},
        headers={"Authorization": f"Bearer {admin_token}"})
    response = client.post("/api/v1/auth/login", data={"username": "finance@test.com", "password": "Test@1234"})
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}