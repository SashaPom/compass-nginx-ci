import pytest

from probe_compass import read_target


@pytest.fixture(scope="session")
def target():
    return read_target()
