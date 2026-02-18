from decimal import Decimal, getcontext

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from logzero import logger

from ..data.config import SOLANA_WALLET_ADDRESS, SUBSCRIBE_AMOUNT_BY_PLANS
from ..database.repositories import TransactionRepository, UserRepository
from ..keyboards import reply as reply_keyboards
from ..services.payment_validator import PaymentValidator
from ..services.price_service import PriceService
from ..statesgroup import GetTxidFromUser

# Set precision for Decimal calculations
getcontext().prec = 18

payment_router = Router()

@payment_router.message(F.text == "Make subscription")
@payment_router.message(F.text == "Renew subscription")
async def make_subscription(message: types.Message):
    await message.answer(
        text="Choose a subscription plan:",
        reply_markup=await reply_keyboards.subscription_termins(
            SUBSCRIBE_AMOUNT_BY_PLANS.keys()
        ),
    )

@payment_router.message(F.text.contains("week"))
async def set_subscription_term(message: types.Message, state: FSMContext):
    """
    Handles the user's selection of a subscription term and provides payment instructions.
    """
    if not message.text:
        return

    try:
        term = int(message.text.split(" ")[0])
        if term not in SUBSCRIBE_AMOUNT_BY_PLANS:
            await message.answer(
                text="Invalid subscription duration. Please select from the available options.",
                reply_markup=await reply_keyboards.back_to_main_menu(),
            )
            return
    except (ValueError, IndexError):
        await message.answer(
            text="Invalid format. Please select a subscription plan from the buttons.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )
        return

    usd_amount = SUBSCRIBE_AMOUNT_BY_PLANS[term]
    sol_price_usd = await PriceService.get_sol_price_in_usd()

    if not sol_price_usd:
        await message.answer(
            text="Could not fetch the current SOL price. Please try again in a few moments.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )
        return

    required_sol_amount = Decimal(usd_amount) / Decimal(sol_price_usd)
    await state.set_data({"subscription_term": term, "required_sol_amount": str(required_sol_amount)})

    await message.answer(
        text=(
            f"To subscribe for {term} week(s) for ${usd_amount}, please send exactly "
            f"<b>{required_sol_amount:.8f} SOL</b> to the following wallet address:\n\n"
            f"<code>{SOLANA_WALLET_ADDRESS}</code>\n\n"
            "Only SOL transfers on the Solana network are accepted.\n"
            "After you have sent the transaction, click the 'Confirm Transfer' button below."
        ),
        reply_markup=await reply_keyboards.confirm_transfer(),
    )

@payment_router.message(F.text == "Confirm transfer")
async def confirm_transfer(message: types.Message, state: FSMContext):
    """
    Prompts the user to send the transaction signature for verification.
    """
    await state.set_state(GetTxidFromUser.state)
    await message.answer(
        text="Please send me the transaction signature (hash) to verify your payment.",
        reply_markup=types.ReplyKeyboardRemove(),
    )

@payment_router.message(GetTxidFromUser.state)
async def check_transaction(message: types.Message, state: FSMContext):
    """
    Receives the transaction signature, validates it using the PaymentValidator service,
    and processes the subscription if valid.
    """
    if not message.text or not message.from_user:
        return

    txid = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    weeks = data.get("subscription_term")
    expected_sol = data.get("required_sol_amount")

    if not weeks:
        await message.answer(
            "Your session has expired. Please select a subscription plan again.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )
        await state.clear()
        return

    await message.answer("Validating your transaction... This may take a moment.")

    is_valid, validation_message = await PaymentValidator.validate_transaction(
        txid=txid, user_id=user_id, weeks=weeks, expected_sol=Decimal(expected_sol) if expected_sol else None
    )

    if not is_valid:
        await state.set_state(GetTxidFromUser.payment_failed)
        await message.answer(
            text=f"Payment failed: {validation_message}",
            reply_markup=await reply_keyboards.retry_or_cancel(),
        )
        return

    # If validation is successful, create the transaction record and update subscription
    try:
        success = await TransactionRepository.create(txid, user_id, weeks, amount_sol=expected_sol)
        if not success:
            await message.answer(
                text="This transaction has already been processed or there was an error. If you believe this is a mistake, please contact support.",
                reply_markup=await reply_keyboards.back_to_main_menu(),
            )
            return

        from datetime import datetime, timedelta
        user = await UserRepository.get(telegram_id=user_id)
        now = datetime.now()

        if user and user.days_sub_end:
            try:
                current_end = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")
                if current_end > now:
                    now = current_end
            except (ValueError, TypeError):
                logger.warning(f"Could not parse existing subscription end date for user {user_id}.")

        new_end = now + timedelta(weeks=weeks)
        await UserRepository.update_subscription_date(new_end.strftime("%Y-%m-%d %H:%M:%S"), telegram_id=user_id)

        # Mark transaction as processed
        await TransactionRepository.set_status(True, txid=txid)

        await state.clear()
        await message.answer(
            text=f"✅ Payment successful! Your subscription is now active until {new_end.strftime('%Y-%m-%d')}.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )

    except Exception as e:
        logger.error(f"Error processing subscription for user {user_id} after validation: {e}")
        await message.answer(
            "There was a database error while activating your subscription. Please contact support.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )

@payment_router.message(GetTxidFromUser.payment_failed)
async def handle_payment_failed(message: types.Message, state: FSMContext):
    """
    Handles the user's response after a failed payment.
    """
    if message.text and "retry" in message.text.lower():
        await state.set_state(GetTxidFromUser.state)
        await message.answer(
            text="Please send your new transaction signature.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await state.clear()
        await message.answer(
            text="Payment process cancelled. You can start again from the main menu.",
            reply_markup=await reply_keyboards.back_to_main_menu(),
        )

# Note: The promo code functionality has been kept as-is.
# It could also be refactored into its own service in the future.
from ..database.repositories import PromoCodeRepository

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

    success = await PromoCodeRepository.redeem(code, message.from_user.id)
    if not success:
        await message.answer("Failed to redeem promo code. It may have expired or reached its usage limit.")
        return

    from datetime import timedelta
    user = await UserRepository.get(telegram_id=message.from_user.id)
    now = datetime.now()
    if user and user.days_sub_end:
        try:
            current_end = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")
            if current_end > now:
                now = current_end
        except Exception:
            pass

    new_end = now + timedelta(weeks=1)
    await UserRepository.update_subscription_date(new_end.strftime("%Y-%m-%d %H:%M:%S"), telegram_id=message.from_user.id)

    await state.clear()
    await message.answer(
        text=f"Promo code redeemed! You have been granted 1 week of free access. Subscription active until <code>{new_end.strftime('%Y-%m-%d %H:%M:%S')}</code>.",
        reply_markup=await reply_keyboards.back_to_main_menu(),
    )
