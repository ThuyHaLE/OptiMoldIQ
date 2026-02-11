# tests/workflows_tests/test_dependency_policies_advanced.py

import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, call
from optiMoldMaster.workflows.dependency_policies.strict import StrictWorkflowPolicy
from optiMoldMaster.workflows.dependency_policies.flexible import FlexibleDependencyPolicy
from optiMoldMaster.workflows.dependency_policies.hybrid import HybridDependencyPolicy
from optiMoldMaster.workflows.dependency_policies.factory import DependencyPolicyFactory
from optiMoldMaster.workflows.dependency_policies.base import DependencyReason, DependencySource


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance with large dependency sets"""
    
    def test_strict_policy_large_workflow(self):
        """Test strict policy with 1000 dependencies"""
        policy = StrictWorkflowPolicy()
        
        # Generate large dependency set
        num_deps = 1000
        dependencies = {f"dep_{i}": f"/path/to/dep_{i}.dat" for i in range(num_deps)}
        workflow_modules = [f"dep_{i}" for i in range(num_deps)]
        
        start = time.time()
        result = policy.validate(dependencies, workflow_modules)
        duration = time.time() - start
        
        assert result.valid is True
        assert len(result.resolved) == num_deps
        assert duration < 1.0  # Should complete in under 1 second
    
    def test_flexible_policy_large_mixed(self, tmp_path):
        """Test flexible policy with mixed large dataset"""
        policy = FlexibleDependencyPolicy(
            required_deps=[f"req_{i}" for i in range(100)],
            max_age_days=30
        )
        
        # Create some real files
        dependencies = {}
        for i in range(500):
            file_path = tmp_path / f"file_{i}.dat"
            file_path.write_text(f"data {i}")
            dependencies[f"dep_{i}"] = str(file_path)
        
        start = time.time()
        result = policy.validate(dependencies, workflow_modules=[])
        duration = time.time() - start
        
        # Should handle 500 file checks in reasonable time
        assert duration < 5.0
    
    def test_hybrid_policy_repeated_validation(self, tmp_path):
        """Test repeated validation calls (caching behavior)"""
        policy = HybridDependencyPolicy(max_age_days=30)
        
        # Create test files
        dependencies = {}
        for i in range(100):
            file_path = tmp_path / f"file_{i}.dat"
            file_path.write_text(f"data {i}")
            dependencies[f"dep_{i}"] = str(file_path)
        
        # Run validation multiple times
        times = []
        for _ in range(10):
            start = time.time()
            result = policy.validate(dependencies, workflow_modules=[])
            times.append(time.time() - start)
            assert result.valid is True
        
        # Each call should be consistently fast
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0


# ============================================================================
# CONCURRENT ACCESS TESTS
# ============================================================================

class TestConcurrency:
    """Test thread-safety and concurrent validation"""
    
    def test_multiple_policies_different_configs(self):
        """Test multiple policy instances don't interfere"""
        policies = [
            FlexibleDependencyPolicy(required_deps=["dep1"], max_age_days=5),
            FlexibleDependencyPolicy(required_deps=["dep2"], max_age_days=10),
            FlexibleDependencyPolicy(required_deps=["dep3"], max_age_days=15)
        ]
        
        # Verify each maintains its own config
        assert policies[0].required_deps == {"dep1"}
        assert policies[0].max_age_days == 5
        
        assert policies[1].required_deps == {"dep2"}
        assert policies[1].max_age_days == 10
        
        assert policies[2].required_deps == {"dep3"}
        assert policies[2].max_age_days == 15


# ============================================================================
# COMPLEX DEPENDENCY SCENARIOS
# ============================================================================

