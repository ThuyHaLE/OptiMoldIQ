from loguru import logger
import pandas as pd
from typing import Dict, Any
from loguru import logger
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.utils import save_output_with_versioning
from pathlib import Path
import pandas as pd

def save_validatation_data(save_routing: Dict[str, Any],
                           validation_dir: Path | str,
                           filename_prefix: str) -> str:

    # Extract validation data
    validation_data = extract_validation_data(save_routing)

    if (
        validation_data['combined_all']['po_mismatch_warnings'].empty
        and validation_data['combined_all']['item_invalid_warnings'].empty
        ):
        logger.warning("No mismatches were found during validation, skipping save")
        
        return "No mismatches were found during validation, skipping save"
    
    # Generate validation summary
    reporter = DictBasedReportGenerator(use_colors=False)
    validation_summary = "\n".join(reporter.export_report(validation_data))
    
    # Export results to Excel
    logger.info("📤 Exporting results to Excel...")
    export_log = save_output_with_versioning(
        data=validation_data['combined_all'],
        output_dir=validation_dir,
        filename_prefix=filename_prefix,
        report_text=validation_summary
    )
    logger.info("✅ Results exported successfully!")

    return export_log

def extract_validation_data(save_routing: Dict
                            ) -> Dict[str, Any]:
    
    """Extract validation data from save_routing."""
    
    static_data = save_routing.get(
        "StaticCrossDataValidation", {}).get(
            'phase_result', {}).get(
                'result', {})
    po_data = save_routing.get(
        "PORequiredFieldValidation", {}).get(
            'phase_result', {}).get(
                'result', {})
    dynamic_data = save_routing.get(
        "DynamicCrossDataValidation", {}).get(
            'phase_result', {}).get(
                'result', {})
    
    # Combine results
    return combine_validation_results(static_data, po_data, dynamic_data)

def combine_validation_results(static_data: Dict[str, Any],
                               po_data: Any,
                               dynamic_data: Dict[str, Any]
                               ) -> Dict[str, Any]:
    
    """Combine results from all validation processes."""
    
    static_mismatch_warnings_purchase = static_data.get('purchaseOrders', pd.DataFrame())
    static_mismatch_warnings_product = static_data.get('productRecords', pd.DataFrame())
    po_required_mismatch_warnings = po_data if isinstance(po_data, pd.DataFrame) else pd.DataFrame()
    dynamic_invalid_warnings = dynamic_data.get('invalid_warnings', pd.DataFrame())
    dynamic_mismatch_warnings = dynamic_data.get('mismatch_warnings', pd.DataFrame())
    
    final_df = pd.concat([
        dynamic_mismatch_warnings,
        static_mismatch_warnings_purchase,
        static_mismatch_warnings_product,
        po_required_mismatch_warnings
    ], ignore_index=True)
    
    return {
        'static_mismatch': {
            'purchaseOrders': static_mismatch_warnings_purchase,
            'productRecords': static_mismatch_warnings_product
        },
        'po_required_mismatch': po_required_mismatch_warnings,
        'dynamic_mismatch': {
            'invalid_items': dynamic_invalid_warnings,
            'info_mismatches': dynamic_mismatch_warnings
        },
        'combined_all': {
            'po_mismatch_warnings': final_df,
            'item_invalid_warnings': dynamic_invalid_warnings
        }
    }