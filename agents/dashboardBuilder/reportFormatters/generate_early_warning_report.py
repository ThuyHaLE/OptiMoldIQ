import pandas as pd
from datetime import datetime
from typing import Dict

def generate_early_warning_report(unfinished_df: pd.DataFrame, 
                                  record_month: str,
                                  analysis_date: str,
                                  colored: bool = True,
                                  export_format: str = 'text',
                                  sort_by: str = 'severity') -> str:
    """
    Generate an Enhanced Early Warning Report from unfinished PO data.
    
    Parameters:
    -----------
    unfinished_df : pd.DataFrame
        DataFrame containing unfinished PO data
    colored : bool
        Enable color output for terminal (default: True)
    export_format : str
        Output format: 'text'
    sort_by : str
        Sort priority items by: 'severity', 'quantity', or 'date' (default: 'severity')
    
    Returns:
    --------
    str : Formatted report
    """
    
    # === Enhanced Color Palette with More Options ===
    if colored and export_format == 'text':
        C = {
            "reset": "\033[0m",
            "title": "\033[38;5;141m",
            "section": "\033[38;5;110m",
            "critical": "\033[38;5;203m",
            "high": "\033[38;5;214m",
            "medium": "\033[38;5;220m",
            "good": "\033[38;5;114m",
            "neutral": "\033[38;5;245m",
            "bold": "\033[1m",
            "underline": "\033[4m",
            "dim": "\033[2m"
        }
    else:
        C = {k: "" for k in ["reset", "title", "section", "critical", "high", "medium", "good", "neutral", "bold", "underline", "dim"]}
    
    # === Data Preparation ===
    required_cols = ['poNo', 'is_backlog', 'itemCodeName', 'itemRemainQuantity',
                     'is_overdue', 'poStatus', 'etaStatus', 'overAvgCapacity', 'overTotalCapacity',
                     'capacityWarning', 'capacitySeverity']
    
    # Check for optional columns
    optional_cols = ['poRLT', 'poDate', 'poETA', 'customerName', 'itemCode']
    available_cols = required_cols + [col for col in optional_cols if col in unfinished_df.columns]
    
    df = unfinished_df[available_cols].copy()
    
    # Calculate additional metrics
    if 'poRLT' in df.columns:
        df['days_remaining'] = df['poRLT'].apply(lambda x: x.days if pd.notna(x) else None)
    
    # === Report Header ===
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    text = _generate_text_report(df, 
                                 record_month, 
                                 analysis_date.strftime("%Y-%m-%d"), 
                                 C, 
                                 timestamp, 
                                 sort_by)
    
    return text

