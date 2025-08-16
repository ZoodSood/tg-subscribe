import typing
from datetime import datetime

from ..data.config import SUBSCRIBE_END_NOTIFICATION_DAYS
from ..database.repositories import UserRepository

if typing.TYPE_CHECKING:
    import aiogram


async def task(bot: "aiogram.Bot"):
    users_records = await UserRepository.get_all()
    for user in users_records:
        datetime_now = datetime.now()
        sub_end_date = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")

        days_left = (sub_end_date - datetime_now).days + 1
        print(days_left)
        # Function to notify users about their subscription ending soon. Handles notification days and message formatting.
        # Note: datetime.now() is naive and assumes server timezone; consider using timezone-aware datetimes for production reliability.
        if days_left in SUBSCRIBE_END_NOTIFICATION_DAYS:
            if days_left == 1:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text="Your subscription will end soon!\n"
                        f"<code>{days_left}</code> day left until the end.",
                    )
                except Exception as e:
                    print(f"Failed to send message to {user.telegram_id}: {e}")
            else:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text="Your subscription will end soon!\n"
                        f"<code>{days_left}</code> days left until the end.",
                    )
                except Exception as e:
                    print(f"Failed to send message to {user.telegram_id}: {e}")
