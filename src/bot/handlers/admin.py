from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..data.config import MAILING_TEXT, BOT_OWNER_ID
from ..database import users
from ..filters import IsAdminFilter
from ..loader import bot
from ..keyboards.inline import admin_dashboard_keyboard
from ..database.repositories import PromoCodeRepository
from aiogram.filters import CommandObject

admin_router = Router()


@admin_router.message(IsAdminFilter(), Command("start_mailing"))
async def start_mailing_to_not_subscribed_users(message: types.Message):
    """Start mailing to not subscribed users"""

    if message.from_user is None:
        return
    users_records = await users.get_all()
    for user in users_records:
        if user.telegram_id == message.from_user.id:
            continue
        if datetime.now() > datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S"):
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=MAILING_TEXT,
                )
            except Exception as e:
                print(f"Failed to send mailing message to {user.telegram_id}: {e}")
            try:
                await message.answer(
                    text="The message was successfully sent to <a href='tg://user?id=%s'>%s</a>"
                    % (user.telegram_id, user.first_name)
                )
            except Exception as e:
                print(f"Failed to send confirmation to admin for {user.telegram_id}: {e}")


@admin_router.message(IsAdminFilter(), Command("admin"))
async def admin_dashboard(message: types.Message):
    """Display the admin dashboard with inline buttons. Only accessible by the bot owner."""
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        try:
            await message.answer("You are not authorized to access the admin dashboard.")
        except Exception as e:
            print(f"Failed to send not authorized message: {e}")
        return
    try:
        await message.answer("<b>Admin Dashboard</b>\nChoose an action:", reply_markup=await admin_dashboard_keyboard())
    except Exception as e:
        print(f"Failed to send admin dashboard: {e}")


@admin_router.callback_query(lambda c: c.data and c.data.startswith("admin_"))
async def admin_dashboard_callback(call: types.CallbackQuery):
    """Handles admin dashboard button callbacks. Only accessible by the bot owner."""
    if call.from_user is None or call.from_user.id != BOT_OWNER_ID:
        try:
            await call.answer("Not authorized.", show_alert=True)
        except Exception as e:
            print(f"Failed to send not authorized callback: {e}")
        return
    try:
        if call.data == "admin_view_users":
            await call.message.answer("User list feature coming soon.")
        elif call.data == "admin_manage_subs":
            await call.message.answer("Manage subscriptions feature coming soon.")
        elif call.data == "admin_analytics":
            await call.message.answer("Analytics feature coming soon.")
        else:
            await call.answer("Unknown action.", show_alert=True)
    except Exception as e:
        print(f"Failed to handle admin dashboard callback: {e}")


@admin_router.message(IsAdminFilter(), Command("create_promo"))
async def create_promo_code(message: types.Message, command: CommandObject):
    """
    Allows the bot owner to create a promo code for free access.
    Usage: /create_promo CODE [max_uses] [expires_at]
    """
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        await message.answer("You are not authorized to create promo codes.")
        return
    args = command.args.split() if command.args else []
    if not args:
        await message.answer("Usage: /create_promo CODE [max_uses] [expires_at]")
        return
    code = args[0]
    max_uses = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    expires_at = args[2] if len(args) > 2 else None
    success = await PromoCodeRepository.create(code, max_uses, message.from_user.id, expires_at)
    if success:
        await message.answer(f"Promo code '{code}' created. Max uses: {max_uses}. Expires: {expires_at or 'never'}.")
    else:
        await message.answer("Failed to create promo code. It may already exist.")

@admin_router.message(IsAdminFilter(), Command("list_promos"))
async def list_promo_codes(message: types.Message):
    """
    Lists all promo codes for the bot owner.
    """
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        await message.answer("You are not authorized to view promo codes.")
        return
    import aiosqlite
    from data.config import sqlite_database_filepath
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        cursor = await connection.execute("SELECT code, is_active, used_count, max_uses, expires_at FROM PromoCodes")
        rows = await cursor.fetchall()
        if not rows:
            await message.answer("No promo codes found.")
            return
        text = "<b>Promo Codes:</b>\n"
        for row in rows:
            text += f"Code: <code>{row[0]}</code> | Active: {bool(row[1])} | Used: {row[2]}/{row[3] or '∞'} | Expires: {row[4] or 'never'}\n"
        await message.answer(text)
