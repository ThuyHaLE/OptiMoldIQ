import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Union, Optional
from agents.utils import log_dict_as_table
from loguru import logger

def calculate_feature_confidence_scores(
        good_hist_df: pd.DataFrame,
        bad_hist_df: pd.DataFrame,
        targets: Dict[str, Union[float, str]],
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95,
        min_sample_size: int = 10,
        sample_size_threshold: int = 50
        ) -> Dict[str, Dict[str, float]]:

    """
    Calculate confidence scores for each feature based on good and bad performance groups.

    Args:
        good_hist_df (pd.DataFrame): DataFrame of the good performance group.
        bad_hist_df (pd.DataFrame): DataFrame of the bad performance group.
        features (List[str]): List of features to analyze.
        targets (Dict[str, Union[float, str]]): Dictionary specifying target values for each feature.
        n_bootstrap (int): Number of bootstrap iterations (default: 1000).
        confidence_level (float): Desired confidence level (default: 0.95).
        min_sample_size (int): Minimum required sample size for valid confidence computation.

    Returns:
        Dict[str, Dict[str, float]]: A dictionary containing confidence scores and statistics per feature.
    """

    results = {}
    alpha = 1 - confidence_level

    features = list(targets.keys())
    for feature in features:
        if feature not in good_hist_df.columns or feature not in bad_hist_df.columns:
            results[feature] = {
                'good_confidence': 0.0,
                'bad_confidence': 0.0,
                'separation_confidence': 0.0,
                'sample_size_good': 0,
                'sample_size_bad': 0,
                'warning': f'Feature {feature} not found in data'
            }
            continue

        # Drop NaN values from both groups
        good_data = good_hist_df[feature].dropna()
        bad_data = bad_hist_df[feature].dropna()

        sample_size_good = len(good_data)
        sample_size_bad = len(bad_data)

        # Check for minimum sample size
        if sample_size_good < min_sample_size or sample_size_bad < min_sample_size:
            results[feature] = {
                'good_confidence': 0.5,  # Neutral confidence
                'bad_confidence': 0.5,
                'separation_confidence': 0.0,
                'sample_size_good': sample_size_good,
                'sample_size_bad': sample_size_bad,
                'warning': f'Sample size too small (good: {sample_size_good}, bad: {sample_size_bad})'
            }
            continue

        # Bootstrap sampling to estimate distributions
        good_bootstrap_means = []
        bad_bootstrap_means = []

        np.random.seed(42)  # For reproducibility

        for _ in range(n_bootstrap):
            good_sample = np.random.choice(good_data, size=min(len(good_data), 
                                                                sample_size_threshold), replace=True)
            bad_sample = np.random.choice(bad_data, size=min(len(bad_data), 
                                                                sample_size_threshold), replace=True)
            good_bootstrap_means.append(np.mean(good_sample))
            bad_bootstrap_means.append(np.mean(bad_sample))

        good_bootstrap_means = np.array(good_bootstrap_means)
        bad_bootstrap_means = np.array(bad_bootstrap_means)

        # Confidence intervals
        good_ci_lower = np.percentile(good_bootstrap_means, (alpha / 2) * 100)
        good_ci_upper = np.percentile(good_bootstrap_means, (1 - alpha / 2) * 100)
        bad_ci_lower = np.percentile(bad_bootstrap_means, (alpha / 2) * 100)
        bad_ci_upper = np.percentile(bad_bootstrap_means, (1 - alpha / 2) * 100)

        # Target-based confidence scoring
        target_value = targets[feature]

        if target_value == 'minimize':
            # Smaller is better
            good_target_achievement = np.mean(good_bootstrap_means < np.mean(bad_bootstrap_means))
            bad_target_achievement = np.mean(bad_bootstrap_means > np.mean(good_bootstrap_means))

            good_distance_from_ideal = np.mean(np.abs(good_bootstrap_means))
            bad_distance_from_ideal = np.mean(np.abs(bad_bootstrap_means))
        else:
            # Closer to the target is better
            good_distance_from_target = np.mean(np.abs(good_bootstrap_means - target_value))
            bad_distance_from_target = np.mean(np.abs(bad_bootstrap_means - target_value))

            good_target_achievement = np.mean(
                np.abs(good_bootstrap_means - target_value) <
                np.abs(bad_bootstrap_means - target_value)
            )
            bad_target_achievement = 1 - good_target_achievement

            good_distance_from_ideal = good_distance_from_target
            bad_distance_from_ideal = bad_distance_from_target

        # Separation confidence using CI overlap
        overlap = max(0, min(good_ci_upper, bad_ci_upper) - max(good_ci_lower, bad_ci_lower))
        total_range = max(good_ci_upper, bad_ci_upper) - min(good_ci_lower, bad_ci_lower)
        separation_confidence = 1 - (overlap / max(total_range, 0.001))

        # Statistical test (Mann-Whitney U) to detect significant difference
        try:
            stat, p_value = stats.mannwhitneyu(good_data, bad_data, alternative='two-sided')
            statistical_significance = 1 - p_value
        except:
            statistical_significance = 0.5

        # Final confidence score calculations
        good_confidence = (
            good_target_achievement * 0.4 +
            separation_confidence * 0.3 +
            statistical_significance * 0.2 +
            (1 / (1 + good_distance_from_ideal)) * 0.1
        )
        bad_confidence = (
            bad_target_achievement * 0.4 +
            separation_confidence * 0.3 +
            statistical_significance * 0.2 +
            (1 / (1 + bad_distance_from_ideal)) * 0.1
        )

        # Ensure within [0, 1]
        good_confidence = max(0, min(1, good_confidence))
        bad_confidence = max(0, min(1, bad_confidence))

        results[feature] = {
            'good_confidence': round(good_confidence, 3),
            'bad_confidence': round(bad_confidence, 3),
            'separation_confidence': round(separation_confidence, 3),
            'statistical_significance': round(statistical_significance, 3),
            'sample_size_good': sample_size_good,
            'sample_size_bad': sample_size_bad,
            'good_mean': round(np.mean(good_data), 4),
            'bad_mean': round(np.mean(bad_data), 4),
            'good_ci_lower': round(good_ci_lower, 4),
            'good_ci_upper': round(good_ci_upper, 4),
            'bad_ci_lower': round(bad_ci_lower, 4),
            'bad_ci_upper': round(bad_ci_upper, 4),
            'p_value': round(1 - statistical_significance, 4) if statistical_significance != 0.5 else 0.5
        }

    return results

