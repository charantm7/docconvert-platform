from unittest.mock import MagicMock

from api_gateway.authentication.database.repository import UserRepository

def test_get_user_by_id():
    mock_db = MagicMock()

    mock_db.get.return_value = {
        "id": 1,
        "email": "test@gmail.com"
    }

    repo = UserRepository(mock_db)

    result = repo.get_by_id(1)

    assert result["id"] == 1

def test_get_user_by_email():
    mock_db = MagicMock()

    mock_execute = MagicMock()
    mock_scalars = MagicMock()

    mock_db.execute.return_value = mock_execute
    mock_execute.scalars.return_value = mock_scalars

    mock_scalars.first.return_value = {
        "id": 1,
        "email": "test@gmail.com"
    }

    repo = UserRepository(mock_db)
    result = repo.get_by_email("test@gmail.com")

    assert result["email"] == "test@gmail.com"