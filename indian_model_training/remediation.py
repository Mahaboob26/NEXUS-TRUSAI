from typing import Dict, Any, List


def remediation_suggestions(input_data: Dict[str, Any], shap_info: Dict[str, Any]) -> List[str]:
    """Generate Indian banking-style remediation advice based on SHAP negative reasons.

    The function looks at the top negative SHAP features and tailors
    recommendations accordingly, so different applications get different
    guidance instead of a single generic message.
    """

    reasons = shap_info.get("top_negative") or []
    steps: List[str] = []

    loan_amount = float(input_data.get("LoanAmount", 0))
    loan_term = float(input_data.get("Loan_Amount_Term", 0) or 1)
    emi = loan_amount / loan_term
    applicant_income = float(input_data.get("ApplicantIncome", 0))
    co_income = float(input_data.get("CoapplicantIncome", 0))
    total_income = applicant_income + co_income
    credit_history = input_data.get("Credit_History")
    cibil_proxy = float(input_data.get("cibil_proxy_score", 0))
    bank_balance = float(input_data.get("bank_balance", 0))
    mobile_score = float(input_data.get("mobile_usage_score", 0))
    txn_score = float(input_data.get("transaction_stability_score", 0))
    credit_util = float(input_data.get("credit_utilization", 0))

    def add(msg: str):
        if msg not in steps:
            steps.append(msg)

    # Inspect top negative SHAP features and attach targeted actions
    for r in reasons:
        feature = (r.get("feature") or "").lower()

        if "loanamount" in feature or "emi" in feature or "income_to_emi" in feature:
            add(
                "Reduce the requested loan amount or opt for a longer tenure so that EMI is comfortably below 35–40% of your total family income."
            )
        elif "credit_history" in feature or "cibil_proxy" in feature:
            add(
                "Improve your credit history / CIBIL by paying EMIs on time, clearing overdues and avoiding cheque bounces for the next 6–12 months before reapplying."
            )
        elif "applicantincome" in feature or "coapplicantincome" in feature:
            add(
                "Declare all stable income sources and, if possible, add a salaried co-applicant or reduce the loan amount so that income better supports the EMI."
            )
        elif "bank_balance" in feature or "total_income" in feature:
            add(
                "Maintain a higher average balance and build a consistent savings pattern in your main account for a few months to show better liquidity."
            )
        elif "mobile_usage_score" in feature or "transaction_stability" in feature:
            add(
                "Keep your primary SIM active, avoid frequent number changes and ensure regular salary/business credits into the same account to strengthen behavioural scores."
            )
        elif "credit_utilization" in feature:
            add(
                "Reduce utilisation on existing credit cards and loans (ideally below 30–40% of limits) before taking additional borrowing."
            )

    # Additional rule-based checks for numeric thresholds
    if total_income > 0 and emi / max(total_income, 1) > 0.4:
        add(
            "Current EMI looks high versus income. Reducing ticket size or extending tenure so EMI/Income falls below ~35% will materially help."
        )

    if credit_history == 0 or cibil_proxy and cibil_proxy < 600:
        add(
            "Your risk score is in a weaker band. Focus on building 12 months of clean repayment behaviour and then request a re-evaluation."
        )

    if total_income and total_income < 40000:
        add(
            "For this loan size, income is on the lower side. A smaller loan amount or adding a strong co-applicant (with stable salary) can improve approval chances."
        )

    if bank_balance < 25000:
        add(
            "Increase average balance and avoid frequent full withdrawals. Keeping 1–3 months of EMI in the account strengthens your profile."
        )

    if mobile_score < 500 or txn_score < 500:
        add(
            "Use digital channels regularly (UPI, net banking), keep salary credits consistent and avoid long periods of inactivity in your main account."
        )

    if credit_util > 5:
        add(
            "Overall borrowing compared to your balances looks high. Try closing or consolidating some existing loans before applying again."
        )

    # Fallback generic suggestions if nothing matched
    if not steps:
        add(
            "Strengthen your profile by maintaining timely repayments, keeping credit utilisation moderate, and ensuring your income comfortably supports the requested EMI."
        )

    return steps[:6]

