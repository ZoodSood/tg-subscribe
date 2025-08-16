import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime
from src.bot.database.repositories import UserRepository, TransactionRepository, PromoCodeRepository
from src.bot.database.models import User, Transaction, PromoCode

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

# --- More UserRepository Tests ---

@pytest.mark.asyncio
async def test_user_repository_increase_balance_by(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        user_before = await UserRepository.get(telegram_id=123)
        await UserRepository.increase_balance_by(100, telegram_id=123)
        user_after = await UserRepository.get(telegram_id=123)
        assert user_after.balance == user_before.balance + 100

@pytest.mark.asyncio
async def test_user_repository_ban_and_unban_user(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        await UserRepository.ban_user(telegram_id=123)
        user_banned = await UserRepository.get(telegram_id=123)
        assert user_banned.is_banned == 1
        await UserRepository.unban_user(telegram_id=123)
        user_unbanned = await UserRepository.get(telegram_id=123)
        assert user_unbanned.is_banned == 0

@pytest.mark.asyncio
async def test_user_repository_update_last_active(db_session, mock_db_connection):
    with mock_db_connection:
        await UserRepository.create_if_not_exist(123, "Test", "User", "testuser")
        timestamp = "2025-01-01 12:34:56"
        await UserRepository.update_last_active(telegram_id=123, timestamp=timestamp)
        user = await UserRepository.get(telegram_id=123)
        assert user.last_active == timestamp

# --- More TransactionRepository Tests ---

@pytest.mark.asyncio
async def test_transaction_repository_set_status(db_session, mock_db_connection):
    with mock_db_connection:
        await TransactionRepository.create("txid_status", 123)
        await TransactionRepository.set_status(True, txid="txid_status")
        tx = await TransactionRepository.get(txid="txid_status")
        assert tx.status == 1

@pytest.mark.asyncio
async def test_transaction_repository_get_new(db_session, mock_db_connection):
    with mock_db_connection:
        await TransactionRepository.create("new_tx", 123)
        new_txs = await TransactionRepository.get_new()
        assert len(new_txs) == 1
        assert new_txs[0].txid == "new_tx"

# --- More PromoCodeRepository Tests ---

@pytest.mark.asyncio
async def test_promo_code_repository_redeem_inactive(db_session, mock_db_connection):
    with mock_db_connection:
        await PromoCodeRepository.create("INACTIVE", 1, 123)
        await db_session.execute("UPDATE PromoCodes SET is_active = 0 WHERE code = 'INACTIVE'")
        await db_session.commit()
        redeemed = await PromoCodeRepository.redeem("INACTIVE", 456)
        assert redeemed is False

@pytest.mark.asyncio
async def test_promo_code_repository_redeem_max_uses(db_session, mock_db_connection):
    with mock_db_connection:
        await PromoCodeRepository.create("MAXED", 1, 123)
        await PromoCodeRepository.redeem("MAXED", 456)
        redeemed_again = await PromoCodeRepository.redeem("MAXED", 789)
        assert redeemed_again is False
