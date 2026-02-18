from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from data.config import SUBSCRIBE_AMOUNT_BY_PLANS, SOLANA_WALLET_ADDRESS
from database import transactions
from keyboards import reply as reply_keyboards
from services.payment_service import PaymentService
from statesgroup import GetTxidFromUser
from utils import solana_service, rate_limiter
from database.repositories import PromoCodeRepository
from aiogram.filters import CommandObject

payment_router = Router()

VALID_SUBSCRIPTION_TERMS = list(SUBSCRIBE_AMOUNT_BY_PLANS.keys())

# --- Per-user wallet feature (currently disabled) ---
# from utils import per_user_wallet_service
# PER_USER_WALLET_ENABLED = False  # Set to True to enable per-user wallet generation

@payment_router.message(F.text == "Make subscription")
@payment_router.message(F.text == "Renew subscription")
async def make_subscription(message: types.Message):
    await message.answer(
        text=f"Choose subscription plan",
        reply_markup=await reply_keyboards.subscription_termins(
            SUBSCRIBE_AMOUNT_BY_PLANS.keys()
        ),
    )


@payment_router.message(F.text.contains("week"))
async def set_subscribtion_termin(message: types.Message, state: FSMContext):
    """
    Handles the user's selection of a subscription term, checks allowed payment window, and provides payment instructions.
    """
    if message.text is None:
        return
    # Validate subscription term input
    try:
        termin = int(message.text.split(" ")[0])
        if termin not in VALID_SUBSCRIPTION_TERMS:
            await message.answer(
                text="Invalid subscription duration. Please select from available options.",
                reply_markup=await reply_keyboards.back_to_main_menu(),
            )
            return
    except ValueError:
        await message.answer(
            text="Invalid subscription format. Please select from available options.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )
        return

    amount_required = PaymentService.get_amount_for_plan(termin)
    # Check if current time is Friday 12:00-14:00 UTC
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    if not (now_utc.weekday() == 4 and now_utc.hour >= 12 and now_utc.hour < 14):
        await message.answer(
            text="Payments are only accepted on Fridays between 12:00 and 14:00 UTC. Please try again during the allowed window.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )
        return
    await state.set_data({"subscription_termin": termin})
    # --- Per-user wallet logic (disabled) ---
    # if PER_USER_WALLET_ENABLED:
    #     user_wallet = await per_user_wallet_service.get_or_create_wallet(message.from_user.id)
    #     wallet_address = user_wallet.address
    # else:
    wallet_address = SOLANA_WALLET_ADDRESS
    await message.answer(
        text=f"To pay, use this <b>Solana</b> wallet: <code>{SOLANA_WALLET_ADDRESS}</code>.\n"
        f"Transfer ${amount_required} in <b>SOL</b> to this address. Only SOL is accepted.\n"
        "You have <b>10 minutes</b> to complete the payment. After submitting, click the Confirm button.",
        reply_markup=await reply_keyboards.confirm_transfer(),
    )


@payment_router.message(F.text == "Confirm transfer")
async def confirm_transfer(message: types.Message, state: FSMContext):
    """
    Prompts the user to send the transaction signature for verification.
    """
    await state.set_state(GetTxidFromUser.state)
    await message.answer(
        text="Great, send me the transaction signature (hash) to verify the transfer.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@payment_router.message(GetTxidFromUser.payment_failed)
async def handle_payment_failed(message: types.Message, state: FSMContext):
    """
    Handles failed payment scenarios, provides user feedback and options to retry or cancel.
    """
    await message.answer(
        text="Payment verification failed. Would you like to try again or cancel?",
        reply_markup=await reply_keyboards.retry_or_cancel(),
    )
    await state.set_state(GetTxidFromUser.retry)

@payment_router.message(GetTxidFromUser.retry)
async def handle_payment_retry(message: types.Message, state: FSMContext):
    """
    Handles payment retry logic, allowing the user to resubmit a transaction signature or cancel.
    """
    if message.text and "retry" in message.text.lower():
        await state.set_state(GetTxidFromUser.state)
        await message.answer(
            text="Please send your transaction signature again.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await state.clear()
        await message.answer(
            text="Payment process cancelled. You can start again from the main menu.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )

@payment_router.message(GetTxidFromUser.timeout)
async def handle_payment_timeout(message: types.Message, state: FSMContext):
    """
    Handles payment timeout scenarios, notifies the user and clears the state.
    """
    await state.clear()
    await message.answer(
        text="Your payment session has timed out. Please start again if you wish to subscribe.",
        reply_markup=await reply_keyboards.back_to_main_menu(),
    )

@payment_router.message(GetTxidFromUser.state)
async def check_transaction(message: types.Message, state: FSMContext):
    """
    Checks the transaction signature and validates the payment for the subscription.
    Notifies the user if the invoice is expired (older than 10 minutes).
    Enhanced: Handles failed payment, retry, and timeout logic.
    """
    try:
        data = await state.get_data()
        if not data.get('subscription_termin'):
            await message.answer("Session expired. Please restart payment process.")
            await state.clear()
            return
        if message.text is None or message.from_user is None:
            return
        user_id = message.from_user.id
        txid = message.text.strip()
        # Prevent abuse of transaction checks
        if not rate_limiter.is_allowed(user_id):
            wait_sec = rate_limiter.time_until_allowed(user_id)
            await message.answer(
                text=f"You are doing this too frequently. Please wait {wait_sec} seconds before trying again."
            )
            return
        # Check if txid was already used
        transaction = await transactions.get(txid=txid)
        if transaction is not None:
            await state.set_state(GetTxidFromUser.payment_failed)
            await message.answer(
                text="This transaction has already been used. Please send a new transaction signature or retry.",
                reply_markup=await reply_keyboards.retry_or_cancel(),
            )
            return
        # Check for unpaid invoice older than 10 minutes
        from datetime import datetime, timezone, timedelta
        now_ts = int(datetime.now(timezone.utc).timestamp())
        recent_unpaid = await transactions.get_new()
        for t in recent_unpaid:
            if t.owner_telegram_id == user_id and not t.status:
                if now_ts - t.created_at_timestamp > 600:
                    await transactions.set_status(False, database_id=t.id)
                    await state.set_state(GetTxidFromUser.timeout)
                    await message.answer(
                        text="Your previous invoice was not paid in time and has been cancelled.",
                        reply_markup=await reply_keyboards.retry_or_cancel(),
                    )
                    return
                else:
                    await message.answer(
                        text="You have an unpaid invoice. Please pay or wait for it to expire before submitting a new transaction.",
                        reply_markup=await reply_keyboards.back_to_main_menu(),
                    )
                    return
        # Validate Solana transaction signature and check payment details
        weeks = data.get("subscription_termin", 1)
        amount_required = PaymentService.get_amount_for_plan(weeks)
        # --- Per-user wallet logic (disabled) ---
        # if PER_USER_WALLET_ENABLED:
        #     user_wallet = await per_user_wallet_service.get_or_create_wallet(user_id)
        #     wallet_address = user_wallet.address
        # else:
        wallet_address = SOLANA_WALLET_ADDRESS
        # Validate wallet address format (already checked at config load, but double-check for runtime safety)
        import re
        if not re.fullmatch(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", wallet_address):
            await message.answer(
                text="Invalid wallet address configuration. Please contact support."
            )
            return
        if not await solana_service.is_valid_transaction_signature(txid):
            await state.set_state(GetTxidFromUser.payment_failed)
            await message.answer(
                text="Invalid transaction signature format. Please check and try again.",
                reply_markup=await reply_keyboards.retry_or_cancel(),
            )
            return
        # Check transaction details on Solana
        from data.config import AMOUNT_DEVIATION_ENABLED, AMOUNT_DEVIATION_VALUE
        try:
            is_valid = await solana_service.check_transaction_for_correct_data(
                txid, amount_required, AMOUNT_DEVIATION_ENABLED, AMOUNT_DEVIATION_VALUE
            )
        except Exception as e:
            await state.set_state(GetTxidFromUser.payment_failed)
            await message.answer(
                text="Blockchain API error. Please try again later or retry.",
                reply_markup=await reply_keyboards.retry_or_cancel(),
            )
            return
        if not is_valid:
            await state.set_state(GetTxidFromUser.payment_failed)
            await message.answer(
                text="Transaction not found, wrong amount, or wrong destination wallet. Please check and try again.",
                reply_markup=await reply_keyboards.retry_or_cancel(),
            )
            return
        try:
            await transactions.create(
                txid,
                user_id,
                weeks,
            )
        except Exception as e:
            await state.set_state(GetTxidFromUser.payment_failed)
            await message.answer(
                text="Database error while recording your payment. Please retry or contact support.",
                reply_markup=await reply_keyboards.retry_or_cancel(),
            )
            return
        from database import users
        from datetime import datetime, timedelta
        try:
            user = await users.get(telegram_id=user_id)
            if user:
                now = datetime.now()
                if user.days_sub_end:
                    try:
                        current_end = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")
                        if current_end > now:
                            now = current_end
                    except ValueError as ve:
                        await state.set_state(GetTxidFromUser.payment_failed)
                        await message.answer(
                            text="Error processing your subscription date. Contact support.",
                            reply_markup=await reply_keyboards.retry_or_cancel(),
                        )
                        return
                    except Exception as e:
                        await state.set_state(GetTxidFromUser.payment_failed)
                        await message.answer(
                            text="System error processing subscription. Contact support.",
                            reply_markup=await reply_keyboards.retry_or_cancel(),
                        )
                        return
                new_end = now + timedelta(weeks=weeks)
                await users.update_subscription_date(new_end.strftime("%Y-%m-%d %H:%M:%S"), telegram_id=user_id)
        except Exception as e:
            await state.set_state(GetTxidFromUser.payment_failed)
            await message.answer(
                text="Database error updating subscription. Please retry or contact support.",
                reply_markup=await reply_keyboards.retry_or_cancel(),
            )
            return
        await state.clear()
        await message.answer(
            text="Great, wait for the end of the transaction, and I will notify you when the subscription is charged.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )
    except Exception as e:
        await state.set_state(GetTxidFromUser.payment_failed)
        await message.answer(
            text="An unexpected error occurred. Please retry or contact support.",
            reply_markup=await reply_keyboards.retry_or_cancel(),
        )


# def validate_transaction(tx_data: dict) -> bool:
#     """Verify transaction meets all security requirements"""
#     # Placeholder implementations for missing helper functions
#     def _validate_tx_uniqueness(signature):
#         # Implement uniqueness check or import from utils
#         return True
#     def _validate_tx_timestamp(timestamp):
#         # Implement timestamp validation logic
#         return True
#     def _validate_amount(amount):
#         # Implement amount validation logic
#         return True
#     def _validate_destination(receiver):
#         # Implement destination validation logic
#         return True
#     return all([
#         _validate_tx_uniqueness(tx_data['signature']),
#         _validate_tx_timestamp(tx_data['timestamp']),
#         _validate_amount(tx_data['amount']),
#         _validate_destination(tx_data['receiver'])
#     ])


# Basic security logging
async def log_security_event(event_type: str, user_id: int, details: dict):
    """Log security-related events for monitoring"""
    from datetime import datetime
    import json
    await db.execute(
        "INSERT INTO security_logs VALUES (?, ?, ?, ?)",
        (datetime.now(), event_type, user_id, json.dumps(details))
    )

    
@payment_router.message(F.text == "Redeem promo code")
async def prompt_promo_code(message: types.Message, state: FSMContext):
    """
    Prompts the user to enter a promo code for free access.
    """
    await state.set_state("awaiting_promo_code")
    await message.answer("Please enter your promo code:")

@payment_router.message(lambda m, state: state.get_state() == "awaiting_promo_code")
async def redeem_promo_code(message: types.Message, state: FSMContext):
    """
    Handles promo code redemption, validates code, updates usage, and grants free access if valid.
    """
    if message.text is None or message.from_user is None:
        await message.answer("Invalid input. Please enter a promo code.")
        return
    code = message.text.strip()
    promo = await PromoCodeRepository.get_by_code(code)
    if not promo:
        await message.answer("Promo code not found or invalid. Please try again.")
        return
    if not promo.is_active:
        await message.answer("This promo code is no longer active.")
        return
    from datetime import datetime
    if promo.expires_at:
        try:
            expires = datetime.fromisoformat(promo.expires_at)
            if datetime.utcnow() > expires:
                await message.answer("This promo code has expired.")
                return
        except Exception:
            pass
    if promo.max_uses and promo.used_count >= promo.max_uses:
        await message.answer("This promo code has reached its maximum number of uses.")
        return
    # Check if user has already redeemed a promo code (optional, for one-time per user)
    # Optionally, implement logic here if needed
    success = await PromoCodeRepository.redeem(code, message.from_user.id)
    if not success:
        await message.answer("Failed to redeem promo code. It may have expired or reached its usage limit.")
        return
    # Grant free subscription (e.g., 1 week)
    from database import users
    from datetime import timedelta
    user = await users.get(telegram_id=message.from_user.id)
    now = datetime.now()
    if user and user.days_sub_end:
        try:
            current_end = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")
            if current_end > now:
                now = current_end
        except Exception:
            pass
    new_end = now + timedelta(weeks=1)
    await users.update_subscription_date(new_end.strftime("%Y-%m-%d %H:%M:%S"), telegram_id=message.from_user.id)
    await state.clear()
    await message.answer(
        text=f"Promo code redeemed! You have been granted 1 week of free access. Subscription active until <code>{new_end.strftime('%Y-%m-%d %H:%M:%S')}</code>.",
        reply_markup=await reply_keyboards.back_to_main_menu(),
    )
