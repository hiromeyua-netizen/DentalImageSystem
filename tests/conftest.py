"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def test_data_dir():
    """Return the test data directory path."""
    return TEST_DATA_DIR
