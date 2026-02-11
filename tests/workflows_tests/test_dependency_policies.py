# tests/workflows_tests/test_dependency_policies.py

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from workflows.dependency_policies.base import (
    DependencyPolicy,
    DependencyValidationResult,
    DependencyIssue,
    DependencyReason,
    DependencySource
)
from workflows.dependency_policies.strict import StrictWorkflowPolicy
from workflows.dependency_policies.flexible import FlexibleDependencyPolicy
from workflows.dependency_policies.hybrid import HybridDependencyPolicy
from workflows.dependency_policies.factory import DependencyPolicyFactory
from workflows.dependency_policies import POLICY_SCHEMAS, PolicySchema


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_dependencies():
    """Sample dependencies mapping"""
    return {
        "mesh_data": "/data/meshes/part_001.stl",
        "material_props": "/data/materials/ABS.json",
        "simulation_config": "/data/configs/thermal.yaml"
    }


@pytest.fixture
def workflow_modules():
    """Sample workflow modules"""
    return ["mesh_data", "material_props"]


@pytest.fixture
def mock_filesystem(tmp_path):
    """Create mock filesystem with files of different ages"""
    # Recent file (1 day old)
    recent_file = tmp_path / "recent.stl"
    recent_file.write_text("recent data")
    recent_time = datetime.now() - timedelta(days=1)
    
    # Old file (10 days old)
    old_file = tmp_path / "old.json"
    old_file.write_text("old data")
    old_time = datetime.now() - timedelta(days=10)
    
    # Set modification times (Note: this is platform dependent)
    import os
    os.utime(str(recent_file), (recent_time.timestamp(), recent_time.timestamp()))
    os.utime(str(old_file), (old_time.timestamp(), old_time.timestamp()))
    
    return {
        "recent": str(recent_file),
        "old": str(old_file),
        "missing": str(tmp_path / "missing.yaml")
    }


# ============================================================================
# BASE POLICY TESTS
# ============================================================================

class TestDependencyValidationResult:
    """Test DependencyValidationResult dataclass"""
    
    def test_empty_result_is_valid(self):
        result = DependencyValidationResult()
        assert result.valid is True
        assert result.has_errors() is False
        assert result.has_warnings() is False
        assert result.should_block() is False
    
    def test_result_with_errors_is_invalid(self):
        errors = {
            "dep1": DependencyIssue(
                dep_name="dep1",
                reason=DependencyReason.NOT_FOUND,
                required=True
            )
        }
        result = DependencyValidationResult(errors=errors)
        assert result.valid is False
        assert result.has_errors() is True
        assert result.should_block() is True
    
    def test_result_with_warnings_only_is_valid(self):
        warnings = {
            "dep1": DependencyIssue(
                dep_name="dep1",
                reason=DependencyReason.TOO_OLD,
                required=False
            )
        }
        result = DependencyValidationResult(warnings=warnings)
        assert result.valid is True
        assert result.has_warnings() is True
        assert result.should_block() is False
    
    def test_summary(self):
        result = DependencyValidationResult(
            errors={
                "dep1": DependencyIssue(
                    dep_name="dep1",
                    reason=DependencyReason.NOT_FOUND,
                    source=DependencySource.DATABASE
                )
            },
            warnings={
                "dep2": DependencyIssue(
                    dep_name="dep2",
                    reason=DependencyReason.TOO_OLD,
                    source=DependencySource.DATABASE
                )
            },
            resolved={
                "dep3": DependencySource.WORKFLOW
            }
        )
        
        summary = result.summary()
        assert summary["valid"] is False
        assert summary["errors"]["dep1"] == "not_found"
        assert summary["warnings"]["dep2"] == "too_old"
        assert summary["resolved"]["dep3"] == "workflow"


class TestDependencyIssue:
    """Test DependencyIssue dataclass"""
    
    def test_to_dict(self):
        issue = DependencyIssue(
            dep_name="mesh_data",
            reason=DependencyReason.TOO_OLD,
            source=DependencySource.DATABASE,
            required=True,
            metadata={"age_days": 15}
        )
        
        data = issue.to_dict()
        assert data["dep_name"] == "mesh_data"
        assert data["reason"] == "too_old"
        assert data["source"] == "database"
        assert data["required"] is True
        assert data["metadata"]["age_days"] == 15


# ============================================================================
# STRICT POLICY TESTS
# ============================================================================