def _generate_text_report(df: pd.DataFrame, 
                          record_month: str,
                          analysis_date: str,
                          C: Dict, 
                          timestamp: str, 
                          sort_by: str) -> str:
    """Generate text-based report with colors"""
    
    text = ""
    text += f"\n{C['title']}{'='*110}{C['reset']}\n"
    text += f"{C['bold']}{C['title']}{' '*40}🚨 EARLY WARNING REPORT 🚨{C['reset']}\n"
    text += f"{C['dim']}Generated warining early report for {record_month} | Analysis date: {analysis_date}{' '*75}{C['reset']}\n"
    text += f"{C['dim']}Generated date: {timestamp}{' '*75}{C['reset']}\n"
    text += f"{C['title']}{'='*110}{C['reset']}\n"
    
    # === EXECUTIVE SUMMARY ===
    total_pos = len(df)
    critical_count = (df['capacitySeverity'] == 'critical').sum()
    high_count = (df['capacitySeverity'] == 'high').sum()
    medium_count = (df['capacitySeverity'] == 'medium').sum() if 'medium' in df['capacitySeverity'].values else 0
    overdue_count = df['is_overdue'].sum()
    backlog_count = df['is_backlog'].sum()
    capacity_warning_count = df['capacityWarning'].sum()
    
    total_remaining = df['itemRemainQuantity'].sum()
    critical_remaining = df[df['capacitySeverity'] == 'critical']['itemRemainQuantity'].sum()
    
    text += f"\n{C['section']}{C['bold']}📊 EXECUTIVE SUMMARY{C['reset']}\n"
    text += f"{C['section']}{'─'*110}{C['reset']}\n"
    text += f"   {C['bold']}Total Active POs:{C['reset']} {total_pos:,} orders\n"
    text += f"   {C['bold']}Total Remaining Quantity:{C['reset']} {total_remaining:,.0f} units\n\n"
    
    text += f"   {C['bold']}Severity Breakdown:{C['reset']}\n"
    critical_pct = (critical_count/total_pos*100) if total_pos > 0 else 0
    high_pct = (high_count/total_pos*100) if total_pos > 0 else 0
    
    text += f"   ├─ 🔥 Critical: {C['critical']}{C['bold']}{critical_count:>4}{C['reset']} ({critical_pct:>5.1f}%) - {critical_remaining:>12,.0f} units\n"
    text += f"   ├─ ⚠️  High:     {C['high']}{C['bold']}{high_count:>4}{C['reset']} ({high_pct:>5.1f}%)\n"
    if medium_count > 0:
        text += f"   ├─ ⚡ Medium:   {C['medium']}{C['bold']}{medium_count:>4}{C['reset']} ({medium_count/total_pos*100:>5.1f}%)\n"
    text += f"   └─ ✓  Normal:   {C['good']}{total_pos - critical_count - high_count - medium_count:>4}{C['reset']}\n\n"
    
    text += f"   {C['bold']}Status Indicators:{C['reset']}\n"
    text += f"   ├─ ⏰ Overdue:          {C['neutral']}{overdue_count:>4}{C['reset']} ({overdue_count/total_pos*100:>5.1f}%)\n"
    text += f"   ├─ 📦 Backlog:          {C['neutral']}{backlog_count:>4}{C['reset']} ({backlog_count/total_pos*100:>5.1f}%)\n"
    text += f"   └─ 🚨 Capacity Warning: {C['section']}{capacity_warning_count:>4}{C['reset']} ({capacity_warning_count/total_pos*100:>5.1f}%)\n"
    
    # Risk Score
    risk_score = (critical_count * 10 + high_count * 5 + overdue_count * 3 + backlog_count * 2)
    risk_level = "🔴 CRITICAL" if risk_score > 100 else "🟡 HIGH" if risk_score > 50 else "🟢 MODERATE"
    text += f"\n   {C['bold']}Overall Risk Score:{C['reset']} {risk_score} - {risk_level}\n"
    
    # === PRIORITY SECTIONS ===
    text += _generate_priority_section(df, C, 1, "CRITICAL SEVERITY + OVERDUE", 
                                      (df['capacitySeverity'] == 'critical') & (df['is_overdue'] == True),
                                      'critical', sort_by)
    
    text += _generate_priority_section(df, C, 2, "CRITICAL SEVERITY (Not Overdue)", 
                                      (df['capacitySeverity'] == 'critical') & (df['is_overdue'] == False),
                                      'high', sort_by)
    
    text += _generate_priority_section(df, C, 3, "OVERDUE + BACKLOG", 
                                      (df['is_overdue'] == True) & (df['is_backlog'] == True),
                                      'section', sort_by)
    
    text += _generate_priority_section(df, C, 4, "HIGH SEVERITY (Approaching Limit)", 
                                      df['capacitySeverity'] == 'high',
                                      'high', sort_by, top_n=15)
    
    # === CAPACITY ANALYSIS ===
    if 'overAvgCapacity' in df.columns and 'overTotalCapacity' in df.columns:
        text += f"\n{C['section']}{C['bold']}{'='*110}\n📈 CAPACITY ANALYSIS\n{'='*110}{C['reset']}\n"
        
        over_avg = (df['overAvgCapacity'] == True).sum()
        over_total = (df['overTotalCapacity'] == True).sum()
        
        text += f"   POs exceeding average capacity: {C['high']}{over_avg}{C['reset']} ({over_avg/total_pos*100:.1f}%)\n"
        text += f"   POs exceeding total capacity:   {C['critical']}{over_total}{C['reset']} ({over_total/total_pos*100:.1f}%)\n"
        
        if over_total > 0:
            text += f"\n   {C['critical']}⚠️  WARNING: {over_total} POs exceed total production capacity!{C['reset']}\n"
    
    # === ACTIONABLE INSIGHTS ===
    text += f"\n{C['title']}{C['bold']}{'='*110}\n💡 ACTIONABLE INSIGHTS & RECOMMENDATIONS\n{'='*110}{C['reset']}\n"
    
    recommendations = []
    if critical_count > 0:
        recommendations.append(f"🔥 {C['critical']}URGENT:{C['reset']} Immediate escalation required for {critical_count} critical POs ({critical_remaining:,.0f} units)")
    if overdue_count > 0:
        recommendations.append(f"⏰ Contact customers for {overdue_count} overdue POs - negotiate revised ETAs")
    if backlog_count > 0:
        recommendations.append(f"📦 Prioritize clearing {backlog_count} backlog items to free up capacity")
    if high_count > 0:
        recommendations.append(f"⚠️  Monitor {high_count} high-severity POs daily - may become critical soon")
    
    capacity_risk_pos = df[df['overTotalCapacity'] == True]
    if len(capacity_risk_pos) > 0:
        recommendations.append(f"🏭 Review production schedule - {len(capacity_risk_pos)} POs exceed total capacity")
    
    # Add time-based recommendations if RLT is available
    if 'days_remaining' in df.columns:
        urgent_timeline = df[df['days_remaining'] <= 3]
        if len(urgent_timeline) > 0:
            recommendations.append(f"⏱️  {len(urgent_timeline)} POs have ≤3 days remaining - expedite processing")
    
    for i, rec in enumerate(recommendations, 1):
        text += f"   {i}. {rec}\n"
    
    if not recommendations:
        text += f"   {C['good']}✅ All metrics within acceptable ranges - maintain current monitoring{C['reset']}\n"
    
    # === FOOTER ===
    text += f"\n{C['neutral']}{'='*110}{C['reset']}\n"
    text += f"{C['dim']}Report end - For detailed PO analysis, filter by priority level or severity{C['reset']}\n"
    text += f"{C['neutral']}{'='*110}{C['reset']}\n"

    return text


