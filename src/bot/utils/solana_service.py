"""
solana_service.py
Utility functions for verifying Solana transactions using the solana-py library.
"""
import re
from decimal import Decimal, getcontext

from logzero import logger
from solders.pubkey import PublicKey
from solana.rpc.async_api import AsyncClient
from solders.signature import Signature
from solders.transaction_status import EncodedTransactionWithStatusMeta, UiTransactionEncoding

from data.config import SOLANA_RPC_URL, SOLANA_WALLET_ADDRESS

# Set precision for Decimal calculations
getcontext().prec = 18

async def is_valid_transaction_signature(signature: str) -> bool:
    """
    Checks if the provided string is a valid Solana transaction signature format.
    """
    # A simple regex check for base58 characters and length can be a first pass.
    # Solana signatures are 64 bytes, which results in a base58 string of up to 88 chars.
    pattern = r"^[1-9A-HJ-NP-Za-km-z]{80,90}$" # A bit lenient on length
    if not re.fullmatch(pattern, signature):
        return False
    try:
        # The most reliable check is to try to decode it.
        Signature.from_string(signature)
        return True
    except Exception:
        logger.warning(f"Invalid signature format: {signature}")
        return False

async def check_transaction_for_correct_data(
    signature: str,
    subscription_amount: Decimal,
    amount_deviation_enabled: bool,
    amount_deviation_value: Decimal,
) -> bool:
    """
    Verifies the transaction on the Solana blockchain using an RPC client.
    Checks if the transaction sent the correct amount to the configured wallet.
    """
    try:
        async with AsyncClient(SOLANA_RPC_URL) as client:
            tx_response = await client.get_transaction(
                Signature.from_string(signature),
                encoding=UiTransactionEncoding.JSONParsed,
                max_supported_transaction_version=0,
            )

            if not tx_response or not tx_response.value:
                logger.warning(f"Transaction not found for signature: {signature}")
                return False

            tx_data: EncodedTransactionWithStatusMeta = tx_response.value

            if tx_data.meta and tx_data.meta.err:
                logger.warning(f"Transaction {signature} failed with error: {tx_data.meta.err}")
                return False

            # Find the transfer to our wallet in the transaction instructions
            for instruction in tx_data.transaction.message.instructions:
                if (
                    isinstance(instruction.parsed, dict)
                    and instruction.program == "system"
                    and instruction.parsed.get("type") == "transfer"
                ):
                    parsed_info = instruction.parsed.get("info", {})
                    if parsed_info.get("destination") == SOLANA_WALLET_ADDRESS:
                        transferred_lamports = Decimal(parsed_info.get("lamports", 0))
                        transferred_sol = transferred_lamports / Decimal(1e9)

                        # Check if the amount is correct
                        if amount_deviation_enabled:
                            lower_bound = subscription_amount - amount_deviation_value
                            upper_bound = subscription_amount + amount_deviation_value
                            if lower_bound <= transferred_sol <= upper_bound:
                                logger.info(f"Transaction {signature} is valid. Amount: {transferred_sol} SOL.")
                                return True
                        else:
                            # For exact match, use a very small tolerance for precision issues
                            if abs(transferred_sol - subscription_amount) < Decimal('0.00001'):
                                logger.info(f"Transaction {signature} is valid. Amount: {transferred_sol} SOL.")
                                return True

            logger.warning(f"Transaction {signature} did not contain a valid transfer to {SOLANA_WALLET_ADDRESS} for the required amount.")
            return False

    except Exception as e:
        logger.error(f"An error occurred while checking transaction {signature}: {e}")
        return False
