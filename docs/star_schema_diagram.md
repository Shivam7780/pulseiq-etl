# PulseIQ Analytics Warehouse ? Star Schema Diagram

The diagram shows the enforced employee/date relationships in the current SQL schema. Department, role, and leave-type business identifiers in fact tables are not represented as enforced foreign keys.

```mermaid
erDiagram
    DIM_EMPLOYEE ||--o{ FACT_ATTENDANCE : employee
    DIM_DATE ||--o{ FACT_ATTENDANCE : date
    DIM_EMPLOYEE ||--o{ FACT_PAYROLL : employee
    DIM_DATE o|--o{ FACT_PAYROLL : date
    DIM_EMPLOYEE ||--o{ FACT_LEAVE : employee
    DIM_DATE o|--o{ FACT_LEAVE : start_date
    DIM_DATE o|--o{ FACT_LEAVE : end_date
    DIM_DATE ||--o{ FACT_HEADCOUNT_MONTHLY : month

    DIM_EMPLOYEE {
        bigint employee_key PK
        varchar employee_id
        date valid_from
        date valid_to
        boolean is_current
    }

    DIM_DEPARTMENT {
        bigint department_key PK
        varchar department_id UK
        varchar department_name
    }

    DIM_ROLE {
        bigint role_key PK
        varchar role_id UK
        varchar role_title
    }

    DIM_DATE {
        integer date_key PK
        date full_date UK
        integer year_number
        integer quarter_number
        integer month_number
    }

    DIM_LEAVE_TYPE {
        bigint leave_type_key PK
        varchar leave_type_code UK
        varchar leave_type_name
    }

    FACT_ATTENDANCE {
        varchar attendance_fact_id PK
        bigint employee_key FK
        integer date_key FK
        varchar department_id
        numeric scheduled_days
        numeric present_days
        numeric wfh_days
        numeric overtime_hours
        date period_end_date
    }

    FACT_PAYROLL {
        varchar payroll_item_id PK
        bigint employee_key FK
        integer date_key FK
        date period_end_date
        varchar department_id
        varchar role_id
        numeric gross_pay
        numeric net_pay
        numeric employer_cost
    }

    FACT_LEAVE {
        varchar leave_request_id PK
        bigint employee_key FK
        varchar leave_type_code
        integer start_date_key FK
        integer end_date_key FK
        date start_date
        date end_date
        numeric days
        varchar status
    }

    FACT_HEADCOUNT_MONTHLY {
        integer date_key PK, FK
        date month_start_date
        varchar department_id PK
        integer headcount_start
        integer hires
        integer exits
        integer voluntary_exits
        integer transfers_in
        integer transfers_out
        integer headcount_end
        numeric attrition_rate_monthly_pct
    }
```
