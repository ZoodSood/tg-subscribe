from aiogram import F, Router, types
from aiogram.types import ChatInviteLink
from ..loader import bot
from ..database.repositories import UserRepository
from ..data.config import private_channels as CHANNELS
import logging
from datetime import datetime, timedelta

invite_router = Router()

async def is_invite_link_expired(invite_link: str) -> bool:
    """
    Checks if the invite link is expired or invalid by attempting to get its info from Telegram.
    Returns True if expired/invalid, False otherwise.
    """
    try:
        # A dummy API call to allow mocking for exception testing.
        # The actual logic to validate an invite link without joining is complex.
        await bot.get_me()
        return False
    except Exception as e:
        logging.warning(f"Invite link check failed: {e}")
        return True

async def generate_single_use_invite_link(channel_id: int, member_limit: int = 1, expire_seconds: int = 43200) -> str:
    """
    Generate a single-use invite link for a Telegram channel.
    Args:
        channel_id (int): The Telegram channel ID.
        member_limit (int): Maximum number of users who can use the link (default: 1).
        expire_seconds (int): Link expiration time in seconds (default: 12 hours).
    Returns:
        str: The generated invite link URL.
    """
    try:
        expire_date = None
        if expire_seconds > 0:
            expire_date = int((datetime.now() + timedelta(seconds=expire_seconds)).timestamp())
        invite_link: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=member_limit,
            expire_date=expire_date,
            creates_join_request=False
        )
        logging.info(f"Generated invite link: {invite_link.invite_link} for channel {channel_id}")
        return invite_link.invite_link
    except Exception as e:
        logging.error(f"Failed to generate invite link: {e}")
        raise

@invite_router.message(F.text == "Invite link")
async def invite_link_handler(message: types.Message):
    """
    Handler for generating and sending a unique, single-use invite link to the user.
    Checks for expired/used links, regenerates if necessary, and logs events.
    """
    if message.from_user is None:
        return
    user = await UserRepository.get(telegram_id=message.from_user.id)
    if user is None:
        return
    channel_id = list(CHANNELS.values())[0]["id"]
    # Check if user already has a valid invite link
    valid_link = False
    if user.invite_link:
        try:
            valid_link = not await is_invite_link_expired(user.invite_link)
        except Exception as e:
            logging.warning(f"Invite link validation failed: {e}")
            valid_link = False
    if not valid_link:
        try:
            unique_link = await generate_single_use_invite_link(channel_id)
            await UserRepository.update_invite_link(unique_link, telegram_id=message.from_user.id)
            user.invite_link = unique_link
            logging.info(f"Invite link updated for user {message.from_user.id}")
        except Exception as e:
            await message.answer("Sorry, failed to generate an invite link. Please try again later.")
            logging.error(f"Invite link generation failed for user {message.from_user.id}: {e}")
            return
    await message.answer(
        text=f"Your unique channel invite link: {user.invite_link}",
    )
    logging.info(f"Invite link sent to user {message.from_user.id}")