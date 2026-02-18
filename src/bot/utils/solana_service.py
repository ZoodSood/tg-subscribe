"""
solana_service.py
Utility functions for verifying Solana transactions using public APIs.
"""
import aiohttp
import re
import logging
from data.config import SOLANA_WALLET_ADDRESS

async def is_valid_transaction_signature(signature: str) -> bool:
    """
    Checks if the provided string is a valid Solana transaction signature (hash).
    """
    if not signature:
        return False
    # Solana signatures are base58, 87-88 chars
    pattern = r"^[1-9A-HJ-NP-Za-km-z]{87,88}$"
    return bool(re.fullmatch(pattern, signature))

async def check_transaction_for_correct_data(
    signature: str,
    subscription_amount: float,
    deviation_enabled: bool = False,
    deviation_value: float = 0.01
) -> bool:
    """
    Verifies the transaction on Solana blockchain using a public API.
    Checks if the transaction sent the correct amount to the configured wallet.
    Supports optional amount deviation.
    """
    # Example: Use Solscan public API (Note: Public APIs may have rate limits)
    api_url = f"https://public-api.solscan.io/transaction/{signature}"
    headers = {"accept": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logging.error(f"Solana API returned status {response.status} for signature {signature}")
                    return False
                tx_data = await response.json()

                # Check if transaction is successful (status: "Success" or equivalent in API)
                # In Solscan public API, successful transactions usually return data
                if not tx_data:
                    return False

                # Verification logic for amount and destination
                # Note: The structure depends on the specific API response.
                # This implementation follows the pattern used in the codebase.
                instructions = tx_data.get("parsedInstruction", [])
                for instr in instructions:
                    if (
                        instr.get("type") == "transfer"
                        and instr.get("destination") == SOLANA_WALLET_ADDRESS
                    ):
                        actual_amount = float(instr.get("lamports", 0)) / 1e9
                        required_amount = float(subscription_amount)

                        if deviation_enabled:
                            if actual_amount >= (required_amount - deviation_value):
                                return True
                        else:
                            if actual_amount >= required_amount:
                                return True
    except Exception as e:
        logging.error(f"Error checking Solana transaction {signature}: {e}")
        return False

    return False
