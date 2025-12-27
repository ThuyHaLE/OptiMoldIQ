# tests/conftest.py - Root conftest (shared by ALL tests)
"""
Root conftest - shared fixtures for both agent_tests and module_tests
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Project root path - available to all tests"""
    return PROJECT_ROOT