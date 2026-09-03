from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_finance_officer, require_any_role
from app.database import get_db
from app.models.settlement import SettlementStatus
from app.models.user import User
from app.schemas.settlement_schema import SettlementCreate, SettlementMessageResponse, SettlementPaginationResponse
from app.services.settlement_service import create_settlement, get_settlement_by_id, get_all_settlements

router = APIRouter(prefix="/api/v1", tags=["Settlement Management"])


@router.post("/claims/{claim_id}/settle", response_model=SettlementMessageResponse, status_code=status.HTTP_201_CREATED)
def settle_claim(claim_id: int, data: SettlementCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_finance_officer)):

    return create_settlement(claim_id, data, current_user, db)


@router.get("/settlements", response_model=SettlementPaginationResponse, dependencies=[Depends(require_any_role)])
def list_settlements(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), settlement_status: SettlementStatus | None = Query(None), db: Session = Depends(get_db)):

    return get_all_settlements(db, page, limit, settlement_status)


@router.get("/settlements/{id}", response_model=SettlementMessageResponse, dependencies=[Depends(require_any_role)])
def get_settlement(id: int, db: Session = Depends(get_db)):

    return get_settlement_by_id(id, db)