def _generate_priority_section(df: pd.DataFrame, C: Dict, priority: int, title: str, 
                               condition, color_key: str, sort_by: str = 'severity', 
                               top_n: int = None) -> str:
    """Generate a priority section with enhanced formatting"""
    
    icons = {1: "🔥", 2: "⚠️ ", 3: "📦", 4: "⚡"}
    icon = icons.get(priority, "•")
    
    text = f"\n{C[color_key]}{C['bold']}{'='*110}\n{icon} PRIORITY {priority}: {title}\n{'='*110}{C['reset']}\n"
    
    priority_df = df[condition]
    
    if len(priority_df) > 0:
        total_qty = priority_df['itemRemainQuantity'].sum()
        text += f"   {C['bold']}Count:{C['reset']} {len(priority_df)} POs | {C['bold']}Total Remaining:{C['reset']} {total_qty:,.0f} units\n"
        
        # Sort logic
        if sort_by == 'quantity':
            priority_df = priority_df.sort_values('itemRemainQuantity', ascending=False)
        elif sort_by == 'date' and 'days_remaining' in priority_df.columns:
            priority_df = priority_df.sort_values('days_remaining', ascending=True)
        
        # Display limit
        display_df = priority_df.head(top_n) if top_n else priority_df
        
        text += f"\n   {C['dim']}{'─'*110}{C['reset']}\n"
        text += f"   {C['underline']}{'PO Number':<15} {'Item':<45} {'Remaining':>15} {'Status':<30}{C['reset']}\n"
        text += f"   {C['dim']}{'─'*110}{C['reset']}\n"
        
        for _, row in display_df.iterrows():
            status_tags = []
            if row['is_overdue']:
                status_tags.append(f"{C['critical']}OVERDUE{C['reset']}")
            if row['is_backlog']:
                status_tags.append(f"{C['neutral']}BACKLOG{C['reset']}")
            if 'days_remaining' in row and pd.notna(row['days_remaining']):
                status_tags.append(f"{row['days_remaining']:.0f}d left")
            
            status_str = " | ".join(status_tags)
            
            text += f"   • {C['bold']}{row['poNo']:<15}{C['reset']} "
            text += f"{row['itemCodeName'][:43]:<45} "
            text += f"{C[color_key]}{row['itemRemainQuantity']:>13,.0f}{C['reset']} u  "
            text += f"{status_str}\n"
        
        if top_n and len(priority_df) > top_n:
            text += f"\n   {C['dim']}... and {len(priority_df) - top_n} more POs{C['reset']}\n"
    else:
        text += f"   {C['good']}✅ No POs in this category{C['reset']}\n"
    
    return text