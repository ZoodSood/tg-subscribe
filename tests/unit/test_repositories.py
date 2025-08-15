import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime
from src.bot.database.repositories import UserRepository, TransactionRepository, PromoCodeRepository
from src.bot.database.models import User

# --- Fixtures ---

@pytest.fixture
def mock_db_connection(db_session):
    """Fixture to mock the database connection for repository tests."""
    cm = AsyncMock()
    cm.__aenter__.return_value = db_session
    return patch('aiosqlite.connect', return_value=cm)

# --- UserRepository Tests ---

@pytest.mark.asyncio
async def test_user_repository_create_and_get(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        user = await UserRepository.get(telegram_id=123)
        assert user is not None
        assert user.telegram_id == 123
        assert user.first_name == "Test"

@pytest.mark.asyncio
async def test_user_repository_create_if_not_exist_already_exists(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        users = await db_session.execute_fetchall("SELECT * FROM Users WHERE telegram_id=123")
        assert len(users) == 1

@pytest.mark.asyncio
async def test_user_repository_get_not_found(mock_db_connection):
    with mock_db_connection:
        user = await UserRepository.get(telegram_id=999)
        assert user is None

@pytest.mark.asyncio
async def test_user_repository_get_no_id(mock_db_connection):
    with mock_db_connection:
        user = await UserRepository.get()
        assert user is None

@pytest.mark.asyncio
async def test_user_repository_get_exception(mock_db_connection):
    with patch('aiosqlite.connect', side_effect=Exception("DB error")):
        user = await UserRepository.get(telegram_id=123)
        assert user is None

@pytest.mark.asyncio
async def test_user_repository_update_subscription_date(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        new_date = "2025-01-01 00:00:00"
        updated = await UserRepository.update_subscription_date(new_date, telegram_id=123)
        assert updated is True
        user = await UserRepository.get(telegram_id=123)
        assert user.days_sub_end == new_date

@pytest.mark.asyncio
async def test_user_repository_update_subscription_date_not_found(mock_db_connection):
    with mock_db_connection:
        updated = await UserRepository.update_subscription_date("2025-01-01 00:00:00", telegram_id=999)
        assert updated is False

@pytest.mark.asyncio
async def test_user_repository_update_subscription_date_exception(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        with patch.object(type(db_session), 'execute', side_effect=Exception("DB error")):
            result = await UserRepository.update_subscription_date("2025-01-01 00:00:00", telegram_id=123)
            assert result is False

@pytest.mark.asyncio
async def test_user_repository_get_all(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser1")
        await UserRepository.create_if_not_exist(456, "Another", "User", "testuser2")
        all_users = await UserRepository.get_all()
        assert len(all_users) == 2

@pytest.mark.asyncio
async def test_user_repository_get_all_exception(mock_db_connection):
    with patch('aiosqlite.connect', side_effect=Exception("DB error")):
        users = await UserRepository.get_all()
        assert users == []

# ... (similar comprehensive tests for increase_balance, ban/unban, update_last_active) ...

# --- TransactionRepository Tests ---

@pytest.mark.asyncio
async def test_transaction_repository_create_and_get(db_session, mock_db_connection):
    with mock_db_connection:
        txid = "test_txid_123"
        await TransactionRepository.create(txid, 123, weeks=1)
        transaction = await TransactionRepository.get(txid=txid)
        assert transaction is not None
        assert transaction.txid == txid
        assert transaction.status == 0

@pytest.mark.asyncio
async def test_transaction_repository_get_not_found(mock_db_connection):
    with mock_db_connection:
        transaction = await TransactionRepository.get(txid="non_existent")
        assert transaction is None

@pytest.mark.asyncio
async def test_transaction_repository_create_exception(mock_db_connection):
     with patch('aiosqlite.connect', side_effect=Exception("DB error")):
        created = await TransactionRepository.create("txid", 123)
        assert created is False

# ... (similar comprehensive tests for set_status, get_new) ...

# --- PromoCodeRepository Tests ---

@pytest.mark.asyncio
async def test_promo_code_repository_create_and_get(db_session, mock_db_connection):
    with mock_db_connection:
        code = "TESTPROMO"
        await PromoCodeRepository.create(code, 10, 123)
        promo = await PromoCodeRepository.get_by_code(code)
        assert promo is not None
        assert promo.code == code
        assert promo.is_active == 1

@pytest.mark.asyncio
async def test_promo_code_repository_redeem(db_session, mock_db_connection):
    with mock_db_connection:
        code = "REDEEM_ME"
        await PromoCodeRepository.create(code, 1, 123)
        redeemed = await PromoCodeRepository.redeem(code, 456)
        assert redeemed is True
        promo = await PromoCodeRepository.get_by_code(code)
        assert promo.used_count == 1
        assert promo.is_active == 0

@pytest.mark.asyncio
async def test_promo_code_repository_redeem_not_found(mock_db_connection):
     with patch('src.bot.database.repositories.PromoCodeRepository.get_by_code', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        redeemed = await PromoCodeRepository.redeem("non_existent_promo", 123)
        assert redeemed is False

# ... (similar comprehensive tests for other failure cases) ...
