import pytest


@pytest.fixture(autouse=True)
def clear_database():
    pass


@pytest.fixture(scope="session", autouse=True)
def wait_for_postgres_fixture():
    pass
