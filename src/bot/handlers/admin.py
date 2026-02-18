from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.config import MAILING_TEXT, BOT_OWNER_ID
from database import users
from filters import IsAdminFilter
from loader import bot
from keyboards.inline import admin_dashboard_keyboard
from database.repositories import PromoCodeRepository
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

    promos = await PromoCodeRepository.get_all()
    if not promos:
        await message.answer("No promo codes found.")
        return

    text = "<b>Promo Codes:</b>\n"
    for p in promos:
        text += f"Code: <code>{p.code}</code> | Active: {bool(p.is_active)} | Used: {p.used_count}/{p.max_uses or '∞'} | Expires: {p.expires_at or 'never'}\n"
    await message.answer(text)


@admin_router.message(IsAdminFilter(), Command("ban"))
async def ban_user_handler(message: types.Message, command: CommandObject):
    """Bans a user by Telegram ID."""
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        return
    if not command.args:
        await message.answer("Usage: /ban <telegram_id>")
        return
    try:
        user_id = int(command.args.split()[0])
        await users.ban_user(telegram_id=user_id)
        await message.answer(f"User <code>{user_id}</code> has been banned.")
    except ValueError:
        await message.answer("Invalid Telegram ID.")


@admin_router.message(IsAdminFilter(), Command("unban"))
async def unban_user_handler(message: types.Message, command: CommandObject):
    """Unbans a user by Telegram ID."""
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        return
    if not command.args:
        await message.answer("Usage: /unban <telegram_id>")
        return
    try:
        user_id = int(command.args.split()[0])
        await users.unban_user(telegram_id=user_id)
        await message.answer(f"User <code>{user_id}</code> has been unbanned.")
    except ValueError:
        await message.answer("Invalid Telegram ID.")


@admin_router.message(IsAdminFilter(), Command("extend"))
async def extend_subscription_handler(message: types.Message, command: CommandObject):
    """Extends a user's subscription by a number of weeks."""
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        return
    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("Usage: /extend <telegram_id> <weeks>")
        return
    try:
        user_id = int(args[0])
        weeks = int(args[1])
        user = await users.get(telegram_id=user_id)
        if not user:
            await message.answer("User not found.")
            return

        from datetime import datetime, timedelta
        now = datetime.now()
        if user.days_sub_end:
            try:
                current_end = datetime.strptime(user.days_sub_end, "%Y-%m-%d %H:%M:%S")
                if current_end > now:
                    now = current_end
            except Exception:
                pass

        new_end = now + timedelta(weeks=weeks)
        await users.update_subscription_date(new_end.strftime("%Y-%m-%d %H:%M:%S"), telegram_id=user_id)
        await message.answer(f"Subscription for <code>{user_id}</code> extended by {weeks} weeks until <code>{new_end.strftime('%Y-%m-%d %H:%M:%S')}</code>.")
    except ValueError:
        await message.answer("Invalid input. Usage: /extend <telegram_id> <weeks>")


@admin_router.message(IsAdminFilter(), Command("revoke"))
async def revoke_subscription_handler(message: types.Message, command: CommandObject):
    """Revokes a user's subscription."""
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        return
    if not command.args:
        await message.answer("Usage: /revoke <telegram_id>")
        return
    try:
        user_id = int(command.args.split()[0])
        await users.update_subscription_date("2000-01-01 00:00:00", telegram_id=user_id)
        await message.answer(f"Subscription for <code>{user_id}</code> has been revoked.")
    except ValueError:
        await message.answer("Invalid Telegram ID.")