class TestStrictWorkflowPolicy:
    """Test StrictWorkflowPolicy"""
    
    def test_all_dependencies_in_workflow(self, sample_dependencies, workflow_modules):
        policy = StrictWorkflowPolicy()
        
        # Only check deps that are in workflow
        deps_to_check = {k: v for k, v in sample_dependencies.items() if k in workflow_modules}
        
        result = policy.validate(deps_to_check, workflow_modules)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.resolved) == 2
        assert result.resolved["mesh_data"] == DependencySource.WORKFLOW
        assert result.resolved["material_props"] == DependencySource.WORKFLOW
    
    def test_missing_dependency_causes_error(self, sample_dependencies, workflow_modules):
        policy = StrictWorkflowPolicy()
        
        result = policy.validate(sample_dependencies, workflow_modules)
        
        assert result.valid is False
        assert "simulation_config" in result.errors
        assert result.errors["simulation_config"].reason == DependencyReason.WORKFLOW_VIOLATION
        assert result.errors["simulation_config"].required is True
    
    def test_empty_workflow_all_errors(self, sample_dependencies):
        policy = StrictWorkflowPolicy()
        
        result = policy.validate(sample_dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert len(result.errors) == 3
        for dep_name in sample_dependencies.keys():
            assert dep_name in result.errors
            assert result.errors[dep_name].reason == DependencyReason.WORKFLOW_VIOLATION
    
    def test_no_dependencies(self):
        policy = StrictWorkflowPolicy()
        
        result = policy.validate({}, workflow_modules=["module1"])
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.resolved) == 0


# ============================================================================
# FLEXIBLE POLICY TESTS
# ============================================================================

