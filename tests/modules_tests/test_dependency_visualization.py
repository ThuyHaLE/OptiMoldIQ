# tests/modules_tests/test_dependency_visualization.py

"""
Dependency graph visualization and analysis tests
Helps understand module relationships
"""

import pytest
from typing import Dict, List, Set


class TestDependencyVisualization:
    """
    Tests that visualize and analyze module dependencies
    Useful for understanding the system architecture
    """
    
    @pytest.mark.smoke
    def test_print_all_module_dependencies(self,
                                           available_modules,
                                           module_registry,
                                           module_fixture_factory):
        """
        Print dependency tree for all modules
        Useful for documentation and debugging
        """
        print("\n" + "="*80)
        print("MODULE DEPENDENCY OVERVIEW")
        print("="*80)
        
        for module_name in sorted(available_modules.keys()):
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                deps = module.dependencies
                
                print(f"\n📦 {module_name}")
                if deps:
                    print(f"   Dependencies: {', '.join(deps)}")
                else:
                    print(f"   Dependencies: None (entry point)")
                
            except Exception as e:
                print(f"\n📦 {module_name}")
                print(f"   ❌ Error: {e}")
        
        print("\n" + "="*80)
    
    @pytest.mark.smoke
    def test_print_execution_orders(self,
                                    available_modules,
                                    module_registry,
                                    module_dependency_graph):
        """
        Print execution order for each module
        Shows dependency resolution
        """
        print("\n" + "="*80)
        print("MODULE EXECUTION ORDERS")
        print("="*80)
        
        for module_name in sorted(available_modules.keys()):
            if module_name not in module_registry:
                continue
            
            try:
                order = module_dependency_graph.get_execution_order(module_name)
                deps = module_dependency_graph.get_all_dependencies(module_name)
                
                print(f"\n🎯 {module_name}")
                print(f"   Execution Order: {' → '.join(order)}")
                print(f"   Direct Dependencies: {deps if deps else 'None'}")
                
            except Exception as e:
                print(f"\n🎯 {module_name}")
                print(f"   ❌ Error: {e}")
        
        print("\n" + "="*80)
    
    @pytest.mark.smoke
    def test_analyze_dependency_depth(self,
                                      available_modules,
                                      module_registry,
                                      module_dependency_graph):
        """
        Analyze dependency depth for each module
        Shows which modules are deepest in the dependency tree
        """
        print("\n" + "="*80)
        print("MODULE DEPENDENCY DEPTH ANALYSIS")
        print("="*80)
        
        depth_analysis = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                order = module_dependency_graph.get_execution_order(module_name)
                depth = len(order) - 1  # Exclude the module itself
                depth_analysis.append((module_name, depth, order))
            except:
                pass
        
        # Sort by depth
        depth_analysis.sort(key=lambda x: x[1])
        
        print("\n📊 Depth Analysis (0 = no dependencies):\n")
        for module_name, depth, order in depth_analysis:
            if depth == 0:
                print(f"   Depth {depth}: {module_name} (entry point)")
            else:
                print(f"   Depth {depth}: {module_name}")
                print(f"              Chain: {' → '.join(order)}")
        
        print("\n" + "="*80)
        
        # Statistics
        if depth_analysis:
            max_depth = max(d for _, d, _ in depth_analysis)
            avg_depth = sum(d for _, d, _ in depth_analysis) / len(depth_analysis)
            
            print("\n📈 Statistics:")
            print(f"   Total Modules: {len(depth_analysis)}")
            print(f"   Max Depth: {max_depth}")
            print(f"   Avg Depth: {avg_depth:.2f}")
            print(f"   Entry Points: {sum(1 for _, d, _ in depth_analysis if d == 0)}")
            print("="*80)
    
    @pytest.mark.smoke
    def test_find_dependency_patterns(self,
                                      available_modules,
                                      module_registry,
                                      module_fixture_factory):
        """
        Find common dependency patterns
        Shows which modules are most frequently depended upon
        """
        print("\n" + "="*80)
        print("DEPENDENCY PATTERN ANALYSIS")
        print("="*80)
        
        # Count how many times each module is depended upon
        dependency_count: Dict[str, int] = {}
        dependent_of: Dict[str, List[str]] = {}  # module -> list of dependents
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                for dep in module.dependencies:
                    dependency_count[dep] = dependency_count.get(dep, 0) + 1
                    
                    if dep not in dependent_of:
                        dependent_of[dep] = []
                    dependent_of[dep].append(module_name)
                    
            except:
                pass
        
        # Sort by frequency
        sorted_deps = sorted(dependency_count.items(), 
                           key=lambda x: x[1], 
                           reverse=True)
        
        print("\n🔗 Most Depended Upon Modules:\n")
        for dep, count in sorted_deps:
            print(f"   {dep}: used by {count} module(s)")
            print(f"      Dependents: {', '.join(dependent_of[dep])}")
        
        print("\n" + "="*80)
    
    @pytest.mark.smoke
    def test_check_for_orphan_modules(self,
                                      available_modules,
                                      module_registry,
                                      module_fixture_factory):
        """
        Check for modules that are not depended upon by anyone
        These might be final outputs or unused modules
        """
        print("\n" + "="*80)
        print("ORPHAN MODULE DETECTION")
        print("="*80)
        
        all_dependencies: Set[str] = set()
        
        # Collect all modules that are dependencies of others
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                all_dependencies.update(module.dependencies)
            except:
                pass
        
        # Find modules that are NOT in any dependency list
        orphans = []
        for module_name in available_modules.keys():
            if module_name not in all_dependencies:
                orphans.append(module_name)
        
        print("\n🏝️  Orphan Modules (not depended upon by anyone):\n")
        if orphans:
            for orphan in sorted(orphans):
                print(f"   - {orphan}")
            print("\n   These might be:")
            print("   • Final output modules")
            print("   • Unused/deprecated modules")
            print("   • Entry point modules")
        else:
            print("   None found - all modules are dependencies!")
        
        print("\n" + "="*80)


class TestDependencyIntegrity:
    """
    Tests that validate dependency integrity
    """
    
    @pytest.mark.smoke
    def test_all_dependencies_exist(self,
                                    available_modules,
                                    module_registry,
                                    module_fixture_factory):
        """
        Verify that all declared dependencies actually exist
        """
        print("\n" + "="*80)
        print("DEPENDENCY INTEGRITY CHECK")
        print("="*80)
        
        missing_deps = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                for dep in module.dependencies:
                    if dep not in available_modules:
                        missing_deps.append((module_name, dep))
                        print(f"\n❌ {module_name} depends on {dep} (NOT FOUND)")
            except Exception as e:
                print(f"\n⚠️  Could not check {module_name}: {e}")
        
        if not missing_deps:
            print("\n✅ All dependencies are valid!")
        
        print("\n" + "="*80)
        
        assert len(missing_deps) == 0, \
            f"Found {len(missing_deps)} missing dependencies: {missing_deps}"
    
    @pytest.mark.smoke
    def test_no_self_dependencies(self,
                                  available_modules,
                                  module_registry,
                                  module_fixture_factory):
        """
        Check that no module depends on itself
        """
        self_deps = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                if module_name in module.dependencies:
                    self_deps.append(module_name)
            except:
                pass
        
        assert len(self_deps) == 0, \
            f"Found self-dependencies: {self_deps}"