def calculate_overall_confidence(
        confidence_scores: Dict[str, Dict[str, float]],
        feature_weights: Optional[Dict[str, float]] = None
        ) -> Dict[str, float]:

    """
    Calculate overall confidence scores by aggregating individual feature confidence scores.

    Args:
        confidence_scores: Output from calculate_confidence_scores()
        feature_weights: Weights for each feature (optional)

    Returns:
        Dict with overall confidence scores
    """

    if not confidence_scores:
        return {'overall_good_confidence': 0.0, 'overall_bad_confidence': 0.0, 'model_reliability': 0.0}

    # Use equal weights if none are provided
    if feature_weights is None:
        feature_weights = {feature: 1.0 for feature in confidence_scores.keys()}

    # Normalize weights
    total_weight = sum(feature_weights.values())
    if total_weight > 0:
        feature_weights = {k: v / total_weight for k, v in feature_weights.items()}

    good_confidences = []
    bad_confidences = []
    separation_confidences = []
    valid_features = 0

    for feature, scores in confidence_scores.items():
        if 'warning' not in scores:
            weight = feature_weights.get(feature, 1.0)
            good_confidences.append(scores['good_confidence'] * weight)
            bad_confidences.append(scores['bad_confidence'] * weight)
            separation_confidences.append(scores['separation_confidence'] * weight)
            valid_features += 1

    if valid_features == 0:
        return {'overall_good_confidence': 0.0, 'overall_bad_confidence': 0.0, 'model_reliability': 0.0}

    overall_good_confidence = sum(good_confidences)
    overall_bad_confidence = sum(bad_confidences)
    overall_separation = sum(separation_confidences)

    # Model reliability based on separation and the number of valid features
    model_reliability = overall_separation * (valid_features / len(confidence_scores))

    logger.info("Model Reliability: {:.1%}", model_reliability)
    logger.info("Good Group Confidence: {:.1%}", overall_good_confidence)
    logger.info("Bad Group Confidence: {:.1%}", overall_bad_confidence)

    results = {
            'overall_good_confidence': round(overall_good_confidence, 3),
            'overall_bad_confidence': round(overall_bad_confidence, 3),
            'overall_separation_confidence': round(overall_separation, 3),
            'model_reliability': round(model_reliability, 3),
            'valid_features_ratio': round(valid_features / len(confidence_scores), 3),
            'total_features': len(confidence_scores),
            'valid_features': valid_features
            }

    # Diplay
    logger.debug('Overall confidence score: \n{}', log_dict_as_table(results, transpose = False))

    return results

