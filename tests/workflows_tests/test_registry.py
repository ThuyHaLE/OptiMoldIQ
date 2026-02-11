# tests/workflows_tests/test_registry.py

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from optiMoldMaster.workflows.registry.registry import ModuleRegistry


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def registry_file(tmp_path):
    """Create temporary registry YAML file"""
    registry_path = tmp_path / "module_registry.yaml"
    return str(registry_path)


@pytest.fixture
def sample_registry_data():
    """Sample registry data"""
    return {
        "DataPipelineModule": {
            "config_path": "configs/pipeline.yaml",
            "enabled": True,
            "description": "Data pipeline module"
        },
        "AnalysisModule": {
            "config_path": "configs/analysis.yaml",
            "enabled": True,
            "description": "Analysis module"
        },
        "DisabledModule": {
            "config_path": "configs/disabled.yaml",
            "enabled": False,
            "description": "Disabled module"
        }
    }


@pytest.fixture
def create_registry_file(registry_file):
    """Helper to create registry file with content"""
    def _create(data):
        with open(registry_file, 'w') as f:
            yaml.dump(data, f)
        return registry_file
    return _create


@pytest.fixture
def mock_available_modules():
    """Mock AVAILABLE_MODULES"""
    return {
        "DataPipelineModule": Mock(),
        "AnalysisModule": Mock(),
        "DisabledModule": Mock(),
        "TestModule": Mock()
    }


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestRegistryInitialization:
    """Test ModuleRegistry initialization"""
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_initialization_with_valid_registry(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test successful initialization with valid registry file"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        assert registry.registry_path == registry_path
        assert len(registry.module_registry) == 3
        assert "DataPipelineModule" in registry.module_registry
        assert "AnalysisModule" in registry.module_registry
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_initialization_registry_not_found(
        self,
        mock_modules,
        mock_available_modules
    ):
        """Test initialization when registry file doesn't exist"""
        mock_modules.return_value = mock_available_modules
        
        with patch('optiMoldMaster.workflows.registry.registry.logger') as mock_logger:
            registry = ModuleRegistry(registry_path="nonexistent.yaml")
            
            assert registry.module_registry == {}
            assert mock_logger.warning.called
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_initialization_empty_registry_file(
        self,
        mock_modules,
        registry_file,
        mock_available_modules
    ):
        """Test initialization with empty registry file"""
        mock_modules.return_value = mock_available_modules
        
        # Create empty file
        Path(registry_file).write_text("")
        
        registry = ModuleRegistry(registry_path=registry_file)
        
        assert registry.module_registry == {}
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_initialization_invalid_yaml(
        self,
        mock_modules,
        registry_file,
        mock_available_modules
    ):
        """Test initialization with invalid YAML"""
        mock_modules.return_value = mock_available_modules
        
        # Create invalid YAML
        Path(registry_file).write_text("{ invalid yaml: [")
        
        with pytest.raises(yaml.YAMLError):
            ModuleRegistry(registry_path=registry_file)


# ============================================================================
# MODULE INSTANCE TESTS
# ============================================================================

class TestGetModuleInstance:
    """Test getting module instances"""
    
    @patch('optiMoldMaster.workflows.registry.registry.get_module')
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_instance_with_override_config(
        self,
        mock_modules,
        mock_get_module,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module with override config"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance
        mock_get_module.return_value = mock_module_class
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        instance = registry.get_module_instance(
            "DataPipelineModule",
            override_config_path="configs/override.yaml"
        )
        
        # Should use override config
        mock_module_class.assert_called_once_with("configs/override.yaml")
        assert instance == mock_module_instance
    
    @patch('optiMoldMaster.workflows.registry.registry.get_module')
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_instance_with_registry_config(
        self,
        mock_modules,
        mock_get_module,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module with registry config"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance
        mock_get_module.return_value = mock_module_class
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        instance = registry.get_module_instance("DataPipelineModule")
        
        # Should use registry config
        mock_module_class.assert_called_once_with("configs/pipeline.yaml")
        assert instance == mock_module_instance
    
    @patch('optiMoldMaster.workflows.registry.registry.get_module')
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_instance_no_config(
        self,
        mock_modules,
        mock_get_module,
        create_registry_file,
        mock_available_modules
    ):
        """Test getting module with no config"""
        mock_modules.return_value = mock_available_modules
        
        # Registry without config_path
        registry_data = {
            "TestModule": {
                "enabled": True
            }
        }
        registry_path = create_registry_file(registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance
        mock_get_module.return_value = mock_module_class
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        instance = registry.get_module_instance("TestModule")
        
        # Should use None as config
        mock_module_class.assert_called_once_with(None)
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_instance_not_available(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module that doesn't exist"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        with pytest.raises(ValueError, match="Module 'NonexistentModule' not found"):
            registry.get_module_instance("NonexistentModule")
    
    @patch('optiMoldMaster.workflows.registry.registry.get_module')
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_instance_not_in_registry(
        self,
        mock_modules,
        mock_get_module,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module available but not in registry"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance
        mock_get_module.return_value = mock_module_class
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        # TestModule is available but not in registry
        instance = registry.get_module_instance("TestModule")
        
        # Should work with None config
        mock_module_class.assert_called_once_with(None)
        assert instance == mock_module_instance


# ============================================================================
# MODULE LISTING TESTS
# ============================================================================

class TestListModules:
    """Test module listing functionality"""
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_list_modules_all(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test listing all available modules"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        modules = registry.list_modules(enabled_only=False)
        
        assert len(modules) == 4  # All modules in AVAILABLE_MODULES
        assert "DataPipelineModule" in modules
        assert "AnalysisModule" in modules
        assert "DisabledModule" in modules
        assert "TestModule" in modules
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_list_modules_enabled_only(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test listing only enabled modules"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        modules = registry.list_modules(enabled_only=True)
        
        assert len(modules) == 2  # Only enabled modules
        assert "DataPipelineModule" in modules
        assert "AnalysisModule" in modules
        assert "DisabledModule" not in modules
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_list_modules_empty_registry(
        self,
        mock_modules,
        mock_available_modules
    ):
        """Test listing modules with empty registry"""
        mock_modules.return_value = mock_available_modules
        
        registry = ModuleRegistry(registry_path="nonexistent.yaml")
        
        # All modules - returns from AVAILABLE_MODULES
        all_modules = registry.list_modules(enabled_only=False)
        assert len(all_modules) == 4
        
        # Enabled only - returns empty since nothing in registry
        enabled_modules = registry.list_modules(enabled_only=True)
        assert len(enabled_modules) == 0


# ============================================================================
# MODULE INFO TESTS
# ============================================================================

class TestGetModuleInfo:
    """Test getting module information"""
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_info_exists(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting info for existing module"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        info = registry.get_module_info("DataPipelineModule")
        
        assert info["config_path"] == "configs/pipeline.yaml"
        assert info["enabled"] is True
        assert info["description"] == "Data pipeline module"
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_info_not_in_registry(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting info for module not in registry"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        info = registry.get_module_info("TestModule")
        
        # Should return empty dict
        assert info == {}
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_get_module_info_not_available(
        self,
        mock_modules,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting info for non-existent module"""
        mock_modules.return_value = mock_available_modules
        registry_path = create_registry_file(sample_registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        
        with pytest.raises(ValueError, match="Module 'NonexistentModule' not found"):
            registry.get_module_info("NonexistentModule")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRegistryIntegration:
    """Integration tests for ModuleRegistry"""
    
    @patch('optiMoldMaster.workflows.registry.registry.get_module')
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_complete_registry_workflow(
        self,
        mock_modules,
        mock_get_module,
        create_registry_file,
        mock_available_modules
    ):
        """Test complete registry workflow"""
        mock_modules.return_value = mock_available_modules
        
        # Create comprehensive registry
        registry_data = {
            "Module1": {
                "config_path": "configs/module1.yaml",
                "enabled": True,
                "priority": 1
            },
            "Module2": {
                "config_path": "configs/module2.yaml",
                "enabled": True,
                "priority": 2
            },
            "Module3": {
                "enabled": False
            }
        }
        registry_path = create_registry_file(registry_data)
        
        # Setup mocks
        def create_mock_module(name):
            mock_class = Mock()
            mock_class.return_value = Mock(name=name)
            return mock_class
        
        mock_get_module.side_effect = [
            create_mock_module("Module1"),
            create_mock_module("Module2")
        ]
        
        # Initialize registry
        registry = ModuleRegistry(registry_path=registry_path)
        
        # List all modules
        all_modules = registry.list_modules()
        assert len(all_modules) > 0
        
        # List enabled modules
        enabled = registry.list_modules(enabled_only=True)
        assert "Module1" in enabled
        assert "Module2" in enabled
        assert "Module3" not in enabled
        
        # Get module instances
        instance1 = registry.get_module_instance("Module1")
        assert instance1.name == "Module1"
        
        instance2 = registry.get_module_instance("Module2")
        assert instance2.name == "Module2"
        
        # Get module info
        info1 = registry.get_module_info("Module1")
        assert info1["priority"] == 1


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_registry_with_unicode_paths(
        self,
        mock_modules,
        create_registry_file,
        mock_available_modules
    ):
        """Test registry with Unicode config paths"""
        mock_modules.return_value = mock_available_modules
        
        registry_data = {
            "TestModule": {
                "config_path": "配置/模块.yaml",
                "enabled": True
            }
        }
        registry_path = create_registry_file(registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        info = registry.get_module_info("TestModule")
        
        assert info["config_path"] == "配置/模块.yaml"
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_registry_with_special_characters(
        self,
        mock_modules,
        create_registry_file,
        mock_available_modules
    ):
        """Test registry with special characters in values"""
        mock_modules.return_value = mock_available_modules
        
        registry_data = {
            "TestModule": {
                "config_path": "configs/test-@#$%.yaml",
                "description": "Module with special chars: @#$%^&*()",
                "enabled": True
            }
        }
        registry_path = create_registry_file(registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        info = registry.get_module_info("TestModule")
        
        assert "@#$%" in info["config_path"]
        assert "@#$%^&*()" in info["description"]
    
    @patch('optiMoldMaster.workflows.registry.registry.AVAILABLE_MODULES')
    def test_registry_with_null_values(
        self,
        mock_modules,
        create_registry_file,
        mock_available_modules
    ):
        """Test registry with null/None values"""
        mock_modules.return_value = mock_available_modules
        
        registry_data = {
            "TestModule": {
                "config_path": None,
                "enabled": True,
                "description": None
            }
        }
        registry_path = create_registry_file(registry_data)
        
        registry = ModuleRegistry(registry_path=registry_path)
        info = registry.get_module_info("TestModule")
        
        assert info["config_path"] is None
        assert info["description"] is None