class TestFlexibleDependencyPolicy:
    """Test FlexibleDependencyPolicy"""
    
    def test_no_required_deps_all_optional(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(required_deps=None, max_age_days=None)
        
        dependencies = {
            "recent": mock_filesystem["recent"],
            "missing": mock_filesystem["missing"]
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should be valid since all deps are optional
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1  # missing is warning only
        assert "missing" in result.warnings
        assert result.warnings["missing"].reason == DependencyReason.NOT_FOUND
    
    def test_required_dep_found_in_workflow(self):
        policy = FlexibleDependencyPolicy(required_deps=["mesh_data"])
        
        dependencies = {"mesh_data": "/some/path.stl"}
        workflow_modules = ["mesh_data"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert "mesh_data" in result.resolved
        assert result.resolved["mesh_data"] == DependencySource.WORKFLOW
    
    def test_required_dep_missing_causes_error(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(required_deps=["critical_data"])
        
        dependencies = {"critical_data": mock_filesystem["missing"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "critical_data" in result.errors
        assert result.errors["critical_data"].required is True
    
    def test_age_constraint_required_dep(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(
            required_deps=["old_data"],
            max_age_days=5
        )
        
        dependencies = {"old_data": mock_filesystem["old"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "old_data" in result.errors
        assert result.errors["old_data"].reason == DependencyReason.TOO_OLD
        assert result.errors["old_data"].required is True
    
    def test_age_constraint_optional_dep(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(
            required_deps=[],
            max_age_days=5
        )
        
        dependencies = {"old_data": mock_filesystem["old"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should be valid but with warning
        assert result.valid is True
        assert "old_data" in result.warnings
        assert result.warnings["old_data"].reason == DependencyReason.TOO_OLD
        assert result.warnings["old_data"].required is False
    
    def test_recent_file_passes_age_check(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(
            required_deps=["recent_data"],
            max_age_days=5
        )
        
        dependencies = {"recent_data": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "recent_data" in result.resolved
        assert result.resolved["recent_data"] == DependencySource.DATABASE
    
    def test_mixed_required_and_optional(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(required_deps=["dep1"])
        
        dependencies = {
            "dep1": mock_filesystem["recent"],  # required, exists
            "dep2": mock_filesystem["missing"]  # optional, missing
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "dep1" in result.resolved
        assert "dep2" in result.warnings
        assert result.warnings["dep2"].required is False


# ============================================================================
# HYBRID POLICY TESTS
# ============================================================================

class TestHybridDependencyPolicy:
    """Test HybridDependencyPolicy"""
    
    def test_workflow_preferred_no_fallback(self):
        policy = HybridDependencyPolicy(prefer_workflow=True)
        
        dependencies = {"mesh_data": "/some/path.stl"}
        workflow_modules = ["mesh_data"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert "mesh_data" in result.resolved
        assert result.resolved["mesh_data"] == DependencySource.WORKFLOW
        assert len(result.warnings) == 0
    
    def test_fallback_to_database_with_warning(self, mock_filesystem):
        policy = HybridDependencyPolicy(prefer_workflow=True)
        
        dependencies = {"data": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "data" in result.resolved
        assert result.resolved["data"] == DependencySource.DATABASE
        # Should warn because workflow was preferred
        assert "data" in result.warnings
        assert result.warnings["data"].reason == DependencyReason.WORKFLOW_VIOLATION
    
    def test_fallback_to_database_no_warning(self, mock_filesystem):
        policy = HybridDependencyPolicy(prefer_workflow=False)
        
        dependencies = {"data": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "data" in result.resolved
        assert result.resolved["data"] == DependencySource.DATABASE
        # Should NOT warn because workflow not preferred
        assert len(result.warnings) == 0
    
    def test_database_not_found_error(self, mock_filesystem):
        policy = HybridDependencyPolicy()
        
        dependencies = {"missing": mock_filesystem["missing"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "missing" in result.errors
        assert result.errors["missing"].reason == DependencyReason.NOT_FOUND
        assert result.errors["missing"].required is True
    
    def test_age_constraint_blocks_old_data(self, mock_filesystem):
        policy = HybridDependencyPolicy(max_age_days=5)
        
        dependencies = {"old_data": mock_filesystem["old"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "old_data" in result.errors
        assert result.errors["old_data"].reason == DependencyReason.TOO_OLD
        assert result.errors["old_data"].required is True
    
    def test_recent_data_passes_age_check(self, mock_filesystem):
        policy = HybridDependencyPolicy(max_age_days=5)
        
        dependencies = {"recent": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "recent" in result.resolved
    
    def test_workflow_bypasses_age_check(self, mock_filesystem):
        """Data in workflow should bypass age checks"""
        policy = HybridDependencyPolicy(max_age_days=5)
        
        # Even though the file is old, it's in workflow
        dependencies = {"old_data": mock_filesystem["old"]}
        workflow_modules = ["old_data"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert "old_data" in result.resolved
        assert result.resolved["old_data"] == DependencySource.WORKFLOW


# ============================================================================
# FACTORY TESTS
# ============================================================================

class TestDependencyPolicyFactory:
    """Test DependencyPolicyFactory"""
    
    def test_create_from_string_strict(self):
        policy = DependencyPolicyFactory.create("strict")
        assert isinstance(policy, StrictWorkflowPolicy)
    
    def test_create_from_string_flexible(self):
        policy = DependencyPolicyFactory.create("flexible")
        assert isinstance(policy, FlexibleDependencyPolicy)
    
    def test_create_from_string_hybrid(self):
        policy = DependencyPolicyFactory.create("hybrid")
        assert isinstance(policy, HybridDependencyPolicy)
    
    def test_create_from_string_invalid(self):
        with pytest.raises(ValueError, match="Unknown dependency policy"):
            DependencyPolicyFactory.create("invalid_policy")
    
    def test_create_from_dict_flexible_with_params(self):
        config = {
            "name": "flexible",
            "params": {
                "required_deps": ["mesh_data", "material"],
                "max_age_days": 7
            }
        }
        
        policy = DependencyPolicyFactory.create(config)
        assert isinstance(policy, FlexibleDependencyPolicy)
        assert policy.required_deps == {"mesh_data", "material"}
        assert policy.max_age_days == 7
    
    def test_create_from_dict_hybrid_with_params(self):
        config = {
            "name": "hybrid",
            "params": {
                "max_age_days": 10,
                "prefer_workflow": False
            }
        }
        
        policy = DependencyPolicyFactory.create(config)
        assert isinstance(policy, HybridDependencyPolicy)
        assert policy.max_age_days == 10
        assert policy.prefer_workflow is False
    
    def test_create_from_dict_missing_name(self):
        config = {"params": {}}
        
        with pytest.raises(ValueError, match="Missing 'name' field"):
            DependencyPolicyFactory.create(config)
    
    def test_create_from_dict_invalid_params(self):
        config = {
            "name": "flexible",
            "params": {
                "unknown_param": "value",
                "another_unknown": 123
            }
        }
        
        with pytest.raises(ValueError, match="Unknown parameters"):
            DependencyPolicyFactory.create(config)
    
    def test_create_none_returns_none(self):
        policy = DependencyPolicyFactory.create(None)
        assert policy is None
    
    def test_create_invalid_type(self):
        with pytest.raises(TypeError):
            DependencyPolicyFactory.create(123)
    
    def test_get_schema(self):
        schema = DependencyPolicyFactory.get_schema("flexible")
        
        assert "description" in schema
        assert "required_params" in schema
        assert "optional_params" in schema
        assert "defaults" in schema
        assert isinstance(schema["optional_params"], dict)
    
    def test_get_schema_invalid_policy(self):
        with pytest.raises(ValueError, match="Unknown policy"):
            DependencyPolicyFactory.get_schema("nonexistent")
    
    def test_list_policies(self):
        policies = DependencyPolicyFactory.list_policies()
        
        assert isinstance(policies, dict)
        assert "strict" in policies
        assert "flexible" in policies
        assert "hybrid" in policies
        assert all(isinstance(desc, str) for desc in policies.values())


# ============================================================================
# POLICY SCHEMA TESTS
# ============================================================================

class TestPolicySchema:
    """Test PolicySchema validation"""
    
    def test_validate_params_success(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            required_params=["param1"],
            optional_params={
                "param2": {"type": int, "default": 10}
            }
        )
        
        result = schema.validate_params({
            "param1": "value1",
            "param2": 20
        })
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    def test_validate_params_missing_required(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            required_params=["param1", "param2"]
        )
        
        result = schema.validate_params({"param1": "value"})
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("param2" in err for err in result["errors"])
    
    def test_validate_params_unknown_params(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            required_params=["param1"]
        )
        
        result = schema.validate_params({
            "param1": "value",
            "unknown_param": "value"
        })
        
        assert result["valid"] is False
        assert any("Unknown parameters" in err for err in result["errors"])
    
    def test_validate_params_type_warning(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            optional_params={
                "param1": {"type": int}
            }
        )
        
        result = schema.validate_params({"param1": "not_an_int"})
        
        assert result["valid"] is True  # Type mismatch is warning, not error
        assert len(result["warnings"]) > 0
        assert any("type mismatch" in warn for warn in result["warnings"])
    
    def test_get_defaults(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            optional_params={
                "param1": {"type": int, "default": 10},
                "param2": {"type": str, "default": "test"},
                "param3": {"type": bool}  # No default
            }
        )
        
        defaults = schema.get_defaults()
        
        assert defaults["param1"] == 10
        assert defaults["param2"] == "test"
        assert "param3" not in defaults


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPolicyIntegration:
    """Integration tests combining policies with realistic scenarios"""
    
    def test_strict_policy_workflow_execution(self):
        """Simulate strict policy in workflow execution context"""
        policy = StrictWorkflowPolicy()
        
        # Workflow with 3 modules
        workflow_modules = ["preprocess", "simulate", "postprocess"]
        
        # Module dependencies
        dependencies = {
            "preprocess": "/data/input.stl",
            "simulate": "/data/sim_config.yaml",
            "postprocess": "/data/results.csv"
        }
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert len(result.resolved) == 3
    
    def test_flexible_policy_partial_workflow(self, mock_filesystem):
        """Flexible policy allows partial execution"""
        policy = FlexibleDependencyPolicy(
            required_deps=["critical_input"],
            max_age_days=7
        )
        
        dependencies = {
            "critical_input": mock_filesystem["recent"],  # Required, exists
            "optional_cache": mock_filesystem["old"],     # Optional, old
            "optional_missing": mock_filesystem["missing"] # Optional, missing
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should allow execution with warnings
        assert result.valid is True
        assert "critical_input" in result.resolved
        assert "optional_cache" in result.warnings  # Old but optional
        assert "optional_missing" in result.warnings  # Missing but optional
    
    def test_hybrid_policy_progressive_fallback(self, mock_filesystem):
        """Hybrid policy tries workflow first, falls back to database"""
        policy = HybridDependencyPolicy(
            max_age_days=5,
            prefer_workflow=True
        )
        
        dependencies = {
            "in_workflow": "/some/path.stl",
            "in_db_recent": mock_filesystem["recent"],
            "in_db_old": mock_filesystem["old"],
            "missing": mock_filesystem["missing"]
        }
        
        workflow_modules = ["in_workflow"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        # in_workflow: resolved from workflow
        assert result.resolved["in_workflow"] == DependencySource.WORKFLOW
        
        # in_db_recent: resolved from database with warning
        assert result.resolved["in_db_recent"] == DependencySource.DATABASE
        assert "in_db_recent" in result.warnings
        
        # in_db_old: error (too old)
        assert "in_db_old" in result.errors
        
        # missing: error (not found)
        assert "missing" in result.errors


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_dependencies(self):
        policies = [
            StrictWorkflowPolicy(),
            FlexibleDependencyPolicy(),
            HybridDependencyPolicy()
        ]
        
        for policy in policies:
            result = policy.validate({}, workflow_modules=[])
            assert result.valid is True
            assert len(result.resolved) == 0
    
    def test_none_workflow_modules(self, sample_dependencies):
        """All policies should handle None workflow_modules"""
        policies = [
            StrictWorkflowPolicy(),
            FlexibleDependencyPolicy(),
            HybridDependencyPolicy()
        ]
        
        for policy in policies:
            result = policy.validate(sample_dependencies, workflow_modules=None)
            # Should not crash, behavior depends on policy
            assert isinstance(result, DependencyValidationResult)
    
    def test_special_characters_in_paths(self):
        """Test paths with special characters"""
        policy = HybridDependencyPolicy()
        
        dependencies = {
            "data": "/path/with spaces/file.stl",
            "other": "/path/with-dashes/file.json"
        }
        
        # Should handle gracefully (will be missing but shouldn't crash)
        result = policy.validate(dependencies, workflow_modules=[])
        assert isinstance(result, DependencyValidationResult)
    
    @patch('workflows.dependency_policies.base.Path')
    def test_filesystem_error_handling(self, mock_path):
        """Test handling of filesystem errors"""
        mock_path.return_value.exists.side_effect = PermissionError("Access denied")
        
        policy = HybridDependencyPolicy()
        dependencies = {"data": "/restricted/path.stl"}
        
        # Should handle error gracefully
        result = policy.validate(dependencies, workflow_modules=[])
        assert "data" in result.errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])# tests/workflows/test_dependency_policies.py

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from workflows.dependency_policies.base import (
    DependencyPolicy,
    DependencyValidationResult,
    DependencyIssue,
    DependencyReason,
    DependencySource
)
from workflows.dependency_policies.strict import StrictWorkflowPolicy
from workflows.dependency_policies.flexible import FlexibleDependencyPolicy
from workflows.dependency_policies.hybrid import HybridDependencyPolicy
from workflows.dependency_policies.factory import DependencyPolicyFactory
from workflows.dependency_policies import POLICY_SCHEMAS, PolicySchema


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_dependencies():
    """Sample dependencies mapping"""
    return {
        "mesh_data": "/data/meshes/part_001.stl",
        "material_props": "/data/materials/ABS.json",
        "simulation_config": "/data/configs/thermal.yaml"
    }


@pytest.fixture
def workflow_modules():
    """Sample workflow modules"""
    return ["mesh_data", "material_props"]


@pytest.fixture
def mock_filesystem(tmp_path):
    """Create mock filesystem with files of different ages"""
    # Recent file (1 day old)
    recent_file = tmp_path / "recent.stl"
    recent_file.write_text("recent data")
    recent_time = datetime.now() - timedelta(days=1)
    
    # Old file (10 days old)
    old_file = tmp_path / "old.json"
    old_file.write_text("old data")
    old_time = datetime.now() - timedelta(days=10)
    
    # Set modification times (Note: this is platform dependent)
    import os
    os.utime(str(recent_file), (recent_time.timestamp(), recent_time.timestamp()))
    os.utime(str(old_file), (old_time.timestamp(), old_time.timestamp()))
    
    return {
        "recent": str(recent_file),
        "old": str(old_file),
        "missing": str(tmp_path / "missing.yaml")
    }


# ============================================================================
# BASE POLICY TESTS
# ============================================================================

class TestDependencyValidationResult:
    """Test DependencyValidationResult dataclass"""
    
    def test_empty_result_is_valid(self):
        result = DependencyValidationResult()
        assert result.valid is True
        assert result.has_errors() is False
        assert result.has_warnings() is False
        assert result.should_block() is False
    
    def test_result_with_errors_is_invalid(self):
        errors = {
            "dep1": DependencyIssue(
                dep_name="dep1",
                reason=DependencyReason.NOT_FOUND,
                required=True
            )
        }
        result = DependencyValidationResult(errors=errors)
        assert result.valid is False
        assert result.has_errors() is True
        assert result.should_block() is True
    
    def test_result_with_warnings_only_is_valid(self):
        warnings = {
            "dep1": DependencyIssue(
                dep_name="dep1",
                reason=DependencyReason.TOO_OLD,
                required=False
            )
        }
        result = DependencyValidationResult(warnings=warnings)
        assert result.valid is True
        assert result.has_warnings() is True
        assert result.should_block() is False
    
    def test_summary(self):
        result = DependencyValidationResult(
            errors={
                "dep1": DependencyIssue(
                    dep_name="dep1",
                    reason=DependencyReason.NOT_FOUND,
                    source=DependencySource.DATABASE
                )
            },
            warnings={
                "dep2": DependencyIssue(
                    dep_name="dep2",
                    reason=DependencyReason.TOO_OLD,
                    source=DependencySource.DATABASE
                )
            },
            resolved={
                "dep3": DependencySource.WORKFLOW
            }
        )
        
        summary = result.summary()
        assert summary["valid"] is False
        assert summary["errors"]["dep1"] == "not_found"
        assert summary["warnings"]["dep2"] == "too_old"
        assert summary["resolved"]["dep3"] == "workflow"


class TestDependencyIssue:
    """Test DependencyIssue dataclass"""
    
    def test_to_dict(self):
        issue = DependencyIssue(
            dep_name="mesh_data",
            reason=DependencyReason.TOO_OLD,
            source=DependencySource.DATABASE,
            required=True,
            metadata={"age_days": 15}
        )
        
        data = issue.to_dict()
        assert data["dep_name"] == "mesh_data"
        assert data["reason"] == "too_old"
        assert data["source"] == "database"
        assert data["required"] is True
        assert data["metadata"]["age_days"] == 15


# ============================================================================
# STRICT POLICY TESTS
# ============================================================================

class TestStrictWorkflowPolicy:
    """Test StrictWorkflowPolicy"""
    
    def test_all_dependencies_in_workflow(self, sample_dependencies, workflow_modules):
        policy = StrictWorkflowPolicy()
        
        # Only check deps that are in workflow
        deps_to_check = {k: v for k, v in sample_dependencies.items() if k in workflow_modules}
        
        result = policy.validate(deps_to_check, workflow_modules)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.resolved) == 2
        assert result.resolved["mesh_data"] == DependencySource.WORKFLOW
        assert result.resolved["material_props"] == DependencySource.WORKFLOW
    
    def test_missing_dependency_causes_error(self, sample_dependencies, workflow_modules):
        policy = StrictWorkflowPolicy()
        
        result = policy.validate(sample_dependencies, workflow_modules)
        
        assert result.valid is False
        assert "simulation_config" in result.errors
        assert result.errors["simulation_config"].reason == DependencyReason.WORKFLOW_VIOLATION
        assert result.errors["simulation_config"].required is True
    
    def test_empty_workflow_all_errors(self, sample_dependencies):
        policy = StrictWorkflowPolicy()
        
        result = policy.validate(sample_dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert len(result.errors) == 3
        for dep_name in sample_dependencies.keys():
            assert dep_name in result.errors
            assert result.errors[dep_name].reason == DependencyReason.WORKFLOW_VIOLATION
    
    def test_no_dependencies(self):
        policy = StrictWorkflowPolicy()
        
        result = policy.validate({}, workflow_modules=["module1"])
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.resolved) == 0


# ============================================================================
# FLEXIBLE POLICY TESTS
# ============================================================================

class TestFlexibleDependencyPolicy:
    """Test FlexibleDependencyPolicy"""
    
    def test_no_required_deps_all_optional(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(required_deps=None, max_age_days=None)
        
        dependencies = {
            "recent": mock_filesystem["recent"],
            "missing": mock_filesystem["missing"]
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should be valid since all deps are optional
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1  # missing is warning only
        assert "missing" in result.warnings
        assert result.warnings["missing"].reason == DependencyReason.NOT_FOUND
    
    def test_required_dep_found_in_workflow(self):
        policy = FlexibleDependencyPolicy(required_deps=["mesh_data"])
        
        dependencies = {"mesh_data": "/some/path.stl"}
        workflow_modules = ["mesh_data"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert "mesh_data" in result.resolved
        assert result.resolved["mesh_data"] == DependencySource.WORKFLOW
    
    def test_required_dep_missing_causes_error(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(required_deps=["critical_data"])
        
        dependencies = {"critical_data": mock_filesystem["missing"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "critical_data" in result.errors
        assert result.errors["critical_data"].required is True
    
    def test_age_constraint_required_dep(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(
            required_deps=["old_data"],
            max_age_days=5
        )
        
        dependencies = {"old_data": mock_filesystem["old"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "old_data" in result.errors
        assert result.errors["old_data"].reason == DependencyReason.TOO_OLD
        assert result.errors["old_data"].required is True
    
    def test_age_constraint_optional_dep(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(
            required_deps=[],
            max_age_days=5
        )
        
        dependencies = {"old_data": mock_filesystem["old"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should be valid but with warning
        assert result.valid is True
        assert "old_data" in result.warnings
        assert result.warnings["old_data"].reason == DependencyReason.TOO_OLD
        assert result.warnings["old_data"].required is False
    
    def test_recent_file_passes_age_check(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(
            required_deps=["recent_data"],
            max_age_days=5
        )
        
        dependencies = {"recent_data": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "recent_data" in result.resolved
        assert result.resolved["recent_data"] == DependencySource.DATABASE
    
    def test_mixed_required_and_optional(self, mock_filesystem):
        policy = FlexibleDependencyPolicy(required_deps=["dep1"])
        
        dependencies = {
            "dep1": mock_filesystem["recent"],  # required, exists
            "dep2": mock_filesystem["missing"]  # optional, missing
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "dep1" in result.resolved
        assert "dep2" in result.warnings
        assert result.warnings["dep2"].required is False


# ============================================================================
# HYBRID POLICY TESTS
# ============================================================================

class TestHybridDependencyPolicy:
    """Test HybridDependencyPolicy"""
    
    def test_workflow_preferred_no_fallback(self):
        policy = HybridDependencyPolicy(prefer_workflow=True)
        
        dependencies = {"mesh_data": "/some/path.stl"}
        workflow_modules = ["mesh_data"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert "mesh_data" in result.resolved
        assert result.resolved["mesh_data"] == DependencySource.WORKFLOW
        assert len(result.warnings) == 0
    
    def test_fallback_to_database_with_warning(self, mock_filesystem):
        policy = HybridDependencyPolicy(prefer_workflow=True)
        
        dependencies = {"data": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "data" in result.resolved
        assert result.resolved["data"] == DependencySource.DATABASE
        # Should warn because workflow was preferred
        assert "data" in result.warnings
        assert result.warnings["data"].reason == DependencyReason.WORKFLOW_VIOLATION
    
    def test_fallback_to_database_no_warning(self, mock_filesystem):
        policy = HybridDependencyPolicy(prefer_workflow=False)
        
        dependencies = {"data": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "data" in result.resolved
        assert result.resolved["data"] == DependencySource.DATABASE
        # Should NOT warn because workflow not preferred
        assert len(result.warnings) == 0
    
    def test_database_not_found_error(self, mock_filesystem):
        policy = HybridDependencyPolicy()
        
        dependencies = {"missing": mock_filesystem["missing"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "missing" in result.errors
        assert result.errors["missing"].reason == DependencyReason.NOT_FOUND
        assert result.errors["missing"].required is True
    
    def test_age_constraint_blocks_old_data(self, mock_filesystem):
        policy = HybridDependencyPolicy(max_age_days=5)
        
        dependencies = {"old_data": mock_filesystem["old"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        assert "old_data" in result.errors
        assert result.errors["old_data"].reason == DependencyReason.TOO_OLD
        assert result.errors["old_data"].required is True
    
    def test_recent_data_passes_age_check(self, mock_filesystem):
        policy = HybridDependencyPolicy(max_age_days=5)
        
        dependencies = {"recent": mock_filesystem["recent"]}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "recent" in result.resolved
    
    def test_workflow_bypasses_age_check(self, mock_filesystem):
        """Data in workflow should bypass age checks"""
        policy = HybridDependencyPolicy(max_age_days=5)
        
        # Even though the file is old, it's in workflow
        dependencies = {"old_data": mock_filesystem["old"]}
        workflow_modules = ["old_data"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert "old_data" in result.resolved
        assert result.resolved["old_data"] == DependencySource.WORKFLOW


# ============================================================================
# FACTORY TESTS
# ============================================================================

class TestDependencyPolicyFactory:
    """Test DependencyPolicyFactory"""
    
    def test_create_from_string_strict(self):
        policy = DependencyPolicyFactory.create("strict")
        assert isinstance(policy, StrictWorkflowPolicy)
    
    def test_create_from_string_flexible(self):
        policy = DependencyPolicyFactory.create("flexible")
        assert isinstance(policy, FlexibleDependencyPolicy)
    
    def test_create_from_string_hybrid(self):
        policy = DependencyPolicyFactory.create("hybrid")
        assert isinstance(policy, HybridDependencyPolicy)
    
    def test_create_from_string_invalid(self):
        with pytest.raises(ValueError, match="Unknown dependency policy"):
            DependencyPolicyFactory.create("invalid_policy")
    
    def test_create_from_dict_flexible_with_params(self):
        config = {
            "name": "flexible",
            "params": {
                "required_deps": ["mesh_data", "material"],
                "max_age_days": 7
            }
        }
        
        policy = DependencyPolicyFactory.create(config)
        assert isinstance(policy, FlexibleDependencyPolicy)
        assert policy.required_deps == {"mesh_data", "material"}
        assert policy.max_age_days == 7
    
    def test_create_from_dict_hybrid_with_params(self):
        config = {
            "name": "hybrid",
            "params": {
                "max_age_days": 10,
                "prefer_workflow": False
            }
        }
        
        policy = DependencyPolicyFactory.create(config)
        assert isinstance(policy, HybridDependencyPolicy)
        assert policy.max_age_days == 10
        assert policy.prefer_workflow is False
    
    def test_create_from_dict_missing_name(self):
        config = {"params": {}}
        
        with pytest.raises(ValueError, match="Missing 'name' field"):
            DependencyPolicyFactory.create(config)
    
    def test_create_from_dict_invalid_params(self):
        config = {
            "name": "flexible",
            "params": {
                "unknown_param": "value",
                "another_unknown": 123
            }
        }
        
        with pytest.raises(ValueError, match="Unknown parameters"):
            DependencyPolicyFactory.create(config)
    
    def test_create_none_returns_none(self):
        policy = DependencyPolicyFactory.create(None)
        assert policy is None
    
    def test_create_invalid_type(self):
        with pytest.raises(TypeError):
            DependencyPolicyFactory.create(123)
    
    def test_get_schema(self):
        schema = DependencyPolicyFactory.get_schema("flexible")
        
        assert "description" in schema
        assert "required_params" in schema
        assert "optional_params" in schema
        assert "defaults" in schema
        assert isinstance(schema["optional_params"], dict)
    
    def test_get_schema_invalid_policy(self):
        with pytest.raises(ValueError, match="Unknown policy"):
            DependencyPolicyFactory.get_schema("nonexistent")
    
    def test_list_policies(self):
        policies = DependencyPolicyFactory.list_policies()
        
        assert isinstance(policies, dict)
        assert "strict" in policies
        assert "flexible" in policies
        assert "hybrid" in policies
        assert all(isinstance(desc, str) for desc in policies.values())


# ============================================================================
# POLICY SCHEMA TESTS
# ============================================================================

class TestPolicySchema:
    """Test PolicySchema validation"""
    
    def test_validate_params_success(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            required_params=["param1"],
            optional_params={
                "param2": {"type": int, "default": 10}
            }
        )
        
        result = schema.validate_params({
            "param1": "value1",
            "param2": 20
        })
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    def test_validate_params_missing_required(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            required_params=["param1", "param2"]
        )
        
        result = schema.validate_params({"param1": "value"})
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("param2" in err for err in result["errors"])
    
    def test_validate_params_unknown_params(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            required_params=["param1"]
        )
        
        result = schema.validate_params({
            "param1": "value",
            "unknown_param": "value"
        })
        
        assert result["valid"] is False
        assert any("Unknown parameters" in err for err in result["errors"])
    
    def test_validate_params_type_warning(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            optional_params={
                "param1": {"type": int}
            }
        )
        
        result = schema.validate_params({"param1": "not_an_int"})
        
        assert result["valid"] is True  # Type mismatch is warning, not error
        assert len(result["warnings"]) > 0
        assert any("type mismatch" in warn for warn in result["warnings"])
    
    def test_get_defaults(self):
        schema = PolicySchema(
            policy_class=FlexibleDependencyPolicy,
            optional_params={
                "param1": {"type": int, "default": 10},
                "param2": {"type": str, "default": "test"},
                "param3": {"type": bool}  # No default
            }
        )
        
        defaults = schema.get_defaults()
        
        assert defaults["param1"] == 10
        assert defaults["param2"] == "test"
        assert "param3" not in defaults


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPolicyIntegration:
    """Integration tests combining policies with realistic scenarios"""
    
    def test_strict_policy_workflow_execution(self):
        """Simulate strict policy in workflow execution context"""
        policy = StrictWorkflowPolicy()
        
        # Workflow with 3 modules
        workflow_modules = ["preprocess", "simulate", "postprocess"]
        
        # Module dependencies
        dependencies = {
            "preprocess": "/data/input.stl",
            "simulate": "/data/sim_config.yaml",
            "postprocess": "/data/results.csv"
        }
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is True
        assert len(result.resolved) == 3
    
    def test_flexible_policy_partial_workflow(self, mock_filesystem):
        """Flexible policy allows partial execution"""
        policy = FlexibleDependencyPolicy(
            required_deps=["critical_input"],
            max_age_days=7
        )
        
        dependencies = {
            "critical_input": mock_filesystem["recent"],  # Required, exists
            "optional_cache": mock_filesystem["old"],     # Optional, old
            "optional_missing": mock_filesystem["missing"] # Optional, missing
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should allow execution with warnings
        assert result.valid is True
        assert "critical_input" in result.resolved
        assert "optional_cache" in result.warnings  # Old but optional
        assert "optional_missing" in result.warnings  # Missing but optional
    
    def test_hybrid_policy_progressive_fallback(self, mock_filesystem):
        """Hybrid policy tries workflow first, falls back to database"""
        policy = HybridDependencyPolicy(
            max_age_days=5,
            prefer_workflow=True
        )
        
        dependencies = {
            "in_workflow": "/some/path.stl",
            "in_db_recent": mock_filesystem["recent"],
            "in_db_old": mock_filesystem["old"],
            "missing": mock_filesystem["missing"]
        }
        
        workflow_modules = ["in_workflow"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        # in_workflow: resolved from workflow
        assert result.resolved["in_workflow"] == DependencySource.WORKFLOW
        
        # in_db_recent: resolved from database with warning
        assert result.resolved["in_db_recent"] == DependencySource.DATABASE
        assert "in_db_recent" in result.warnings
        
        # in_db_old: error (too old)
        assert "in_db_old" in result.errors
        
        # missing: error (not found)
        assert "missing" in result.errors


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_dependencies(self):
        policies = [
            StrictWorkflowPolicy(),
            FlexibleDependencyPolicy(),
            HybridDependencyPolicy()
        ]
        
        for policy in policies:
            result = policy.validate({}, workflow_modules=[])
            assert result.valid is True
            assert len(result.resolved) == 0
    
    def test_none_workflow_modules(self, sample_dependencies):
        """All policies should handle None workflow_modules"""
        policies = [
            StrictWorkflowPolicy(),
            FlexibleDependencyPolicy(),
            HybridDependencyPolicy()
        ]
        
        for policy in policies:
            result = policy.validate(sample_dependencies, workflow_modules=None)
            # Should not crash, behavior depends on policy
            assert isinstance(result, DependencyValidationResult)
    
    def test_special_characters_in_paths(self):
        """Test paths with special characters"""
        policy = HybridDependencyPolicy()
        
        dependencies = {
            "data": "/path/with spaces/file.stl",
            "other": "/path/with-dashes/file.json"
        }
        
        # Should handle gracefully (will be missing but shouldn't crash)
        result = policy.validate(dependencies, workflow_modules=[])
        assert isinstance(result, DependencyValidationResult)
    
    @patch('workflows.dependency_policies.base.Path')
    def test_filesystem_error_handling(self, mock_path):
        """Test handling of filesystem errors"""
        mock_path.return_value.exists.side_effect = PermissionError("Access denied")
        
        policy = HybridDependencyPolicy()
        dependencies = {"data": "/restricted/path.stl"}
        
        # Should handle error gracefully
        result = policy.validate(dependencies, workflow_modules=[])
        assert "data" in result.errors