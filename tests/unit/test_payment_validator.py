import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from src.bot.services.payment_validator import PaymentValidator

@pytest.fixture
def mock_dependencies():
    with patch("src.bot.services.payment_validator.rate_limiter") as mock_rate_limiter, \
         patch("src.bot.services.payment_validator.solana_service") as mock_solana_service, \
         patch("src.bot.services.payment_validator.transactions") as mock_transactions, \
         patch("src.bot.services.payment_validator.PriceService") as mock_price_service:

        # Configure async mocks
        mock_solana_service.is_valid_transaction_signature = AsyncMock(return_value=True)
        mock_transactions.get = AsyncMock(return_value=None)
        mock_price_service.get_sol_price_in_usd = AsyncMock(return_value=Decimal("150.0"))
        mock_solana_service.check_transaction_for_correct_data = AsyncMock(return_value=True)

        yield {
            "rate_limiter": mock_rate_limiter,
            "solana_service": mock_solana_service,
            "transactions": mock_transactions,
            "price_service": mock_price_service,
        }

@pytest.mark.asyncio
async def test_validate_transaction_success(mock_dependencies):
    """Tests a successful transaction validation."""
    is_valid, message = await PaymentValidator.validate_transaction("txid", 123, 1)
    assert is_valid
    assert message == "Payment successfully validated."

@pytest.mark.asyncio
async def test_validate_transaction_rate_limited(mock_dependencies):
    """Tests that a user is rate limited."""
    mock_dependencies["rate_limiter"].is_allowed.return_value = False
    mock_dependencies["rate_limiter"].time_until_allowed.return_value = 30

    is_valid, message = await PaymentValidator.validate_transaction("txid", 123, 1)
    assert not is_valid
    assert "You are doing this too frequently" in message

@pytest.mark.asyncio
async def test_validate_transaction_invalid_signature(mock_dependencies):
    """Tests an invalid transaction signature."""
    mock_dependencies["solana_service"].is_valid_transaction_signature.return_value = False

    is_valid, message = await PaymentValidator.validate_transaction("txid", 123, 1)
    assert not is_valid
    assert message == "Invalid transaction signature format. Please check and try again."

@pytest.mark.asyncio
async def test_validate_transaction_already_used(mock_dependencies):
    """Tests a transaction that has already been used."""
    mock_dependencies["transactions"].get.return_value = "some_transaction_object"

    is_valid, message = await PaymentValidator.validate_transaction("txid", 123, 1)
    assert not is_valid
    assert message == "This transaction has already been used."

@pytest.mark.asyncio
async def test_validate_transaction_price_fetch_fails(mock_dependencies):
    """Tests when the price service fails to fetch the SOL price."""
    mock_dependencies["price_service"].get_sol_price_in_usd.return_value = None

    is_valid, message = await PaymentValidator.validate_transaction("txid", 123, 1)
    assert not is_valid
    assert message == "Could not fetch the current SOL price. Please try again later."

@pytest.mark.asyncio
async def test_validate_transaction_blockchain_check_fails(mock_dependencies):
    """Tests when the blockchain transaction check fails."""
    mock_dependencies["solana_service"].check_transaction_for_correct_data.return_value = False

    is_valid, message = await PaymentValidator.validate_transaction("txid", 123, 1)
    assert not is_valid
    assert message == "Transaction not found on the blockchain, or the amount/destination was incorrect."
