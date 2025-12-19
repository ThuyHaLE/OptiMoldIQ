import pandas as pd
from typing import Literal, Dict, Union
from loguru import logger

def suggest_weights_standard_based(
        good_hist_df: pd.DataFrame,
        bad_hist_df: pd.DataFrame,
        targets: Dict[str, Union[float, str]],
        scaling: Literal['absolute', 'relative'] = 'absolute'
        ) -> Dict[str, float]:

    """
    Suggests weights based on standard method without confidence consideration.

    Args:
        good_hist_df: Good performance data
        bad_hist_df: Bad performance data
        targets: Dict mapping feature names to target values or 'minimize'
        scaling: 'absolute' or 'relative' scaling method

    Returns:
        Dictionary of normalized weights (sum = 1)
    """

    # Get list of features
    features = list(targets.keys())

    # Validate inputs
    if not features:
        logger.error("Features list cannot be empty")
        raise ValueError("Features list cannot be empty")
    if scaling not in ['absolute', 'relative']:
        logger.error("Scaling must be 'absolute' or 'relative'")
        raise ValueError("Scaling must be 'absolute' or 'relative'")

    # Calculate raw weights
    weights = {}
    for feature in features:
        if feature not in good_hist_df.columns or feature not in bad_hist_df.columns:
            logger.info(f"Warning: Feature '{feature}' not found in data. Setting weight to 0.")
            weights[feature] = 0
            continue

        # Calculate means
        mean_good = good_hist_df[feature].mean() if len(good_hist_df) > 0 else 0
        mean_bad = bad_hist_df[feature].mean() if len(bad_hist_df) > 0 else 0
        if pd.isna(mean_good):
            mean_good = 0
        if pd.isna(mean_bad):
            mean_bad = 0

        # Calculate score based on target
        if targets[feature] == 'minimize':
            # For metrics like NG rate: lower is better
            deviation_good = abs(mean_good)  # deviation from 0
            deviation_bad = abs(mean_bad)
            score = abs(deviation_bad - deviation_good)
        else:
            # For metrics with target values: closer to target is better
            target = targets[feature]
            deviation_good = abs(mean_good - target)
            deviation_bad = abs(mean_bad - target)
            score = abs(deviation_bad - deviation_good)

        # Apply scaling
        if scaling == 'relative':
            if targets[feature] == 'minimize':
                # Avoid division by zero
                denominator = max(abs(mean_good), abs(mean_bad), 0.001)
                score /= denominator
            else:
                score /= max(abs(targets[feature]), 0.001)

        # Assign score to weights
        weights[feature] = score

    # Normalize weights to sum to 1
    total = sum(weights.values())
    if total == 0:
        # If all scores are 0, assign equal weights
        return {k: 1 / len(weights) for k in weights}

    return {k: v / total for k, v in weights.items()}