import pytest
import httpx
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from src.bot.services.price_service import PriceService

@pytest.fixture
def mock_httpx_client():
    """Fixture to mock httpx.AsyncClient."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_client.__aenter__.return_value.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client) as mock_class:
        yield mock_client, mock_response, mock_class

@pytest.mark.asyncio
async def test_get_sol_price_in_usd_success(mock_httpx_client):
    """
    Tests that get_sol_price_in_usd returns the correct price on a successful API call.
    """
    mock_client, mock_response, _ = mock_httpx_client
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"solana": {"usd": 150.75}})
    mock_response.raise_for_status = MagicMock()

    # Clear cache before test
    PriceService.get_sol_price_in_usd.cache_clear()

    price = await PriceService.get_sol_price_in_usd()

    assert price == Decimal("150.75")
    mock_client.__aenter__.return_value.get.assert_called_once_with(f"{PriceService.COINGECKO_API_URL}?ids=solana&vs_currencies=usd")

@pytest.mark.asyncio
async def test_get_sol_price_in_usd_http_error(mock_httpx_client):
    """
    Tests that get_sol_price_in_usd returns None when the API returns an HTTP error.
    """
    mock_client, mock_response, _ = mock_httpx_client
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Server Error", request=AsyncMock(), response=mock_response)

    # Clear cache before test
    PriceService.get_sol_price_in_usd.cache_clear()

    price = await PriceService.get_sol_price_in_usd()

    assert price is None

@pytest.mark.asyncio
async def test_get_sol_price_in_usd_malformed_response(mock_httpx_client):
    """
    Tests that get_sol_price_in_usd returns None when the API response is malformed.
    """
    mock_client, mock_response, _ = mock_httpx_client
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"solana": {"eur": 140.0}}) # Missing 'usd' key
    mock_response.raise_for_status = MagicMock()

    # Clear cache before test
    PriceService.get_sol_price_in_usd.cache_clear()

    price = await PriceService.get_sol_price_in_usd()

    assert price is None

@pytest.mark.asyncio
async def test_get_sol_price_in_usd_caching(mock_httpx_client):
    """
    Tests that the result of get_sol_price_in_usd is cached.
    """
    mock_client, mock_response, _ = mock_httpx_client

    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"solana": {"usd": 200.0}})
    mock_response.raise_for_status = MagicMock()

    # Clear cache before test
    PriceService.get_sol_price_in_usd.cache_clear()

    # First call - should call the API
    price1 = await PriceService.get_sol_price_in_usd()
    assert price1 == Decimal("200.0")
    assert mock_client.__aenter__.return_value.get.call_count == 1

    # Second call - should be cached, so API should not be called again
    price2 = await PriceService.get_sol_price_in_usd()
    assert price2 == Decimal("200.0") # Should be the cached value
    assert mock_client.__aenter__.return_value.get.call_count == 1 # Still called only once