def calculate_shift_requirements_explanation(
        item_quantity: int,
        mold_cavity_standard: int,
        mold_setting_cycle: float,
        efficiency: float,
        loss: float) -> Dict[str, float]:
    
    """
    Detailed explanation of how `moldEstimatedShiftUsed` is calculated.

    Args:
        item_quantity: The total number of items to produce
        mold_cavity_standard: The standard cavity count of the mold
        mold_setting_cycle: The standard mold cycle time (in seconds)
        efficiency: Machine efficiency (e.g., 85% = 0.85)
        loss: Loss due to NG (defects) and setup time (e.g., 3% = 0.03)

    Returns:
        A dictionary containing detailed calculation parameters
    """
    
    # Step 1: Calculate the required number of shots (theoretical)
    total_shots_needed = item_quantity / mold_cavity_standard

    # Step 2: Calculate total theoretical time (in seconds)
    total_seconds_theory = total_shots_needed * mold_setting_cycle

    # Step 3: Calculate theoretical number of shifts (1 shift = 8 hours = 28,800 seconds)
    theoretical_shifts = total_seconds_theory / (8 * 60 * 60)

    # Step 4: Calculate actual net efficiency
    net_efficiency = efficiency - loss  # e.g., 0.85 - 0.03 = 0.82 (82%)

    # Step 5: Estimate the actual number of shifts required
    # Because the net efficiency is only 82%, more time is needed than in theory
    estimated_shifts = theoretical_shifts / net_efficiency

    return {
        'item_quantity': item_quantity,
        'mold_cavity_standard': mold_cavity_standard,
        'mold_setting_cycle_seconds': mold_setting_cycle,
        'total_shots_needed': total_shots_needed,
        'total_seconds_theory': total_seconds_theory,
        'theoretical_shifts': theoretical_shifts,
        'efficiency_percent': efficiency * 100,
        'loss_percent': loss * 100,
        'net_efficiency_percent': net_efficiency * 100,
        'estimated_shifts_needed': estimated_shifts,
        'efficiency_factor': 1 / net_efficiency,
        'additional_time_percent': ((estimated_shifts / theoretical_shifts) - 1) * 100
    }

def generate_confidence_report(
        confidence_scores,
        overall_confidence) -> str:
    
    """
    Generate a detailed confidence report.
    """

    report = "=== CONFIDENCE ANALYSIS REPORT ===\n\n"

    report += "=== EXAMPLE: SHIFT REQUIREMENTS CALCULATION ===\n"

    example_calc = calculate_shift_requirements_explanation(
        item_quantity=10000,      # Need to produce 10,000 items
        mold_cavity_standard=4,   # Mold has 4 cavities
        mold_setting_cycle=30,    # 30 seconds per shot
        efficiency=0.85,          # 85% efficiency
        loss=0.03                 # 3% loss
    )

    for key, value in example_calc.items():
        if isinstance(value, float):
            report += f"{key}: {value:.2f}\n"
        else:
            report += f"{key}: {value}\n"

    report += (
        f"\nConclusion: With actual efficiency of {example_calc['net_efficiency_percent']:.0f}%, "
        f"an additional {example_calc['additional_time_percent']:.1f}% time is needed compared to theory.\n\n"
    )

    report += "=== OVERALL SUMMARY ===\n"
    report += f"Overall Model Reliability: {overall_confidence['model_reliability']:.1%}\n"
    report += f"Valid Features: {overall_confidence['valid_features']}/{overall_confidence['total_features']}\n"
    report += f"Overall Good Group Confidence: {overall_confidence['overall_good_confidence']:.1%}\n"
    report += f"Overall Bad Group Confidence: {overall_confidence['overall_bad_confidence']:.1%}\n\n"

    report += "=== FEATURE ANALYSIS ===\n"
    for feature, scores in confidence_scores.items():
        report += f"\n{feature.upper()}:\n"

        if 'warning' in scores:
            report += f"⚠️ WARNING: {scores['warning']}\n"
            continue

        report += f"  Sample sizes: Good={scores['sample_size_good']}, Bad={scores['sample_size_bad']}\n"
        report += f"  Means: Good={scores['good_mean']:.4f}, Bad={scores['bad_mean']:.4f}\n"
        report += f"  Confidence: Good={scores['good_confidence']:.1%}, Bad={scores['bad_confidence']:.1%}\n"
        report += f"  Separation: {scores['separation_confidence']:.1%}\n"
        report += f"  Statistical significance: {scores['statistical_significance']:.1%} (p={scores['p_value']:.4f})\n"

        # Interpretation
        if scores['separation_confidence'] > 0.7:
            report += "✅ Strong separation between groups\n"
        elif scores['separation_confidence'] > 0.4:
            report += "⚠️ Moderate separation between groups\n"
        else:
            report += "❌ Weak separation between groups\n"

    report += "\nMain Functions Used: \n"
    report += "1. get_hist_info() - Analyze historical performance\n"
    report += "2. group_hist_by_performance() - Classify good/bad POs\n"
    report += "3. suggest_weights_standard_based() - Suggest weights\n"
    report += "4. calculate_shift_requirements_explanation() - Shift calculation explanation\n"
    report += "5. calculate_confidence_scores() - Bootstrap-based confidence analysis\n"
    report += "6. suggest_weights_with_confidence() - Confidence-aware weights\n"
    report += "7. generate_confidence_report() - Generate detailed confidence report"

    return report