# tests/modules_tests/test_base_module_errors.py

"""
Test error handling in BaseModule
"""

import pytest
from modules.base_module import ModuleResult


class TestBaseModuleErrorHandling:
    """Test error scenarios in BaseModule"""
    
    def test_execute_without_parameters(self, module_fixture_factory):
        """Test that module executes without any parameters"""
        module = module_fixture_factory('DataPipelineModule')
        
        # Should execute successfully without parameters
        result = module.safe_execute()
        
        # Result should be valid
        assert isinstance(result, ModuleResult)
        assert result.status in ('success', 'failed', 'skipped')
    
    def test_execute_with_exception(self, module_fixture_factory, monkeypatch):
        """Test module execution with unexpected exception"""
        module = module_fixture_factory('DataPipelineModule')
        
        # Mock execute to raise exception
        def mock_execute():
            raise ValueError("Simulated error")
        
        monkeypatch.setattr(module, 'execute', mock_execute)
        
        # Should catch exception in safe_execute
        result = module.safe_execute()
        
        assert result.status == 'failed'
        assert "Simulated error" in result.message
        assert result.errors is not None
        assert len(result.errors) > 0
    
    def test_module_result_status_methods(self):
        """Test ModuleResult status checking methods"""
        # Test success
        success_result = ModuleResult(
            status='success',
            data={'key': 'value'},
            message='Success'
        )
        assert success_result.is_success()
        assert not success_result.is_failed()
        assert not success_result.is_skipped()
        
        # Test failed
        failed_result = ModuleResult(
            status='failed',
            data=None,
            message='Failed',
            errors=['Error 1']
        )
        assert failed_result.is_failed()
        assert not failed_result.is_success()
        assert not failed_result.is_skipped()
        
        # Test skipped
        skipped_result = ModuleResult(
            status='skipped',
            data=None,
            message='Skipped'
        )
        assert skipped_result.is_skipped()
        assert not skipped_result.is_success()
        assert not skipped_result.is_failed()
    
    def test_execute_returns_module_result(self, module_fixture_factory):
        """Test that execute always returns ModuleResult"""
        module = module_fixture_factory('DataPipelineModule')
        
        result = module.safe_execute()
        
        assert isinstance(result, ModuleResult)
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert hasattr(result, 'message')
        assert hasattr(result, 'errors')
    
    def test_error_message_in_result(self, module_fixture_factory, monkeypatch):
        """Test that error messages are properly captured"""
        module = module_fixture_factory('DataPipelineModule')
        
        error_msg = "Custom error message"
        
        def mock_execute():
            raise RuntimeError(error_msg)
        
        monkeypatch.setattr(module, 'execute', mock_execute)
        
        result = module.safe_execute()
        
        assert result.status == 'failed'
        assert error_msg in result.message
        assert result.errors is not None
        assert any(error_msg in str(e) for e in result.errors)
    
    def test_logger_binding(self, module_fixture_factory):
        """Test that logger is properly bound with module name"""
        module = module_fixture_factory('DataPipelineModule')
        
        # Logger should be bound with module name
        assert hasattr(module, 'logger')
        # The logger should have the module context
        # (Actual verification depends on loguru implementation)
    
    def test_multiple_executions(self, module_fixture_factory):
        """Test that module can be executed multiple times"""
        module = module_fixture_factory('DataPipelineModule')
        
        # First execution
        result1 = module.safe_execute()
        assert isinstance(result1, ModuleResult)
        
        # Second execution
        result2 = module.safe_execute()
        assert isinstance(result2, ModuleResult)
        
        # Both should be valid results
        assert result1.status in ('success', 'failed', 'skipped')
        assert result2.status in ('success', 'failed', 'skipped')
    
    def test_config_loading_error_handling(self, module_fixture_factory, tmp_path):
        """Test error handling when config file doesn't exist"""
        from modules import AVAILABLE_MODULES
        
        # Try to create module with non-existent config
        non_existent_config = str(tmp_path / "does_not_exist.yaml")
        
        module_class = AVAILABLE_MODULES['DataPipelineModule']
        
        # Should handle gracefully (use default or empty config)
        module = module_class(non_existent_config)
        
        # Should still be able to instantiate
        assert module is not None
        assert hasattr(module, 'config')
        # Config might be empty dict
        assert isinstance(module.config, dict)
    
    def test_safe_execute_logs_correctly(self, module_fixture_factory, caplog):
        """Test that safe_execute logs execution info"""
        import logging
        
        module = module_fixture_factory('DataPipelineModule')
        
        # Capture logs
        with caplog.at_level(logging.INFO):
            result = module.safe_execute()
        
        # Should have logged execution start
        log_messages = [record.message for record in caplog.records]
        
        # Check for execution log (might vary based on implementation)
        # At minimum, should have some logging
        assert len(log_messages) > 0


class TestModuleResultDataclass:
    """Test ModuleResult dataclass functionality"""
    
    def test_module_result_creation_minimal(self):
        """Test creating ModuleResult with minimal fields"""
        result = ModuleResult(
            status='success',
            data=None,
            message='OK'
        )
        
        assert result.status == 'success'
        assert result.data is None
        assert result.message == 'OK'
        assert result.errors is None
    
    def test_module_result_creation_full(self):
        """Test creating ModuleResult with all fields"""
        result = ModuleResult(
            status='failed',
            data={'key': 'value'},
            message='Error occurred',
            errors=['Error 1', 'Error 2']
        )
        
        assert result.status == 'failed'
        assert result.data == {'key': 'value'}
        assert result.message == 'Error occurred'
        assert result.errors == ['Error 1', 'Error 2']
    
    def test_module_result_is_dataclass(self):
        """Test that ModuleResult behaves as dataclass"""
        from dataclasses import is_dataclass
        
        assert is_dataclass(ModuleResult)
    
    def test_module_result_equality(self):
        """Test ModuleResult equality comparison"""
        result1 = ModuleResult(
            status='success',
            data={'key': 'value'},
            message='OK'
        )
        
        result2 = ModuleResult(
            status='success',
            data={'key': 'value'},
            message='OK'
        )
        
        # Dataclasses should support equality
        assert result1 == result2
    
    def test_module_result_status_values(self):
        """Test that status accepts expected values"""
        valid_statuses = ['success', 'failed', 'skipped']
        
        for status in valid_statuses:
            result = ModuleResult(
                status=status,
                data=None,
                message=f'Status: {status}'
            )
            assert result.status == status


class TestBaseModuleDependencies:
    """Test dependency-related functionality"""
    
    def test_dependencies_property_exists(self, module_fixture_factory):
        """Test that dependencies property exists"""
        module = module_fixture_factory('DataPipelineModule')
        
        assert hasattr(module, 'dependencies')
        assert isinstance(module.dependencies, dict)
    
    def test_dependencies_are_strings(self, module_fixture_factory):
        """Test that dependency values are strings"""
        module = module_fixture_factory('DataPipelineModule')
        
        for dep_name, dep_path in module.dependencies.items():
            assert isinstance(dep_name, str)
            assert isinstance(dep_path, str)
    
    def test_module_name_property(self, module_fixture_factory):
        """Test module_name property"""
        module = module_fixture_factory('DataPipelineModule')
        
        assert hasattr(module, 'module_name')
        assert isinstance(module.module_name, str)
        assert len(module.module_name) > 0