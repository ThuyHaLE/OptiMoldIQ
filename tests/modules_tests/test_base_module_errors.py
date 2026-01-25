# tests/modules_tests/test_base_module_errors.py

class TestBaseModuleErrorHandling:
    """Test error scenarios in BaseModule"""
    
    def test_execute_with_invalid_context(self, module_fixture_factory):
        """Test module with invalid context type"""
        module = module_fixture_factory('DataPipelineModule')
        
        # Test with None context
        result = module.safe_execute(None)
        assert result.status == 'failed'
        
        # Test with invalid type
        result = module.safe_execute("not a dict")
        assert result.status == 'failed'
    
    def test_execute_with_exception(self, module_fixture_factory, monkeypatch):
        """Test module execution with unexpected exception"""
        module = module_fixture_factory('DataPipelineModule')
        
        # Mock execute to raise exception
        def mock_execute(*args, **kwargs):
            raise ValueError("Simulated error")
        
        monkeypatch.setattr(module, 'execute', mock_execute)
        
        result = module.safe_execute({})
        assert result.status == 'failed'
        assert "Simulated error" in result.message
    
    def test_context_update_validation(self, module_fixture_factory):
        """Test context update validation"""
        module = module_fixture_factory('DataPipelineModule')
        
        # Should handle invalid context updates gracefully
        result = module.safe_execute({})
        assert result.context_updates is not None