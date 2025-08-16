import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from src.bot.utils import solana_service
from solders.pubkey import Pubkey
from solders.signature import Signature

# A dummy signature that has the correct length (88 chars) and character set
VALID_SIGNATURE_DUMMY = "5joA4W3A22c4L9zrqN4aJc6qZ9ZqzJ6Y9Z4XwzY2j2G2j2K2L2m2N2P2R2S2V2W2Y2Z2a2b2c2d2e2f2g2h2i"
DUMMY_SIGNATURE_OBJ = Signature.new_unique()

@pytest.mark.asyncio
async def test_is_valid_transaction_signature_valid():
    """Tests that a valid signature string returns True."""
    with patch("solders.signature.Signature.from_string"):
        assert await solana_service.is_valid_transaction_signature(VALID_SIGNATURE_DUMMY)

@pytest.mark.asyncio
async def test_is_valid_transaction_signature_invalid():
    """Tests that an invalid signature string returns False."""
    invalid_sig = "this_is_not_a_valid_signature"
    assert not await solana_service.is_valid_transaction_signature(invalid_sig)

@pytest.mark.asyncio
@patch("solders.signature.Signature.from_string", return_value=DUMMY_SIGNATURE_OBJ)
@patch("solana.rpc.async_api.AsyncClient.get_transaction", new_callable=AsyncMock)
async def test_check_transaction_for_correct_data_success(mock_get_transaction, mock_from_string):
    """Tests a successful transaction validation."""
    mock_tx_response = MagicMock()
    mock_tx_response.value = MagicMock()
    mock_tx_response.value.meta.err = None
    mock_tx_response.value.transaction.message.instructions = [
        MagicMock(
            program="system",
            parsed={
                "type": "transfer",
                "info": {
                    "destination": solana_service.SOLANA_WALLET_ADDRESS,
                    "lamports": int(Decimal("0.5") * Decimal("1e9")),
                },
            },
        )
    ]
    mock_get_transaction.return_value = mock_tx_response

    result = await solana_service.check_transaction_for_correct_data(
        signature=VALID_SIGNATURE_DUMMY,
        subscription_amount=Decimal("0.5"),
        amount_deviation_enabled=False,
        amount_deviation_value=Decimal("0.01"),
    )
    assert result

@pytest.mark.asyncio
@patch("solders.signature.Signature.from_string", return_value=DUMMY_SIGNATURE_OBJ)
@patch("solana.rpc.async_api.AsyncClient.get_transaction", new_callable=AsyncMock)
async def test_check_transaction_for_correct_data_failed_tx(mock_get_transaction, mock_from_string):
    """Tests a transaction that failed on-chain."""
    mock_tx_response = MagicMock()
    mock_tx_response.value = MagicMock()
    mock_tx_response.value.meta.err = "Some error"
    mock_get_transaction.return_value = mock_tx_response

    result = await solana_service.check_transaction_for_correct_data(
        signature=VALID_SIGNATURE_DUMMY,
        subscription_amount=Decimal("0.5"),
        amount_deviation_enabled=False,
        amount_deviation_value=Decimal("0.01"),
    )
    assert not result

@pytest.mark.asyncio
async def test_is_valid_transaction_signature_decode_error():
    """Tests that a signature that fails to decode returns False."""
    with patch("solders.signature.Signature.from_string", side_effect=Exception("Decode error")):
        assert not await solana_service.is_valid_transaction_signature(VALID_SIGNATURE_DUMMY)

@pytest.mark.asyncio
@patch("solders.signature.Signature.from_string", return_value=DUMMY_SIGNATURE_OBJ)
@patch("solana.rpc.async_api.AsyncClient.get_transaction", new_callable=AsyncMock)
async def test_check_transaction_not_found(mock_get_transaction, mock_from_string):
    """Tests a transaction that is not found on-chain."""
    mock_get_transaction.return_value = None
    result = await solana_service.check_transaction_for_correct_data(
        signature=VALID_SIGNATURE_DUMMY,
        subscription_amount=Decimal("0.5"),
        amount_deviation_enabled=False,
        amount_deviation_value=Decimal("0.01"),
    )
    assert not result

@pytest.mark.asyncio
@patch("solders.signature.Signature.from_string", return_value=DUMMY_SIGNATURE_OBJ)
@patch("solana.rpc.async_api.AsyncClient.get_transaction", new_callable=AsyncMock)
async def test_check_transaction_with_deviation_success(mock_get_transaction, mock_from_string):
    """Tests a successful transaction validation with amount deviation."""
    mock_tx_response = MagicMock()
    mock_tx_response.value = MagicMock()
    mock_tx_response.value.meta.err = None
    mock_tx_response.value.transaction.message.instructions = [
        MagicMock(
            program="system",
            parsed={"type": "transfer", "info": {"destination": solana_service.SOLANA_WALLET_ADDRESS, "lamports": int(Decimal("0.505") * Decimal("1e9"))}},
        )
    ]
    mock_get_transaction.return_value = mock_tx_response

    result = await solana_service.check_transaction_for_correct_data(
        signature=VALID_SIGNATURE_DUMMY,
        subscription_amount=Decimal("0.5"),
        amount_deviation_enabled=True,
        amount_deviation_value=Decimal("0.01"),
    )
    assert result

@pytest.mark.asyncio
@patch("solders.signature.Signature.from_string", return_value=DUMMY_SIGNATURE_OBJ)
@patch("solana.rpc.async_api.AsyncClient.get_transaction", new_callable=AsyncMock)
async def test_check_transaction_no_valid_instruction(mock_get_transaction, mock_from_string):
    """Tests a transaction with no valid transfer instruction to our wallet."""
    mock_tx_response = MagicMock()
    mock_tx_response.value = MagicMock()
    mock_tx_response.value.meta.err = None
    mock_tx_response.value.transaction.message.instructions = [
        MagicMock(program="other_program", parsed={})
    ]
    mock_get_transaction.return_value = mock_tx_response

    result = await solana_service.check_transaction_for_correct_data(
        signature=VALID_SIGNATURE_DUMMY,
        subscription_amount=Decimal("0.5"),
        amount_deviation_enabled=False,
        amount_deviation_value=Decimal("0.01"),
    )
    assert not result
