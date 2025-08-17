from typing import Dict

def calculate_shift_requirements_explanation(item_quantity: int,
                                             mold_cavity_standard: int,
                                             mold_setting_cycle: float,
                                             efficiency: float = 0.85,
                                             loss: float = 0.03) -> Dict[str, float]:
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

# Support feature_weight_calculator.py
def generate_confidence_report(confidence_scores,
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