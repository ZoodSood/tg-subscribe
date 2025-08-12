"""
payment_validator.py
Service for validating payment transactions.
"""
from decimal import Decimal, getcontext

from logzero import logger

from data.config import (
    AMOUNT_DEVIATION_ENABLED,
    AMOUNT_DEVIATION_VALUE,
    SUBSCRIBE_AMOUNT_BY_PLANS,
)
from database import transactions
from services.price_service import PriceService
from utils import solana_service, rate_limiter

# Set precision for Decimal calculations
getcontext().prec = 18

class PaymentValidator:
    @staticmethod
    async def validate_transaction(txid: str, user_id: int, weeks: int) -> tuple[bool, str]:
        """
        Validates a Solana transaction for a subscription payment.

        Returns a tuple (is_valid, message).
        """
        # 1. Rate limit check
        if not rate_limiter.is_allowed(user_id):
            wait_sec = rate_limiter.time_until_allowed(user_id)
            return False, f"You are doing this too frequently. Please wait {wait_sec} seconds."

        # 2. Validate signature format
        if not await solana_service.is_valid_transaction_signature(txid):
            return False, "Invalid transaction signature format. Please check and try again."

        # 3. Check if transaction has already been used
        transaction = await transactions.get(txid=txid)
        if transaction is not None:
            return False, "This transaction has already been used."

        # 4. Calculate required SOL amount based on current price
        usd_amount = SUBSCRIBE_AMOUNT_BY_PLANS.get(weeks)
        if not usd_amount:
            logger.error(f"Invalid subscription plan (weeks={weeks}) for user {user_id}.")
            return False, "Invalid subscription plan selected."

        sol_price_usd = await PriceService.get_sol_price_in_usd()
        if not sol_price_usd:
            logger.error("Could not fetch SOL price for validation.")
            return False, "Could not fetch the current SOL price. Please try again later."

        required_sol_amount = Decimal(usd_amount) / Decimal(sol_price_usd)
        logger.info(f"Required SOL for user {user_id}: {required_sol_amount:.8f} SOL (${usd_amount} @ ${sol_price_usd}/SOL)")

        # 5. Verify transaction on the blockchain
        is_correct = await solana_service.check_transaction_for_correct_data(
            signature=txid,
            subscription_amount=required_sol_amount,
            amount_deviation_enabled=AMOUNT_DEVIATION_ENABLED,
            amount_deviation_value=Decimal(AMOUNT_DEVIATION_VALUE),
        )

        if not is_correct:
            return False, "Transaction not found on the blockchain, or the amount/destination was incorrect."

        logger.info(f"Transaction {txid} successfully validated for user {user_id}.")
        return True, "Payment successfully validated."
