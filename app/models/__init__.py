# app/models/__init__.py

# importing every model here ensures they're all registered with
# SQLAlchemy's mapper registry before any mapper configuration happens -
# without this, Base.metadata has no tables registered, and Alembic's
# autogenerate finds nothing to create, same root cause behind the
# property platform's MaintenanceStaffProfile bug
from app.models.user import User
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.policy import Policy
from app.models.beneficiary import Beneficiary
from app.models.payment import Payment
from app.models.claim import Claim
from app.models.claim_document import ClaimDocument
from app.models.claim_assessment import ClaimAssessment
from app.models.settlement import Settlement
from app.models.audit_log import AuditLog