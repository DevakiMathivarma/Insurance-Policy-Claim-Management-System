from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_agent, require_any_role
from app.database import get_db
from app.models.user import User
from app.schemas.beneficiary_schema import BeneficiaryCreate, BeneficiaryUpdate, BeneficiaryMessageResponse, BeneficiaryListResponse
from app.schemas.common_schema import MessageResponse
from app.services.beneficiary_service import create_beneficiary, get_beneficiaries_for_policy, update_beneficiary, delete_beneficiary

router = APIRouter(prefix="/api/v1", tags=["Beneficiary Management"])


@router.post("/policies/{policy_id}/beneficiaries", response_model=BeneficiaryMessageResponse, status_code=status.HTTP_201_CREATED)
def add_beneficiary(policy_id: int, data: BeneficiaryCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return create_beneficiary(policy_id, data, current_user, db)


@router.get("/policies/{policy_id}/beneficiaries", response_model=BeneficiaryListResponse, dependencies=[Depends(require_any_role)])
def list_beneficiaries(policy_id: int, db: Session = Depends(get_db)):

    return get_beneficiaries_for_policy(policy_id, db)


@router.put("/beneficiaries/{beneficiary_id}", response_model=BeneficiaryMessageResponse)
def update_existing_beneficiary(beneficiary_id: int, data: BeneficiaryUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return update_beneficiary(beneficiary_id, data, current_user, db)


@router.delete("/beneficiaries/{beneficiary_id}", response_model=MessageResponse)
def remove_beneficiary(beneficiary_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return delete_beneficiary(beneficiary_id, current_user, db)