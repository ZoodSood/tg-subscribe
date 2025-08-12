import typing
from datetime import datetime, timedelta

from ..data.config import (
    NUMBER_DAYS_FROM_ONE_PAYMENT,
    SUBSCRIBE_AMOUNT_BY_PLANS,
)
from ..database import transactions, users
from ..keyboards import reply
from . import solana_service
import aiogram

async def task(bot: "aiogram.Bot"):
    transactions_records = await transactions.get_new()
    for transaction in transactions_records:
        if await solana_service.check_transaction_for_correct_data(
            transaction.txid, SUBSCRIBE_AMOUNT_BY_PLANS[transaction.months]
        ):
            await transactions.set_status(True, database_id=transaction.id)
            await users.update_subscription_date(
                (datetime.now() + timedelta(days=NUMBER_DAYS_FROM_ONE_PAYMENT * transaction.months)).strftime("%Y-%m-%d"),
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
            user = await users.get(telegram_id=transaction.owner_telegram_id)
            if user:
                try:
                    await bot.send_message(
                        chat_id=transaction.owner_telegram_id,
                        text="Transaction verification failed. Please check your transaction and try again.",
                    )
                except Exception as e:
                    print(f"Failed to send failure message to {transaction.owner_telegram_id}: {e}")
