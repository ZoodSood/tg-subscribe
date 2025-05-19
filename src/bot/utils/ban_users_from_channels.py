import typing
from datetime import datetime

from data.config import private_channels
from database import users

if typing.TYPE_CHECKING:
    import aiogram


async def task(bot: "aiogram.Bot"):
    users_records = await users.get_all()
    channels = [
        await bot.get_chat(private_channels[name]["id"])
        for name in private_channels.keys()
    ]
    for user in users_records:
        if datetime.now() < datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S"):
            continue

        for channel in channels:
            try:
                member = await bot.get_chat_member(channel.id, user.telegram_id)
            except Exception as e:
                # Handle case where user is not found or bot lacks permission
                continue
            if member.status in ["left", "creator"]:
                continue
            try:
                # Ban and immediately unban to remove user from channel (Telegram API compliant)
                await bot.ban_chat_member(channel.id, user.telegram_id)
                await bot.unban_chat_member(channel.id, user.telegram_id)
            except Exception as e:
                # Log or handle errors (e.g., insufficient rights, user already removed)
                continue
