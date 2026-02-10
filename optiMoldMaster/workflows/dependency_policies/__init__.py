# optiMoldMaster/workflows/dependency_policies/__init__.py

from typing import Dict, Any, List, Type
from optiMoldMaster.workflows.dependency_policies.base import DependencyPolicy
from optiMoldMaster.workflows.dependency_policies.strict import StrictWorkflowPolicy
from optiMoldMaster.workflows.dependency_policies.flexible import FlexibleDependencyPolicy
from optiMoldMaster.workflows.dependency_policies.hybrid import HybridDependencyPolicy

# ------------------------------------------------------------------
# Policy registry with schemas
# ------------------------------------------------------------------

class PolicySchema:
    """Schema definition for a dependency policy."""
    
    def __init__(
        self,
        policy_class: Type[DependencyPolicy],
        required_params: List[str] = None,
        optional_params: Dict[str, Any] = None,
        description: str = ""
    ):
        self.policy_class = policy_class
        self.required_params = set(required_params or [])
        self.optional_params = optional_params or {}
        self.description = description
    
    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate params against schema.
        
        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        provided = set(params.keys())
        
        # Check required params
        missing = self.required_params - provided
        if missing:
            errors.append(f"Missing required parameters: {missing}")
        
        # Check unknown params
        all_valid = self.required_params | set(self.optional_params.keys())
        unknown = provided - all_valid
        if unknown:
            errors.append(f"Unknown parameters: {unknown}")
        
        # Type validation (optional)
        for param_name, param_value in params.items():
            if param_name in self.optional_params:
                expected_type = self.optional_params[param_name].get('type')
                if expected_type and not isinstance(param_value, expected_type):
                    warnings.append(
                        f"Parameter '{param_name}' type mismatch: "
                        f"expected {expected_type.__name__}, got {type(param_value).__name__}"
                    )
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for optional params."""
        return {
            name: spec.get('default')
            for name, spec in self.optional_params.items()
            if 'default' in spec
        }


# ------------------------------------------------------------------
# Registry with schemas
# ------------------------------------------------------------------

POLICY_SCHEMAS = {
    "strict": PolicySchema(
        policy_class=StrictWorkflowPolicy,
        required_params=[],
        optional_params={},
        description="All dependencies must be in current workflow"
    ),
    
    "flexible": PolicySchema(
        policy_class=FlexibleDependencyPolicy,
        required_params=[],  # All params are optional
        optional_params={
            'required_deps': {
                'type': list,
                'default': None,
                'description': 'List of dependency names that must exist'
            },
            'max_age_days': {
                'type': int,
                'default': None,
                'description': 'Maximum age in days for database dependencies'
            }
        },
        description="Flexible policy with configurable required dependencies"
    ),
    
    "hybrid": PolicySchema(
        policy_class=HybridDependencyPolicy,
        required_params=[],  # All params are optional
        optional_params={
            'max_age_days': {
                'type': int,
                'default': None,
                'description': 'Maximum age in days for database fallback'
            },
            'prefer_workflow': {
                'type': bool,
                'default': True,
                'description': 'Whether to warn when using database instead of workflow'
            }
        },
        description="Hybrid policy: prefer workflow, fallback to database with age check"
    ),
}

# Backward compatible - simple class lookup
AVAILABLE_POLICIES = {
    "strict": StrictWorkflowPolicy,
    "flexible": FlexibleDependencyPolicy,
    "hybrid": HybridDependencyPolicy,
    "StrictWorkflowPolicy": StrictWorkflowPolicy,
    "FlexibleDependencyPolicy": FlexibleDependencyPolicy,
    "HybridDependencyPolicy": HybridDependencyPolicy,
}

__all__ = [
    "DependencyPolicy",
    "StrictWorkflowPolicy",
    "FlexibleDependencyPolicy",
    "HybridDependencyPolicy",
    "AVAILABLE_POLICIES",
    "POLICY_SCHEMAS",
    "PolicySchema",
]