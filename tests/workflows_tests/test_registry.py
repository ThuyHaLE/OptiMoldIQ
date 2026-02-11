# tests/workflows_tests/test_registry.py

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from workflows.registry.registry import ModuleRegistry

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
    
    def test_initialization_with_valid_registry(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test successful initialization with valid registry file"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
        
            assert registry.registry_path == registry_path
            assert len(registry.module_registry) == 3
            assert "DataPipelineModule" in registry.module_registry
            assert "AnalysisModule" in registry.module_registry
    
    def test_initialization_registry_not_found(
        self,
        mock_available_modules
    ):
        """Test initialization when registry file doesn't exist"""
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            with patch('workflows.registry.registry.logger') as mock_logger:
                registry = ModuleRegistry(registry_path="nonexistent.yaml")
                
                assert registry.module_registry == {}
                assert mock_logger.warning.called
    
    def test_initialization_empty_registry_file(
        self,
        registry_file,
        mock_available_modules
    ):
        """Test initialization with empty registry file"""
        # Create empty file
        Path(registry_file).write_text("")
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_file)
        
            assert registry.module_registry == {}
    
    def test_initialization_invalid_yaml(
        self,
        registry_file,
        mock_available_modules
    ):
        """Test initialization with invalid YAML"""
        # Create invalid YAML
        Path(registry_file).write_text("{ invalid yaml: [")
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            with pytest.raises(yaml.YAMLError):
                ModuleRegistry(registry_path=registry_file)


# ============================================================================
# MODULE INSTANCE TESTS
# ============================================================================

