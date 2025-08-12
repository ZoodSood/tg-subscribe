from decimal import Decimal, getcontext
import httpx
from async_lru import alru_cache
from logzero import logger

# Set precision for Decimal calculations
getcontext().prec = 18

class PriceService:
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

    @staticmethod
    @alru_cache(maxsize=1, ttl=300)
    async def get_sol_price_in_usd() -> Decimal | None:
        """
        Fetches the current price of Solana in USD from the CoinGecko API.
        Caches the result for 5 minutes.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PriceService.COINGECKO_API_URL}?ids=solana&vs_currencies=usd"
                )
                response.raise_for_status()
                data = response.json()
                price = data.get("solana", {}).get("usd")
                if price:
                    logger.info(f"Fetched SOL price: ${price}")
                    return Decimal(str(price)) # Use str to avoid precision issues with float
                else:
                    logger.error("Could not find 'solana' or 'usd' key in CoinGecko API response.")
                    return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching SOL price from CoinGecko: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching SOL price: {e}")
            return None
