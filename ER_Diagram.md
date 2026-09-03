# ER Diagram — Insurance Policy & Claim Management System

This diagram shows all 11 tables and how they connect. GitHub renders this
automatically when viewing this file in a repository — no separate image or
tool needed. Full field lists for every table are in `app/models/` and the
Alembic migration file.

```mermaid
erDiagram
    USER ||--o| CUSTOMER : "has profile"
    USER ||--o{ AUDIT_LOG : "performs (optional)"
    USER ||--o{ POLICY : "sells as agent (optional)"

    CUSTOMER ||--o{ POLICY : "purchases"
    CUSTOMER ||--o{ CLAIM : "files"

    PLAN ||--o{ POLICY : "sold as"

    POLICY ||--o{ BENEFICIARY : "names"
    POLICY ||--o{ PAYMENT : "collects"
    POLICY ||--o{ CLAIM : "covered under"
    POLICY ||--o| POLICY : "renews from (optional)"

    CLAIM ||--o{ CLAIM_DOCUMENT : "attaches"
    CLAIM ||--o| CLAIM_ASSESSMENT : "evaluated by"
    CLAIM ||--o| SETTLEMENT : "settled by"

    USER {
        int id PK
        string full_name
        string email UK
        string phone UK
        string password_hash
        enum role
        bool is_active
    }

    CUSTOMER {
        int id PK
        int user_id FK
        date date_of_birth
        string address
        string identification_number UK
        string occupation
        int created_by_user_id FK
    }

    PLAN {
        int id PK
        string plan_name
        enum plan_type
        decimal coverage_amount
        decimal premium_amount
        int duration_years
        int eligibility_age_min
        int eligibility_age_max
        enum status
    }

    POLICY {
        int id PK
        string policy_number UK
        int customer_id FK
        int plan_id FK
        int agent_id FK
        date start_date
        date end_date
        decimal coverage_amount
        decimal premium_amount
        date next_premium_due_date
        enum policy_status
        int renewed_from_policy_id FK
    }

    BENEFICIARY {
        int id PK
        int policy_id FK
        string name
        string relationship_type
        decimal percentage
        string phone
        string identification_number
    }

    PAYMENT {
        int id PK
        int policy_id FK
        decimal amount
        datetime payment_date
        enum payment_method
        string transaction_id UK
        enum status
    }

    CLAIM {
        int id PK
        string claim_number UK
        int policy_id FK
        int customer_id FK
        string claim_type
        date incident_date
        decimal claim_amount
        enum status
    }

    CLAIM_DOCUMENT {
        int id PK
        int claim_id FK
        enum document_type
        string file_name
        string file_path
        datetime uploaded_at
        enum verification_status
        int verified_by_user_id FK
    }

    CLAIM_ASSESSMENT {
        int id PK
        int claim_id FK "unique"
        int assessor_id FK
        decimal eligible_amount
        string assessment_notes
        string recommendation
        datetime assessed_at
    }

    SETTLEMENT {
        int id PK
        int claim_id FK "unique"
        decimal approved_amount
        datetime settlement_date
        string payment_reference
        enum settlement_status
        int processed_by_user_id FK
    }

    AUDIT_LOG {
        int id PK
        int user_id FK
        string action
        string entity_type
        int entity_id
        string description
    }
```

---

## Relationships explained 

- **One User can have one Customer profile** — the only role in this project
  with real extra fields beyond a login account. Insurance Agent, Claims
  Officer, and Finance Officer stay flat login accounts.
- **One User (an Insurance Agent) can sell many Policies** — but a Policy's
  `agent_id` is optional, so this survives even if an agent's account is later
  removed.
- **One Customer can purchase many Policies and file many Claims.**
- **One Plan can be sold as many Policies** over time — but each Policy locks
  in its own `coverage_amount`/`premium_amount` at the moment of purchase, so
  changing the Plan afterward never silently affects existing policyholders.
- **One Policy branches into several things:** many Beneficiaries (who must
  together total exactly 100%), many Payments, many Claims, and optionally
  points back to the **older Policy it was renewed from** — the one
  genuinely self-referencing relationship in this whole schema.
- **One Claim branches into three things, each with a different shape:** many
  Documents (a real list), at most **one** Assessment, and at most **one**
  Settlement (both enforced by a real `unique=True` constraint on `claim_id`,
  not just application logic).
- **Audit Log entries optionally point back to whichever User performed the
  action** — optional because the log entry should still exist even if that
  user's account is later removed.

## How to view this diagram

- **On GitHub:** just open this file in your repository — it renders
  automatically, no setup needed.
- **Locally, before pushing:** paste the code block above (without the triple
  backticks) into [mermaid.live](https://mermaid.live) to preview it instantly.