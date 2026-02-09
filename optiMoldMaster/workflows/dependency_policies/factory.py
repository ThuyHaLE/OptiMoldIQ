# optiMoldMaster/workflows/dependency_policies/factory.py

from optiMoldMaster.workflows.dependency_policies import AVAILABLE_POLICIES

class DependencyPolicyFactory:
    """
    policy_cfg schema: 
    e.g: 
    "dependency_policy": {
        "name": "hybrid",
        "params": {
            "required_deps": ["pipeline"],
            "max_age_days": 7
            }
        }
    """

    @staticmethod
    def create(policy_cfg):
        if policy_cfg is None:
            return None

        # Backward compatibility: string
        if isinstance(policy_cfg, str):
            policy_cls = AVAILABLE_POLICIES.get(policy_cfg)
            if not policy_cls:
                raise ValueError(f"Unknown dependency policy: {policy_cfg}")
            return policy_cls()

        # Object form
        if isinstance(policy_cfg, dict):
            name = policy_cfg.get("name")
            params = policy_cfg.get("params", {})

            if name not in AVAILABLE_POLICIES:
                raise ValueError(f"Unknown dependency policy: {name}")
            
            try:
                return AVAILABLE_POLICIES[name](**params)
            except TypeError as e:
                raise ValueError(
                    f"Invalid params for dependency policy '{name}': {params}"
                ) from e

        raise TypeError(f"Invalid dependency_policy config: {policy_cfg}")