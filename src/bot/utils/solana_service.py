"""
solana_service.py
Utility functions for verifying Solana transactions using public APIs.
"""
import aiohttp
import re
from data.config import SOLANA_WALLET_ADDRESS

async def is_valid_transaction_signature(signature: str) -> bool:
    """
    Checks if the provided string is a valid Solana transaction signature (hash).
    """
    # Solana signatures are base58, 87-88 chars
    pattern = r"^[1-9A-HJ-NP-Za-km-z]{87,88}$"
    return bool(re.fullmatch(pattern, signature))

async def check_transaction_for_correct_data(signature: str, subscription_amount: int) -> bool:
    """
    Verifies the transaction on Solana blockchain using a public API.
    Checks if the transaction sent the correct amount to the configured wallet.
    """
    # Example: Use SolanaFM or Solscan public API
    api_url = f"https://public-api.solscan.io/transaction/{signature}"
    headers = {"accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                return False
            tx_data = await response.json()
            # Check if transaction is successful and sent to the correct wallet
            try:
                instructions = tx_data.get("parsedInstruction", [])
                for instr in instructions:
                    if (
                        instr.get("type") == "transfer"
                        and instr.get("destination") == SOLANA_WALLET_ADDRESS
                        and float(instr.get("lamports", 0)) / 1e9 >= subscription_amount
                    ):
                        return True
            except Exception:
                return False
    return False