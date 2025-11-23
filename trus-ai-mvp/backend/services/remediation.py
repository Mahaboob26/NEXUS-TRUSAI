from typing import List, Dict, Any


REMEDIATION_TEMPLATES = {
    "duration": "Consider choosing a shorter duration or demonstrating stability over a longer period to reduce perceived risk.",
    "amount": "Reducing the requested credit amount or providing additional collateral can improve approval chances.",
    "age": "Building a longer credit history and maintaining timely repayments can strengthen your profile.",
    "checking_status": "Improving your current account balance and avoiding overdrafts will support better decisions.",
    "credit_history": "Maintaining on-time payments and avoiding recent defaults will improve your credit history.",
}


def generate_remediation_steps(
    negative_reasons: List[Dict[str, Any]],
) -> List[str]:
    """Given top SHAP negative reasons, return human-friendly remediation steps."""

    steps: List[str] = []
    for item in negative_reasons:
        feature = item.get("feature") or ""
        text = None
        for key, template in REMEDIATION_TEMPLATES.items():
            if key in feature:
                text = template
                break
        if text is None:
            text = (
                f"Try to improve the underlying factor '{feature}' by lowering risk "
                f"(e.g., reducing debt, increasing income stability, or adding collateral)."
            )
        if text not in steps:
            steps.append(text)

    if not steps:
        steps.append(
            "Maintain good repayment behavior, keep overall debt manageable, and ensure your income can comfortably cover obligations."
        )

    return steps

