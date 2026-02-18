import pytest
from unittest.mock import patch, AsyncMock
from utils.solana_service import is_valid_transaction_signature, check_transaction_for_correct_data

@pytest.mark.asyncio
async def test_is_valid_transaction_signature():
    # A valid Solana signature is base58 and 87-88 characters long
    valid_sig = "5V9Y1v2J8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z"
    # Ensure it's 88 chars for the test
    valid_sig = valid_sig + "A" * (88 - len(valid_sig))
    assert await is_valid_transaction_signature(valid_sig) == True
    assert await is_valid_transaction_signature("invalid") == False

@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
async def test_check_transaction_success(mock_get):
    from data.config import SOLANA_WALLET_ADDRESS
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "parsedInstruction": [
            {
                "type": "transfer",
                "destination": SOLANA_WALLET_ADDRESS,
                "lamports": 200 * 1e9
            }
        ]
    }
    mock_get.return_value.__aenter__.return_value = mock_response

    result = await check_transaction_for_correct_data("5V9Y1v2J8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7zA", 200)
    assert result == True

@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
async def test_check_transaction_failure_wrong_amount(mock_get):
    from data.config import SOLANA_WALLET_ADDRESS
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "parsedInstruction": [
            {
                "type": "transfer",
                "destination": SOLANA_WALLET_ADDRESS,
                "lamports": 100 * 1e9
            }
        ]
    }
    mock_get.return_value.__aenter__.return_value = mock_response

    result = await check_transaction_for_correct_data("5V9Y1v2J8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7zA", 200)
    assert result == False

@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
async def test_check_transaction_deviation_success(mock_get):
    from data.config import SOLANA_WALLET_ADDRESS
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "parsedInstruction": [
            {
                "type": "transfer",
                "destination": SOLANA_WALLET_ADDRESS,
                "lamports": 199.995 * 1e9
            }
        ]
    }
    mock_get.return_value.__aenter__.return_value = mock_response

    # Amount is 200, actual is 199.995, deviation is 0.01. Should be valid.
    result = await check_transaction_for_correct_data(
        "5V9Y1v2J8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7zA",
        200,
        deviation_enabled=True,
        deviation_value=0.01
    )
    assert result == True
