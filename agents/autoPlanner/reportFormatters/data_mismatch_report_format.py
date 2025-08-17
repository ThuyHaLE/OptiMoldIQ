import pandas as pd
from datetime import datetime

def generate_data_mismatch_report(data_dict):

    """
    Generate a mismatch report as a list of strings to join with '\n'
    
    Args:
        data_dict: Dictionary containing mismatch data
    
    Returns:
        List of lines to be joined with '\n'
    """
    
    lines = []
    
    # Header
    lines.extend([
        "=" * 80, 
        "MISMATCH ANALYSIS REPORT".center(80),
        "=" * 80,
        f"Creation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ])
    
    # Overall statistics
    total_issues = 0
    po_count = set()
    
    for category, subcategories in data_dict.items():
        if isinstance(subcategories, dict):
            for subcat, df in subcategories.items():
                if isinstance(df, pd.DataFrame):
                    total_issues += len(df)
                    if 'poNo' in df.columns:
                        po_count.update(df['poNo'].unique())
    
    # Overview section
    lines.extend([
        "OVERVIEW",
        "-" * 20,
        f"Total issues: {total_issues}",
        f"Affected POs: {len(po_count)}",
        f"PO List: {', '.join(sorted(po_count)) if po_count else 'None'}",
        ""
    ])
    
    # Details for each category
    for category, subcategories in data_dict.items():
        if isinstance(subcategories, dict):
            lines.extend([
                f"CATEGORY: {category.upper()}",
                "=" * 50
            ])
            
            for subcat, df in subcategories.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    lines.extend([
                        f"{subcat.replace('_', ' ').title()}",
                        "-" * 30
                    ])
                    
                    # Subcategory statistics
                    lines.append(f"Issue count: {len(df)}")
                    
                    if 'warningType' in df.columns:
                        lines.append(f"Warning types: {df['warningType'].nunique()}")
                    
                    if 'mismatchType' in df.columns:
                        lines.append(f"Mismatch types: {df['mismatchType'].nunique()}")
                    
                    if 'poNo' in df.columns:
                        affected_pos = df['poNo'].unique()
                        lines.extend([
                            f"Affected POs: {len(affected_pos)}",
                            f"PO List: {', '.join(affected_pos)}"
                        ])
                    
                    lines.append("")
                    
                    # Record details
                    lines.append("Details:")
                    for idx, row in df.iterrows():
                        details = []
                        if 'poNo' in row:
                            details.append(f"PO: {row['poNo']}")
                        if 'warningType' in row:
                            details.append(f"Warning: {row['warningType']}")
                        if 'mismatchType' in row:
                            details.append(f"Mismatch: {row['mismatchType']}")
                        if 'requiredAction' in row:
                            details.append(f"Action: {row['requiredAction']}")
                        
                        lines.append(f"  • {' | '.join(details)}")
                    
                    lines.append("")
                    
                    # Breakdown by warning type
                    if 'warningType' in df.columns:
                        warning_counts = df['warningType'].value_counts()
                        lines.append("Breakdown by warning type:")
                        for warning_type, count in warning_counts.items():
                            lines.append(f"  • {warning_type}: {count}")
                        lines.append("")
                    
                    # Breakdown by required action
                    if 'requiredAction' in df.columns:
                        action_counts = df['requiredAction'].value_counts()
                        lines.append("Required actions:")
                        for action, count in action_counts.items():
                            action_short = action[:60] + "..." if len(action) > 60 else action
                            lines.append(f"  • {action_short}: {count}")
                        lines.append("")
    
    # Recommendations
    lines.extend([
        "RECOMMENDATIONS",
        "=" * 20
    ])
    
    recommendations = []
    
    if 'po_required_mismatch' in data_dict:
        recommendations.append("🚨 URGENT: Some POs were produced incorrectly - immediate process halt required")
    
    if 'dynamic_mismatch' in data_dict and 'invalid_items' in data_dict['dynamic_mismatch']:
        invalid_items = data_dict['dynamic_mismatch']['invalid_items']
        if not invalid_items.empty:
            recommendations.append("⚠️ Update Item Composition Summary for invalid items")
    
    if 'static_mismatch' in data_dict:
        recommendations.append("🔍 Review and update information in Purchase Orders and Product Records")
    
    recommendations.extend([
        "📊 Perform regular audits to detect mismatches early",
        "🔄 Establish automated validation processes",
        "📝 Update documentation for all validation procedures"
    ])
    
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec}")
    
    return lines