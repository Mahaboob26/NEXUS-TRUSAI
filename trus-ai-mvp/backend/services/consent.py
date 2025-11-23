from typing import Dict, Any, Iterable


def apply_consent(
    input_data: Dict[str, Any],
    consent_flags: Dict[str, bool],
    numeric_features: Iterable[str],
    categorical_features: Iterable[str],
) -> Dict[str, Any]:
    """Apply consent by masking fields the user denied.

    Instead of dropping columns (which would break the trained pipeline),
    we set denied numeric fields to 0 and denied categorical fields to
    a neutral "missing" token. This effectively removes their influence
    while keeping the feature schema intact.
    """

    result: Dict[str, Any] = {}

    for feature, value in input_data.items():
        allowed = consent_flags.get(feature, True)
        if not allowed:
            if feature in numeric_features:
                result[feature] = 0
            elif feature in categorical_features:
                result[feature] = "missing"
            else:
                result[feature] = None
        else:
            result[feature] = value

    return result

