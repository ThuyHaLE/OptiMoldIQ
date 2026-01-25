"""
Dependency graph visualization and analysis tests
Helps understand module relationships and architecture

All modules inherit from BaseModule and this test suite validates:
- Dependency declarations (BaseModule.dependencies)
- Execution order resolution
- Circular dependency detection
- Architecture patterns
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from modules.base_module import BaseModule, ModuleResult


# ============================================================================
# DEPENDENCY VISUALIZATION TESTS
# ============================================================================

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
        print("\nAll modules inherit from BaseModule and declare dependencies via")
        print("the 'dependencies' property (Dict[str, str])")
        print("="*80)
        
        modules_data = []
        
        for module_name in sorted(available_modules.keys()):
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                
                # Validate it's a BaseModule
                assert isinstance(module, BaseModule), \
                    f"{module_name} must inherit from BaseModule"
                
                deps = module.dependencies
                outputs = module.context_outputs
                
                modules_data.append({
                    'name': module_name,
                    'dependencies': deps,
                    'outputs': outputs,
                    'has_deps': bool(deps)
                })
                
                print(f"\n📦 {module_name}")
                print(f"   Type: {module.__class__.__name__}")
                print(f"   Inherits from: BaseModule ✓")
                
                if deps:
                    print(f"   Dependencies ({len(deps)}):")
                    for dep_name, dep_output in deps.items():
                        print(f"      • {dep_name} → {dep_output}")
                else:
                    print(f"   Dependencies: None (entry point)")
                
                if outputs:
                    print(f"   Context Outputs ({len(outputs)}): {', '.join(outputs)}")
                else:
                    print(f"   Context Outputs: None")
                
            except pytest.skip.Exception:
                # Skip is ok
                continue
            except Exception as e:
                pytest.fail(f"Failed to analyze {module_name}: {e}")
        
        print("\n" + "="*80)
        print(f"Total modules analyzed: {len(modules_data)}")
        print("="*80)
    
    @pytest.mark.smoke
    def test_print_execution_orders(self,
                                    available_modules,
                                    module_registry,
                                    module_dependency_graph):
        """
        Print execution order for each module
        Shows dependency resolution based on BaseModule.dependencies
        """
        print("\n" + "="*80)
        print("MODULE EXECUTION ORDERS")
        print("="*80)
        print("\nExecution order is computed from BaseModule.dependencies")
        print("Dependencies are executed first, then the module itself")
        print("="*80)
        
        for module_name in sorted(available_modules.keys()):
            if module_name not in module_registry:
                continue
            
            try:
                order = module_dependency_graph.get_execution_order(module_name)
                deps = module_dependency_graph.get_all_dependencies(module_name)
                
                print(f"\n🎯 {module_name}")
                print(f"   Execution Order: {' → '.join(order)}")
                print(f"   All Dependencies: {deps if deps else 'None'}")
                print(f"   Dependency Depth: {len(deps)}")
                
            except ValueError as e:
                # Circular dependency or other validation error
                print(f"\n🎯 {module_name}")
                print(f"   ❌ ERROR: {e}")
                pytest.fail(f"Dependency resolution failed for {module_name}: {e}")
            except Exception as e:
                pytest.fail(f"Unexpected error for {module_name}: {e}")
        
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
            except Exception as e:
                pytest.fail(f"Failed to analyze depth for {module_name}: {e}")
        
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
            entry_points = sum(1 for _, d, _ in depth_analysis if d == 0)
            
            print("\n📈 Statistics:")
            print(f"   Total Modules: {len(depth_analysis)}")
            print(f"   Entry Points (no deps): {entry_points}")
            print(f"   Max Depth: {max_depth}")
            print(f"   Avg Depth: {avg_depth:.2f}")
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
        print("\nAnalyzing BaseModule.dependencies across all modules")
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
                    
            except pytest.skip.Exception:
                continue
            except Exception as e:
                pytest.fail(f"Failed to analyze patterns for {module_name}: {e}")
        
        # Sort by frequency
        sorted_deps = sorted(dependency_count.items(), 
                           key=lambda x: x[1], 
                           reverse=True)
        
        print("\n🔗 Most Depended Upon Modules:\n")
        if sorted_deps:
            for dep, count in sorted_deps:
                print(f"   {dep}: used by {count} module(s)")
                print(f"      Dependents: {', '.join(sorted(dependent_of[dep]))}")
        else:
            print("   No dependencies found (all modules are independent)")
        
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
        print("\nModules not listed in any BaseModule.dependencies")
        print("="*80)
        
        all_dependencies: Set[str] = set()
        
        # Collect all modules that are dependencies of others
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                all_dependencies.update(module.dependencies.keys())
            except pytest.skip.Exception:
                continue
            except Exception as e:
                pytest.fail(f"Failed to check orphans for {module_name}: {e}")
        
        # Find modules that are NOT in any dependency list
        orphans = []
        for module_name in available_modules.keys():
            if module_name not in all_dependencies:
                orphans.append(module_name)
        
        print("\n🏝️  Orphan Modules (not depended upon by anyone):\n")
        if orphans:
            for orphan in sorted(orphans):
                print(f"   - {orphan}")
            print("\n   💡 These might be:")
            print("   • Final output/pipeline modules")
            print("   • Standalone tools")
            print("   • Entry point modules")
            print("   • Unused/deprecated modules (verify!)")
        else:
            print("   None found - all modules have dependents!")
        
        print("\n" + "="*80)
    
    @pytest.mark.smoke
    def test_visualize_circular_dependencies(self,
                                            available_modules,
                                            module_registry,
                                            module_dependency_graph):
        """
        Check for and visualize any circular dependencies
        """
        print("\n" + "="*80)
        print("CIRCULAR DEPENDENCY DETECTION")
        print("="*80)
        print("\nChecking for cycles in BaseModule.dependencies")
        print("="*80)
        
        circular_found = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module_dependency_graph.get_execution_order(module_name)
            except ValueError as e:
                if "circular" in str(e).lower():
                    circular_found.append((module_name, str(e)))
                    print(f"\n❌ CIRCULAR DEPENDENCY DETECTED:")
                    print(f"   Module: {module_name}")
                    print(f"   Error: {e}")
        
        if not circular_found:
            print("\n✅ No circular dependencies found!")
            print("   All dependency chains are acyclic (DAG)")
        else:
            print(f"\n❌ Found {len(circular_found)} circular dependency issue(s)")
        
        print("\n" + "="*80)
        
        # Assert no circular dependencies
        assert len(circular_found) == 0, \
            f"Circular dependencies detected in: {[m for m, _ in circular_found]}"


# ============================================================================
# DEPENDENCY INTEGRITY TESTS
# ============================================================================

class TestDependencyIntegrity:
    """
    Tests that validate dependency integrity
    Ensures BaseModule.dependencies are valid
    """
    
    @pytest.mark.smoke
    def test_all_dependencies_exist(self,
                                    available_modules,
                                    module_registry,
                                    module_fixture_factory):
        """
        Verify that all declared dependencies actually exist
        Tests that BaseModule.dependencies references valid modules
        """
        print("\n" + "="*80)
        print("DEPENDENCY INTEGRITY CHECK")
        print("="*80)
        print("\nValidating all BaseModule.dependencies point to existing modules")
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
                        print(f"\n❌ {module_name} depends on '{dep}' (NOT FOUND)")
                        
            except pytest.skip.Exception:
                continue
            except Exception as e:
                pytest.fail(f"Failed to check dependencies for {module_name}: {e}")
        
        if not missing_deps:
            print("\n✅ All dependencies are valid!")
            print("   All BaseModule.dependencies point to existing modules")
        else:
            print(f"\n❌ Found {len(missing_deps)} missing dependencies")
        
        print("\n" + "="*80)
        
        assert len(missing_deps) == 0, \
            f"Missing dependencies: {missing_deps}"
    
    @pytest.mark.smoke
    def test_no_self_dependencies(self,
                                  available_modules,
                                  module_registry,
                                  module_fixture_factory):
        """
        Check that no module depends on itself
        Tests BaseModule.dependencies doesn't include self-reference
        """
        print("\n" + "="*80)
        print("SELF-DEPENDENCY CHECK")
        print("="*80)
        
        self_deps = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                
                if module_name in module.dependencies:
                    self_deps.append(module_name)
                    print(f"\n❌ {module_name} depends on itself!")
                    
            except pytest.skip.Exception:
                continue
            except Exception as e:
                pytest.fail(f"Failed to check self-dependency for {module_name}: {e}")
        
        if not self_deps:
            print("\n✅ No self-dependencies found!")
        
        print("\n" + "="*80)
        
        assert len(self_deps) == 0, \
            f"Modules with self-dependencies: {self_deps}"
    
    @pytest.mark.smoke
    def test_dependency_types(self,
                             available_modules,
                             module_registry,
                             module_fixture_factory):
        """
        Validate that dependencies property returns correct type
        BaseModule.dependencies should be Dict[str, str]
        """
        print("\n" + "="*80)
        print("DEPENDENCY TYPE VALIDATION")
        print("="*80)
        print("\nValidating BaseModule.dependencies returns Dict[str, str]")
        print("="*80)
        
        type_errors = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                
                # Check dependencies is a dict
                if not isinstance(module.dependencies, dict):
                    type_errors.append(
                        (module_name, f"dependencies is {type(module.dependencies)}, not dict")
                    )
                    continue
                
                # Check each key-value pair
                for dep_name, dep_output in module.dependencies.items():
                    if not isinstance(dep_name, str):
                        type_errors.append(
                            (module_name, f"dependency key '{dep_name}' is {type(dep_name)}, not str")
                        )
                    
                    if dep_output is None:
                        type_errors.append(
                            (module_name, f"dependency output for '{dep_name}' is None")
                        )
                        
            except pytest.skip.Exception:
                continue
            except Exception as e:
                pytest.fail(f"Failed to check types for {module_name}: {e}")
        
        if type_errors:
            print("\n❌ Type errors found:")
            for module_name, error in type_errors:
                print(f"   {module_name}: {error}")
        else:
            print("\n✅ All dependency types are valid!")
        
        print("\n" + "="*80)
        
        assert len(type_errors) == 0, \
            f"Type validation errors: {type_errors}"
    
    @pytest.mark.smoke
    def test_context_outputs_types(self,
                                   available_modules,
                                   module_registry,
                                   module_fixture_factory):
        """
        Validate that context_outputs property returns correct type
        BaseModule.context_outputs should be List[str]
        """
        print("\n" + "="*80)
        print("CONTEXT OUTPUTS TYPE VALIDATION")
        print("="*80)
        print("\nValidating BaseModule.context_outputs returns List[str]")
        print("="*80)
        
        type_errors = []
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                
                # Check context_outputs is a list
                if not isinstance(module.context_outputs, list):
                    type_errors.append(
                        (module_name, f"context_outputs is {type(module.context_outputs)}, not list")
                    )
                    continue
                
                # Check each item is string
                for output in module.context_outputs:
                    if not isinstance(output, str):
                        type_errors.append(
                            (module_name, f"context_output '{output}' is {type(output)}, not str")
                        )
                        
            except pytest.skip.Exception:
                continue
            except Exception as e:
                pytest.fail(f"Failed to check context_outputs for {module_name}: {e}")
        
        if type_errors:
            print("\n❌ Type errors found:")
            for module_name, error in type_errors:
                print(f"   {module_name}: {error}")
        else:
            print("\n✅ All context_outputs types are valid!")
        
        print("\n" + "="*80)
        
        assert len(type_errors) == 0, \
            f"Context outputs type errors: {type_errors}"


# ============================================================================
# DEPENDENCY EXPORT TESTS
# ============================================================================

class TestDependencyExport:
    """
    Export dependency graphs to various formats
    Useful for documentation and visualization
    """
    
    @pytest.mark.smoke
    def test_export_dependency_graph_json(self,
                                          available_modules,
                                          module_registry,
                                          module_fixture_factory,
                                          tmp_path):
        """
        Export complete dependency graph to JSON
        """
        print("\n" + "="*80)
        print("EXPORTING DEPENDENCY GRAPH TO JSON")
        print("="*80)
        
        graph_data = {
            'modules': {},
            'metadata': {
                'total_modules': 0,
                'total_dependencies': 0,
                'entry_points': [],
                'orphans': []
            }
        }
        
        all_dependencies = set()
        
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                
                deps = dict(module.dependencies)
                outputs = list(module.context_outputs)
                
                graph_data['modules'][module_name] = {
                    'dependencies': deps,
                    'context_outputs': outputs,
                    'is_entry_point': len(deps) == 0
                }
                
                all_dependencies.update(deps.keys())
                
            except pytest.skip.Exception:
                continue
        
        # Compute metadata
        graph_data['metadata']['total_modules'] = len(graph_data['modules'])
        graph_data['metadata']['total_dependencies'] = len(all_dependencies)
        
        # Find entry points
        for module_name, data in graph_data['modules'].items():
            if data['is_entry_point']:
                graph_data['metadata']['entry_points'].append(module_name)
        
        # Find orphans
        for module_name in graph_data['modules'].keys():
            if module_name not in all_dependencies:
                graph_data['metadata']['orphans'].append(module_name)
        
        # Export to file
        output_file = tmp_path / "dependency_graph.json"
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        print(f"\n✅ Exported dependency graph to: {output_file}")
        print(f"   Total modules: {graph_data['metadata']['total_modules']}")
        print(f"   Entry points: {len(graph_data['metadata']['entry_points'])}")
        print(f"   Orphans: {len(graph_data['metadata']['orphans'])}")
        print("="*80)
        
        assert output_file.exists()
    
    @pytest.mark.smoke
    def test_export_mermaid_diagram(self,
                                    available_modules,
                                    module_registry,
                                    module_fixture_factory,
                                    tmp_path):
        """
        Export dependency graph as Mermaid diagram
        Can be rendered in Markdown/documentation
        """
        print("\n" + "="*80)
        print("EXPORTING MERMAID DEPENDENCY DIAGRAM")
        print("="*80)
        
        lines = [
            "```mermaid",
            "graph TD",
            "    %% Module Dependency Graph",
            "    %% Generated from BaseModule.dependencies",
            ""
        ]
        
        # Collect all relationships
        for module_name in sorted(available_modules.keys()):
            if module_name not in module_registry:
                continue
            
            try:
                module = module_fixture_factory(module_name)
                
                if module.dependencies:
                    for dep in sorted(module.dependencies.keys()):
                        lines.append(f"    {dep} --> {module_name}")
                else:
                    # Entry point - show it standalone
                    lines.append(f"    {module_name}:::entryPoint")
                    
            except pytest.skip.Exception:
                continue
        
        lines.append("")
        lines.append("    %% Styling")
        lines.append("    classDef entryPoint fill:#90EE90,stroke:#333,stroke-width:2px")
        lines.append("```")
        
        # Export to file
        output_file = tmp_path / "dependency_graph.mmd"
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✅ Exported Mermaid diagram to: {output_file}")
        print("\n📝 Preview:")
        print('\n'.join(lines[:20]))
        if len(lines) > 20:
            print(f"    ... ({len(lines) - 20} more lines)")
        print("="*80)
        
        assert output_file.exists()


# ============================================================================
# ARCHITECTURE VALIDATION TESTS
# ============================================================================

class TestArchitectureValidation:
    """
    High-level architecture validation
    Ensures module system follows best practices
    """
    
    @pytest.mark.smoke
    def test_validate_architecture_principles(self,
                                              available_modules,
                                              module_registry,
                                              module_fixture_factory,
                                              module_dependency_graph):
        """
        Validate that architecture follows best practices
        """
        print("\n" + "="*80)
        print("ARCHITECTURE VALIDATION")
        print("="*80)
        print("\nValidating BaseModule-based architecture")
        print("="*80)
        
        issues = []
        warnings = []
        
        # Check 1: All modules inherit from BaseModule
        print("\n✓ Checking: All modules inherit from BaseModule")
        for module_name in available_modules.keys():
            module_class = available_modules[module_name]
            if not issubclass(module_class, BaseModule):
                issues.append(f"{module_name} doesn't inherit from BaseModule")
        
        if not issues:
            print("  ✅ PASS")
        
        # Check 2: No circular dependencies
        print("\n✓ Checking: No circular dependencies")
        try:
            circular = module_dependency_graph.has_circular_dependencies()
            if circular:
                issues.append("Circular dependencies detected")
            else:
                print("  ✅ PASS")
        except Exception as e:
            issues.append(f"Failed to check circular dependencies: {e}")
        
        # Check 3: At least one entry point exists
        print("\n✓ Checking: At least one entry point exists")
        entry_points = 0
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            try:
                module = module_fixture_factory(module_name)
                if not module.dependencies:
                    entry_points += 1
            except pytest.skip.Exception:
                continue
        
        if entry_points == 0:
            warnings.append("No entry points found (all modules have dependencies)")
        else:
            print(f"  ✅ PASS - Found {entry_points} entry point(s)")
        
        # Check 4: Dependency depth is reasonable
        print("\n✓ Checking: Dependency depth is reasonable (< 10)")
        max_depth = 0
        for module_name in available_modules.keys():
            if module_name not in module_registry:
                continue
            try:
                order = module_dependency_graph.get_execution_order(module_name)
                depth = len(order) - 1
                max_depth = max(max_depth, depth)
            except:
                pass
        
        if max_depth > 10:
            warnings.append(f"Max dependency depth is {max_depth} (> 10)")
        else:
            print(f"  ✅ PASS - Max depth: {max_depth}")
        
        # Summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        if issues:
            print(f"\n❌ {len(issues)} critical issue(s):")
            for issue in issues:
                print(f"   • {issue}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"   • {warning}")
        
        if not issues and not warnings:
            print("\n✅ Architecture validation passed!")
            print("   All BaseModule implementations follow best practices")
        
        print("="*80)
        
        assert len(issues) == 0, f"Architecture validation failed: {issues}"