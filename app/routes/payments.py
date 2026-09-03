
# app/routes/payments.py

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_any_role
from app.database import get_db
from app.models.payment import PaymentMethod, PaymentStatus
from app.models.user import User
from app.schemas.payment_schema import PaymentCreate, PaymentMessageResponse, PaymentPaginationResponse
from app.services.payment_service import create_payment, get_payment_by_id, get_all_payments, get_payments_for_policy

router = APIRouter(prefix="/api/v1", tags=["Premium Payment Management"])


@router.post("/policies/{policy_id}/premium-payment", response_model=PaymentMessageResponse, status_code=status.HTTP_201_CREATED)
def pay_premium(policy_id: int, data: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return create_payment(policy_id, data, current_user, db)


@router.get("/payments", response_model=PaymentPaginationResponse, dependencies=[Depends(require_any_role)])
def list_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    payment_status: PaymentStatus | None = Query(None),
    payment_method: PaymentMethod | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: Session = Depends(get_db)
):

    return get_all_payments(db=db, page=page, limit=limit, payment_status=payment_status, payment_method=payment_method, start_date=start_date, end_date=end_date)


@router.get("/payments/{payment_id}", response_model=PaymentMessageResponse, dependencies=[Depends(require_any_role)])
def get_payment(payment_id: int, db: Session = Depends(get_db)):

    return get_payment_by_id(payment_id, db)


@router.get("/policies/{policy_id}/payments", response_model=PaymentPaginationResponse, dependencies=[Depends(require_any_role)])
def list_policy_payments(policy_id: int, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):

    return get_payments_for_policy(policy_id, db, page, limit)