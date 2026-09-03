from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_admin_or_claims_officer, require_any_role
from app.database import get_db
from app.models.claim import ClaimStatus
from app.models.user import User
from app.schemas.claim_schema import ClaimCreate, ClaimUpdate, ClaimMessageResponse, ClaimPaginationResponse
from app.services.claim_service import create_claim, get_claim_by_id, get_all_claims, update_claim, submit_claim, approve_claim, reject_claim
from app.auth.permissions import require_admin_or_claims_officer
from app.schemas.claim_assessment_schema import ClaimAssessmentCreate, ClaimAssessmentMessageResponse
from app.services.claim_assessment_service import create_assessment, get_assessment_for_claim


router = APIRouter(prefix="/api/v1/claims", tags=["Claim Management"])


@router.post("", response_model=ClaimMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_claim(data: ClaimCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return create_claim(data, current_user, db)


@router.get("", response_model=ClaimPaginationResponse, dependencies=[Depends(require_any_role)])
def list_claims(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    claim_status: ClaimStatus | None = Query(None),
    claim_type: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    min_amount: Decimal | None = Query(None),
    max_amount: Decimal | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_claims(
        db=db, page=page, limit=limit, claim_status=claim_status, claim_type=claim_type,
        start_date=start_date, end_date=end_date, min_amount=min_amount, max_amount=max_amount, sort_by=sort_by, sort_order=sort_order
    )


@router.get("/{claim_id}", response_model=ClaimMessageResponse, dependencies=[Depends(require_any_role)])
def get_claim(claim_id: int, db: Session = Depends(get_db)):

    return get_claim_by_id(claim_id, db)


@router.put("/{claim_id}", response_model=ClaimMessageResponse)
def update_existing_claim(claim_id: int, data: ClaimUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return update_claim(claim_id, data, current_user, db)


@router.post("/{claim_id}/submit", response_model=ClaimMessageResponse)
def submit_existing_claim(claim_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return submit_claim(claim_id, current_user, db)


@router.post("/{claim_id}/approve", response_model=ClaimMessageResponse, dependencies=[Depends(require_admin_or_claims_officer)])
def approve_existing_claim(claim_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_claims_officer)):

    return approve_claim(claim_id, current_user, db)


@router.post("/{claim_id}/reject", response_model=ClaimMessageResponse, dependencies=[Depends(require_admin_or_claims_officer)])
def reject_existing_claim(claim_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_claims_officer)):

    return reject_claim(claim_id, current_user, db)



@router.post("/{claim_id}/assessment", response_model=ClaimAssessmentMessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_or_claims_officer)])
def create_claim_assessment(claim_id: int, data: ClaimAssessmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_claims_officer)):

    return create_assessment(claim_id, data, current_user, db)


@router.get("/{claim_id}/assessment", response_model=ClaimAssessmentMessageResponse, dependencies=[Depends(require_any_role)])
def get_claim_assessment(claim_id: int, db: Session = Depends(get_db)):

    return get_assessment_for_claim(claim_id, db)