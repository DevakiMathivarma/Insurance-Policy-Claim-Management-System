from datetime import date
from decimal import Decimal

from app.schemas.common_schema import AppBaseSchema


# --- summary - the 10 single-number metrics from level 13's own list ---


class DashboardSummary(AppBaseSchema):
    total_customers: int
    active_policies: int
    expired_policies: int
    total_premium_collected: Decimal
    pending_premium: Decimal
    total_claims: int
    approved_claims: int
    rejected_claims: int
    pending_claims: int
    total_settlement_amount: Decimal


class DashboardSummaryResponse(AppBaseSchema):
    message: str
    data: DashboardSummary


# --- the 6 named reports from level 13's own list ---


class PolicyPremiumEntry(AppBaseSchema):
    policy_id: int
    policy_number: str
    customer_name: str
    plan_name: str
    premium_amount: Decimal
    policy_status: str


class PolicyPremiumResponse(AppBaseSchema):
    message: str
    data: list[PolicyPremiumEntry]


class CustomerPolicyHistoryEntry(AppBaseSchema):
    customer_id: int
    customer_name: str
    total_policies: int
    total_premium_paid: Decimal


class CustomerPolicyHistoryResponse(AppBaseSchema):
    message: str
    data: list[CustomerPolicyHistoryEntry]


class ClaimSettlementEntry(AppBaseSchema):
    claim_id: int
    claim_number: str
    customer_name: str
    approved_amount: Decimal
    settlement_date: str | None
    settlement_status: str


class ClaimSettlementResponse(AppBaseSchema):
    message: str
    data: list[ClaimSettlementEntry]


class AgentPerformanceEntry(AppBaseSchema):
    agent_id: int
    agent_name: str
    total_policies_sold: int
    total_premium_generated: Decimal


class AgentPerformanceResponse(AppBaseSchema):
    message: str
    data: list[AgentPerformanceEntry]


class MonthlyPremiumCollectionEntry(AppBaseSchema):
    month: str
    total_collected: Decimal


class MonthlyPremiumCollectionResponse(AppBaseSchema):
    message: str
    data: list[MonthlyPremiumCollectionEntry]


class MonthlyClaimStatisticsEntry(AppBaseSchema):
    month: str
    total_claims: int
    total_claim_amount: Decimal


class MonthlyClaimStatisticsResponse(AppBaseSchema):
    message: str
    data: list[MonthlyClaimStatisticsEntry]


# --- bonus reports - beyond the task's own list ---


class ClaimTypeBreakdownEntry(AppBaseSchema):
    claim_type: str
    claim_count: int
    total_amount: Decimal


class ClaimTypeBreakdownResponse(AppBaseSchema):
    message: str
    data: list[ClaimTypeBreakdownEntry]


class TopPayingCustomerEntry(AppBaseSchema):
    customer_id: int
    customer_name: str
    total_paid: Decimal


class TopPayingCustomersResponse(AppBaseSchema):
    message: str
    data: list[TopPayingCustomerEntry]


class PolicyStatusDistributionEntry(AppBaseSchema):
    status: str
    count: int


class PolicyStatusDistributionResponse(AppBaseSchema):
    message: str
    data: list[PolicyStatusDistributionEntry]