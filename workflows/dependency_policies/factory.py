# workflows/dependency_policies/factory.py

from typing import Dict, Any
from loguru import logger
from workflows.dependency_policies import (
    AVAILABLE_POLICIES, 
    POLICY_SCHEMAS
)

class DependencyPolicyFactory:
    """Factory with schema-based validation."""

    @staticmethod
    def create(policy_cfg):
        if policy_cfg is None:
            return None

        # Format 1: String
        if isinstance(policy_cfg, str):
            return DependencyPolicyFactory._create_from_string(policy_cfg)

        # Format 2: Dict
        if isinstance(policy_cfg, dict):
            return DependencyPolicyFactory._create_from_dict(policy_cfg)

        raise TypeError(
            f"Invalid dependency_policy type: {type(policy_cfg)}. "
            f"Expected str or dict."
        )

    @staticmethod
    def _create_from_string(policy_name: str):
        """Create policy from string with defaults."""
        
        if policy_name not in AVAILABLE_POLICIES:
            available = list(AVAILABLE_POLICIES.keys())
            raise ValueError(
                f"Unknown dependency policy: '{policy_name}'. "
                f"Available: {available}"
            )
        
        policy_cls = AVAILABLE_POLICIES[policy_name]
        return policy_cls()

    @staticmethod
    def _create_from_dict(policy_cfg: Dict[str, Any]):
        """Create policy from dict with schema validation."""
        
        # Validate structure
        if "name" not in policy_cfg:
            raise ValueError(
                f"Missing 'name' field in dependency_policy: {policy_cfg}"
            )
        
        name = policy_cfg["name"]
        params = policy_cfg.get("params", {})
        
        # Check policy exists
        if name not in POLICY_SCHEMAS:
            available = list(POLICY_SCHEMAS.keys())
            raise ValueError(
                f"Unknown dependency policy: '{name}'. "
                f"Available: {available}"
            )
        
        # Validate params against schema
        schema = POLICY_SCHEMAS[name]
        validation = schema.validate_params(params)
        
        if not validation['valid']:
            errors = "\n".join(f"  - {e}" for e in validation['errors'])
            raise ValueError(
                f"Invalid params for policy '{name}':\n{errors}\n"
                f"Schema: required={schema.required_params}, "
                f"optional={list(schema.optional_params.keys())}"
            )
        
        # Log warnings
        for warning in validation['warnings']:
            logger.warning(f"Policy '{name}': {warning}")
        
        # Create instance
        try:
            policy_cls = schema.policy_class
            return policy_cls(**params)
        except TypeError as e:
            raise ValueError(
                f"Failed to instantiate policy '{name}' with params {params}: {e}"
            ) from e

    @staticmethod
    def get_schema(policy_name: str) -> Dict[str, Any]:
        """
        Get schema documentation for a policy.
        
        Returns:
            {
                'description': str,
                'required_params': List[str],
                'optional_params': Dict[str, schema_spec]
            }
        """
        if policy_name not in POLICY_SCHEMAS:
            raise ValueError(f"Unknown policy: {policy_name}")
        
        schema = POLICY_SCHEMAS[policy_name]
        return {
            'description': schema.description,
            'required_params': list(schema.required_params),
            'optional_params': schema.optional_params,
            'defaults': schema.get_defaults()
        }

    @staticmethod
    def list_policies() -> Dict[str, str]:
        """List all available policies with descriptions."""
        return {
            name: schema.description
            for name, schema in POLICY_SCHEMAS.items()
        }