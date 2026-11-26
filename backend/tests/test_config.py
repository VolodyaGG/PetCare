import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_reject_non_postgres_database():
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite:///test.db", _env_file=None)


@pytest.mark.parametrize("timeout", [0, 31])
def test_timeout_bounds(timeout):
    with pytest.raises(ValidationError):
        Settings(db_connect_timeout=timeout, _env_file=None)