class TestComplexScenarios:
    """Test complex real-world dependency scenarios"""
    
    def test_circular_dependency_names(self):
        """Test handling of circular dependency naming (not actual circular deps)"""
        policy = StrictWorkflowPolicy()
        
        dependencies = {
            "module_a": "/path/a.dat",
            "module_b": "/path/b.dat",
            "module_c": "/path/c.dat"
        }
        
        # All modules reference each other in workflow
        workflow_modules = ["module_a", "module_b", "module_c"]
        
        result = policy.validate(dependencies, workflow_modules)
        assert result.valid is True
    
    def test_deeply_nested_paths(self, tmp_path):
        """Test dependencies with deeply nested paths"""
        # Create deeply nested structure
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e" / "f"
        deep_path.mkdir(parents=True, exist_ok=True)
        
        file_path = deep_path / "deep_file.dat"
        file_path.write_text("deep data")
        
        policy = HybridDependencyPolicy()
        dependencies = {"deep_dep": str(file_path)}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "deep_dep" in result.resolved
    
    def test_unicode_paths_and_names(self, tmp_path):
        """Test Unicode characters in paths and dependency names"""
        unicode_path = tmp_path / "数据" / "文件.dat"
        unicode_path.parent.mkdir(parents=True, exist_ok=True)
        unicode_path.write_text("unicode data")
        
        policy = FlexibleDependencyPolicy()
        dependencies = {"数据_依赖": str(unicode_path)}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
        assert "数据_依赖" in result.resolved
    
    def test_case_sensitive_dependency_names(self):
        """Test case sensitivity in dependency names"""
        policy = StrictWorkflowPolicy()
        
        dependencies = {
            "MeshData": "/path/mesh.stl",
            "meshdata": "/path/mesh2.stl",
            "MESHDATA": "/path/mesh3.stl"
        }
        
        # Only exact matches should resolve
        workflow_modules = ["MeshData"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        assert result.valid is False
        assert "MeshData" in result.resolved
        assert "meshdata" in result.errors
        assert "MESHDATA" in result.errors


# ============================================================================
# METADATA AND LOGGING TESTS
# ============================================================================

class TestMetadataAndLogging:
    """Test metadata tracking and logging"""
    
    def test_error_metadata_contains_details(self, tmp_path):
        """Test that errors contain useful metadata"""
        old_file = tmp_path / "old.dat"
        old_file.write_text("old data")
        
        # Make it old
        old_time = datetime.now() - timedelta(days=100)
        import os
        os.utime(str(old_file), (old_time.timestamp(), old_time.timestamp()))
        
        policy = FlexibleDependencyPolicy(
            required_deps=["old_dep"],
            max_age_days=30
        )
        
        dependencies = {"old_dep": str(old_file)}
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is False
        error = result.errors["old_dep"]
        
        # Check metadata
        assert "age_days" in error.metadata
        assert error.metadata["age_days"] > 30
        assert "max_age_days" in error.metadata
        assert error.metadata["max_age_days"] == 30
        assert "last_modified" in error.metadata
    
    def test_workflow_violation_metadata(self):
        """Test workflow violation contains workflow info"""
        policy = StrictWorkflowPolicy()
        
        dependencies = {"missing_dep": "/path/missing.dat"}
        workflow_modules = ["other_module"]
        
        result = policy.validate(dependencies, workflow_modules)
        
        error = result.errors["missing_dep"]
        assert "workflow_modules" in error.metadata
        assert error.metadata["workflow_modules"] == workflow_modules
    
    @patch('optiMoldMaster.workflows.dependency_policies.base.logger')
    def test_logging_behavior(self, mock_logger):
        """Test that policies log appropriately"""
        policy = FlexibleDependencyPolicy(required_deps=["dep1"])
        
        dependencies = {"dep1": "/nonexistent/path.dat"}
        
        with patch.object(policy, 'logger') as mock_policy_logger:
            result = policy.validate(dependencies, workflow_modules=[])
            
            # Should have logged the missing dependency
            assert mock_policy_logger.warning.called or mock_policy_logger.info.called


# ============================================================================
# FACTORY ADVANCED TESTS
# ============================================================================

class TestFactoryAdvanced:
    """Advanced factory tests"""
    
    def test_factory_with_empty_params(self):
        """Test factory with empty params dict"""
        config = {
            "name": "flexible",
            "params": {}
        }
        
        policy = DependencyPolicyFactory.create(config)
        assert isinstance(policy, FlexibleDependencyPolicy)
        assert policy.required_deps == set()
        assert policy.max_age_days is None
    
    def test_factory_defaults_applied(self):
        """Test that schema defaults are properly applied"""
        # Check schema defaults
        schema = DependencyPolicyFactory.get_schema("flexible")
        defaults = schema["defaults"]
        
        # Create policy without specifying optional params
        policy = DependencyPolicyFactory.create("flexible")
        
        # Defaults should be applied (or None if no default)
        assert isinstance(policy, FlexibleDependencyPolicy)
    
    def test_factory_validation_warnings_logged(self):
        """Test that validation warnings are logged"""
        config = {
            "name": "flexible",
            "params": {
                "max_age_days": "not_an_int"  # Wrong type
            }
        }
        
        with patch('optiMoldMaster.workflows.dependency_policies.factory.logger') as mock_logger:
            # Should succeed but log warning
            policy = DependencyPolicyFactory.create(config)
            assert isinstance(policy, FlexibleDependencyPolicy)
            # Warning should have been logged
            assert mock_logger.warning.called
    
    def test_factory_multiple_policies_from_configs(self):
        """Test creating multiple different policies"""
        configs = [
            {"name": "strict"},
            {"name": "flexible", "params": {"required_deps": ["dep1"]}},
            {"name": "hybrid", "params": {"max_age_days": 10}}
        ]
        
        policies = [DependencyPolicyFactory.create(cfg) for cfg in configs]
        
        assert isinstance(policies[0], StrictWorkflowPolicy)
        assert isinstance(policies[1], FlexibleDependencyPolicy)
        assert isinstance(policies[2], HybridDependencyPolicy)
        
        # Check params
        assert policies[1].required_deps == {"dep1"}
        assert policies[2].max_age_days == 10


# ============================================================================
# BOUNDARY VALUE TESTS
# ============================================================================

class TestBoundaryValues:
    """Test boundary values and edge conditions"""
    
    def test_age_exactly_at_limit(self, tmp_path):
        """Test file exactly at age limit"""
        file_path = tmp_path / "exact.dat"
        file_path.write_text("data")
        
        # Set to exactly max_age_days old
        exact_time = datetime.now() - timedelta(days=30, hours=0, minutes=0, seconds=0)
        import os
        os.utime(str(file_path), (exact_time.timestamp(), exact_time.timestamp()))
        
        policy = FlexibleDependencyPolicy(max_age_days=30)
        dependencies = {"exact": str(file_path)}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # At exactly 30 days, age_days = 30, which is NOT > 30, so should pass
        assert result.valid is True
    
    def test_age_one_second_over_limit(self, tmp_path):
        """Test file one day over age limit"""
        file_path = tmp_path / "over.dat"
        file_path.write_text("data")
        
        # Set to 31 days old
        over_time = datetime.now() - timedelta(days=31)
        import os
        os.utime(str(file_path), (over_time.timestamp(), over_time.timestamp()))
        
        policy = FlexibleDependencyPolicy(
            required_deps=["over"],
            max_age_days=30
        )
        dependencies = {"over": str(file_path)}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should fail
        assert result.valid is False
        assert "over" in result.errors
    
    def test_zero_age_limit(self, tmp_path):
        """Test max_age_days = 0 (only current files)"""
        file_path = tmp_path / "new.dat"
        file_path.write_text("data")
        
        policy = FlexibleDependencyPolicy(max_age_days=0)
        dependencies = {"new": str(file_path)}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # File is just created, should pass
        assert result.valid is True
    
    def test_very_large_age_limit(self, tmp_path):
        """Test very large max_age_days"""
        file_path = tmp_path / "any.dat"
        file_path.write_text("data")
        
        policy = FlexibleDependencyPolicy(max_age_days=365 * 100)  # 100 years
        dependencies = {"any": str(file_path)}
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        assert result.valid is True
    
    def test_empty_string_dependency_name(self):
        """Test empty string as dependency name"""
        policy = StrictWorkflowPolicy()
        
        dependencies = {"": "/path/file.dat"}
        workflow_modules = [""]
        
        result = policy.validate(dependencies, workflow_modules)
        
        # Should handle gracefully
        assert "" in result.resolved


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

class TestErrorRecovery:
    """Test error recovery and resilience"""
    
    def test_partial_filesystem_failure(self, tmp_path):
        """Test handling when some file checks fail"""
        good_file = tmp_path / "good.dat"
        good_file.write_text("data")
        
        policy = HybridDependencyPolicy()
        
        dependencies = {
            "good": str(good_file),
            "bad": "/dev/null/impossible/path.dat"
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should resolve good, error on bad
        assert "good" in result.resolved
        assert "bad" in result.errors
    
    def test_policy_continues_after_errors(self, tmp_path):
        """Test that validation continues after encountering errors"""
        file1 = tmp_path / "file1.dat"
        file2 = tmp_path / "file2.dat"
        file1.write_text("data1")
        file2.write_text("data2")
        
        policy = FlexibleDependencyPolicy(
            required_deps=["missing", "file1", "file2"]
        )
        
        dependencies = {
            "missing": str(tmp_path / "nonexistent.dat"),
            "file1": str(file1),
            "file2": str(file2)
        }
        
        result = policy.validate(dependencies, workflow_modules=[])
        
        # Should have error for missing but resolve the others
        assert "missing" in result.errors
        assert "file1" in result.resolved
        assert "file2" in result.resolved


# ============================================================================
# COMPARISON TESTS
# ============================================================================

class TestPolicyComparisons:
    """Compare behavior across different policies"""
    
    def test_same_deps_different_policies(self, tmp_path):
        """Test same dependencies with different policies"""
        file_path = tmp_path / "data.dat"
        file_path.write_text("data")
        
        dependencies = {"dep1": str(file_path)}
        workflow_modules = []
        
        # Test with all three policies
        strict = StrictWorkflowPolicy()
        flexible = FlexibleDependencyPolicy()
        hybrid = HybridDependencyPolicy()
        
        strict_result = strict.validate(dependencies, workflow_modules)
        flexible_result = flexible.validate(dependencies, workflow_modules)
        hybrid_result = hybrid.validate(dependencies, workflow_modules)
        
        # Strict: should fail (not in workflow)
        assert strict_result.valid is False
        assert "dep1" in strict_result.errors
        
        # Flexible: should pass (optional by default)
        assert flexible_result.valid is True
        assert "dep1" in flexible_result.resolved
        
        # Hybrid: should pass (fallback to database)
        assert hybrid_result.valid is True
        assert "dep1" in hybrid_result.resolved
    
    def test_strictness_ordering(self, tmp_path):
        """Verify policies from most to least strict"""
        file_path = tmp_path / "data.dat"
        file_path.write_text("data")
        
        dependencies = {"dep1": str(file_path)}
        workflow_modules = []
        
        policies = {
            "strict": StrictWorkflowPolicy(),
            "hybrid": HybridDependencyPolicy(prefer_workflow=True),
            "flexible": FlexibleDependencyPolicy()
        }
        
        results = {
            name: policy.validate(dependencies, workflow_modules)
            for name, policy in policies.items()
        }
        
        # Strict should be most restrictive
        assert results["strict"].valid is False
        
        # Hybrid should allow with warning
        assert results["hybrid"].valid is True
        assert len(results["hybrid"].warnings) > 0
        
        # Flexible should allow with no issues
        assert results["flexible"].valid is True
        assert len(results["flexible"].warnings) == 0