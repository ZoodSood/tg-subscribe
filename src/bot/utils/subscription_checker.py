import typing
from datetime import datetime, timedelta

from decimal import Decimal
from ..data.config import (
    AMOUNT_DEVIATION_ENABLED,
    AMOUNT_DEVIATION_VALUE,
    NUMBER_DAYS_FROM_ONE_PAYMENT,
    SUBSCRIBE_AMOUNT_BY_PLANS,
)
from ..database.repositories import TransactionRepository, UserRepository
from ..keyboards import reply
from ..services.price_service import PriceService
from . import solana_service
import aiogram

async def task(bot: "aiogram.Bot"):
    transactions_records = await TransactionRepository.get_new()
    for transaction in transactions_records:
        if transaction.amount_sol:
            required_sol_amount = Decimal(transaction.amount_sol)
        else:
            usd_amount = SUBSCRIBE_AMOUNT_BY_PLANS.get(transaction.weeks)
            sol_price_usd = await PriceService.get_sol_price_in_usd()

            if not usd_amount or not sol_price_usd:
                continue

            required_sol_amount = Decimal(usd_amount) / Decimal(sol_price_usd)

        if await solana_service.check_transaction_for_correct_data(
            transaction.txid,
            required_sol_amount,
            AMOUNT_DEVIATION_ENABLED,
            Decimal(AMOUNT_DEVIATION_VALUE),
        ):
            await TransactionRepository.set_status(True, database_id=transaction.id)

            user = await UserRepository.get(telegram_id=transaction.owner_telegram_id)
            now = datetime.now()
            if user and user.days_sub_end:
                try:
                    current_end = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")
                    if current_end > now:
                        now = current_end
                except Exception:
                    pass

            new_end = now + timedelta(weeks=transaction.weeks)
            await UserRepository.update_subscription_date(
                new_end.strftime("%Y-%m-%d %H:%M:%S"),
                telegram_id=transaction.owner_telegram_id,
            )
            try:
                await bot.send_message(
                    chat_id=transaction.owner_telegram_id,
                    text="Your subscription has been activated!",
                    reply_markup=await reply.back_to_main_menu(),
                )
            except Exception as e:
                print(f"Failed to send activation message to {transaction.owner_telegram_id}: {e}")
        else:
            user = await UserRepository.get(telegram_id=transaction.owner_telegram_id)
            if user:
                try:
                    await bot.send_message(
                        chat_id=transaction.owner_telegram_id,
                        text="Transaction verification failed. Please check your transaction and try again.",
                    )
                except Exception as e:
                    print(f"Failed to send failure message to {transaction.owner_telegram_id}: {e}")