class TestGetModuleInstance:
    """Test getting module instances"""
    
    def test_get_module_instance_with_override_config(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module with override config"""
        registry_path = create_registry_file(sample_registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance

        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ), patch(
            'workflows.registry.registry.modules_package.get_module',
            return_value=mock_module_class
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            
            instance = registry.get_module_instance(
                "DataPipelineModule",
                override_config_path="configs/override.yaml"
            )
            
            # Should use override config
            mock_module_class.assert_called_once_with("configs/override.yaml")
            assert instance == mock_module_instance
    
    def test_get_module_instance_with_registry_config(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module with registry config"""
        registry_path = create_registry_file(sample_registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance

        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ), patch(
            'workflows.registry.registry.modules_package.get_module',
            return_value=mock_module_class
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            
            instance = registry.get_module_instance("DataPipelineModule")
            
            # Should use registry config
            mock_module_class.assert_called_once_with("configs/pipeline.yaml")
            assert instance == mock_module_instance
    
    def test_get_module_instance_no_config(
        self,
        create_registry_file,
        mock_available_modules
    ):
        """Test getting module with no config"""
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

        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ), patch(
            'workflows.registry.registry.modules_package.get_module',
            return_value=mock_module_class
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            
            instance = registry.get_module_instance("TestModule")
            
            # Should use None as config
            mock_module_class.assert_called_once_with(None)
    
    def test_get_module_instance_not_available(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module that doesn't exist"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            
            with pytest.raises(ValueError, match="Module 'NonexistentModule' not found"):
                registry.get_module_instance("NonexistentModule")
    
    def test_get_module_instance_not_in_registry(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting module available but not in registry"""
        registry_path = create_registry_file(sample_registry_data)
        
        # Setup mock
        mock_module_class = Mock()
        mock_module_instance = Mock()
        mock_module_class.return_value = mock_module_instance

        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ), patch(
            'workflows.registry.registry.modules_package.get_module',
            return_value=mock_module_class
        ):
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
    
    def test_list_modules_all(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test listing all available modules"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            modules = registry.list_modules(enabled_only=False)
        
            assert len(modules) == 4  # All modules in AVAILABLE_MODULES
            assert "DataPipelineModule" in modules
            assert "AnalysisModule" in modules
            assert "DisabledModule" in modules
            assert "TestModule" in modules
    
    def test_list_modules_enabled_only(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test listing only enabled modules"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            modules = registry.list_modules(enabled_only=True)
        
            assert len(modules) == 2  # Only enabled modules
            assert "DataPipelineModule" in modules
            assert "AnalysisModule" in modules
            assert "DisabledModule" not in modules
    
    def test_list_modules_empty_registry(
        self,
        mock_available_modules
    ):
        """Test listing modules with empty registry"""
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
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
    
    def test_get_module_info_exists(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting info for existing module"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            info = registry.get_module_info("DataPipelineModule")
        
            assert info["config_path"] == "configs/pipeline.yaml"
            assert info["enabled"] is True
            assert info["description"] == "Data pipeline module"
    
    def test_get_module_info_not_in_registry(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting info for module not in registry"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            info = registry.get_module_info("TestModule")
        
            # Should return empty dict
            assert info == {}
    
    def test_get_module_info_not_available(
        self,
        create_registry_file,
        sample_registry_data,
        mock_available_modules
    ):
        """Test getting info for non-existent module"""
        registry_path = create_registry_file(sample_registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            
            with pytest.raises(ValueError, match="Module 'NonexistentModule' not found"):
                registry.get_module_info("NonexistentModule")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRegistryIntegration:
    """Integration tests for ModuleRegistry"""
    
    def test_complete_registry_workflow(
        self,
        create_registry_file,
        mock_available_modules
    ):
        """Test complete registry workflow"""
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
        
        # Setup mocks - create mock modules for Module1, Module2, Module3
        def create_mock_module(name):
            mock_class = Mock()
            mock_class.return_value = Mock(name=name)
            return mock_class
        
        # Create mock module classes
        module1_class = create_mock_module("Module1")
        module2_class = create_mock_module("Module2")
        module3_class = create_mock_module("Module3")
        
        # Add our test modules to the available modules
        test_available_modules = {
            **mock_available_modules,
            "Module1": Mock(),
            "Module2": Mock(),
            "Module3": Mock()
        }
        
        # Mock get_module to return the appropriate class
        def mock_get_module(name):
            if name == "Module1":
                return module1_class
            elif name == "Module2":
                return module2_class
            elif name == "Module3":
                return module3_class
            raise ValueError(f"Module '{name}' not found")

        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            test_available_modules
        ), patch(
            'workflows.registry.registry.modules_package.get_module',
            side_effect=mock_get_module
        ):
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
    
    def test_registry_with_unicode_paths(
        self,
        create_registry_file,
        mock_available_modules
    ):
        """Test registry with Unicode config paths"""
        registry_data = {
            "TestModule": {
                "config_path": "配置/模块.yaml",
                "enabled": True
            }
        }
        registry_path = create_registry_file(registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            info = registry.get_module_info("TestModule")
        
            assert info["config_path"] == "配置/模块.yaml"
    
    def test_registry_with_special_characters(
        self,
        create_registry_file,
        mock_available_modules
    ):
        """Test registry with special characters in values"""
        registry_data = {
            "TestModule": {
                "config_path": "configs/test-@#$%.yaml",
                "description": "Module with special chars: @#$%^&*()",
                "enabled": True
            }
        }
        registry_path = create_registry_file(registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            info = registry.get_module_info("TestModule")
        
            assert "@#$%" in info["config_path"]
            assert "@#$%^&*()" in info["description"]
    
    def test_registry_with_null_values(
        self,
        create_registry_file,
        mock_available_modules
    ):
        """Test registry with null/None values"""
        registry_data = {
            "TestModule": {
                "config_path": None,
                "enabled": True,
                "description": None
            }
        }
        registry_path = create_registry_file(registry_data)
        
        with patch(
            'workflows.registry.registry.modules_package.AVAILABLE_MODULES',
            mock_available_modules
        ):
            registry = ModuleRegistry(registry_path=registry_path)
            info = registry.get_module_info("TestModule")
        
            assert info["config_path"] is None
            assert info["description"] is None