from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_super_admin
from app.database import get_db
from app.schemas.dashboard_schema import (
    DashboardSummaryResponse, PolicyPremiumResponse, CustomerPolicyHistoryResponse, ClaimSettlementResponse,
    AgentPerformanceResponse, MonthlyPremiumCollectionResponse, MonthlyClaimStatisticsResponse,
    ClaimTypeBreakdownResponse, TopPayingCustomersResponse, PolicyStatusDistributionResponse
)
from app.services.dashboard_service import (
    get_dashboard_summary, get_policy_premium_report, get_customer_policy_history_report, get_claim_settlement_report,
    get_agent_performance_report, get_monthly_premium_collection_report, get_monthly_claim_statistics_report,
    get_claim_type_breakdown_report, get_top_paying_customers_report, get_policy_status_distribution_report,
    export_monthly_premium_collection_excel, export_agent_performance_excel, export_customer_policy_history_excel
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard & Reports"], dependencies=[Depends(require_super_admin)])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)


@router.get("/reports/policy-premium", response_model=PolicyPremiumResponse)
def policy_premium_report(db: Session = Depends(get_db)):
    return get_policy_premium_report(db)


@router.get("/reports/customer-policy-history", response_model=CustomerPolicyHistoryResponse)
def customer_policy_history_report(db: Session = Depends(get_db)):
    return get_customer_policy_history_report(db)


@router.get("/reports/claim-settlement", response_model=ClaimSettlementResponse)
def claim_settlement_report(db: Session = Depends(get_db)):
    return get_claim_settlement_report(db)


@router.get("/reports/agent-performance", response_model=AgentPerformanceResponse)
def agent_performance_report(db: Session = Depends(get_db)):
    return get_agent_performance_report(db)


@router.get("/reports/monthly-premium-collection", response_model=MonthlyPremiumCollectionResponse)
def monthly_premium_collection_report(db: Session = Depends(get_db)):
    return get_monthly_premium_collection_report(db)


@router.get("/reports/monthly-claim-statistics", response_model=MonthlyClaimStatisticsResponse)
def monthly_claim_statistics_report(db: Session = Depends(get_db)):
    return get_monthly_claim_statistics_report(db)


# --- bonus reports ---

@router.get("/reports/claim-type-breakdown", response_model=ClaimTypeBreakdownResponse)
def claim_type_breakdown_report(db: Session = Depends(get_db)):
    return get_claim_type_breakdown_report(db)


@router.get("/reports/top-paying-customers", response_model=TopPayingCustomersResponse)
def top_paying_customers_report(db: Session = Depends(get_db)):
    return get_top_paying_customers_report(db)


@router.get("/reports/policy-status-distribution", response_model=PolicyStatusDistributionResponse)
def policy_status_distribution_report(db: Session = Depends(get_db)):
    return get_policy_status_distribution_report(db)


# --- excel exports ---

@router.get("/reports/monthly-premium-collection/export")
def export_monthly_premium_collection(db: Session = Depends(get_db)):
    return export_monthly_premium_collection_excel(db)


@router.get("/reports/agent-performance/export")
def export_agent_performance(db: Session = Depends(get_db)):
    return export_agent_performance_excel(db)


@router.get("/reports/customer-policy-history/export")
def export_customer_policy_history(db: Session = Depends(get_db)):
    return export_customer_policy_history_excel(db)