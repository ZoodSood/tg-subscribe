"""
Dashboard handler for advanced admin and management features.
Includes: user management, subscription control, payment review, analytics, and system health monitoring.
"""

from aiogram import Router, types
from aiogram.filters import Command
from filters import IsAdminFilter
from loader import bot
from keyboards.inline import admin_dashboard_keyboard
from data.config import BOT_OWNER_ID
from datetime import datetime, timedelta
import psutil

# Create a separate router for dashboard features
dashboard_router = Router()

# Define START_TIME for uptime calculation
START_TIME = datetime.now()

@dashboard_router.message(IsAdminFilter(), Command("dashboard"))
async def dashboard_entry(message: types.Message):
    """
    Entry point for the admin dashboard. Presents advanced management options.
    Only accessible by the bot owner.
    """
    if message.from_user is None or message.from_user.id != BOT_OWNER_ID:
        await message.answer("You are not authorized to access the admin dashboard.")
        return
    await message.answer(
        "<b>Advanced Admin Dashboard</b>\nChoose an action:",
        reply_markup=await admin_dashboard_keyboard()
    )

@dashboard_router.callback_query(lambda c: c.data and c.data.startswith("admin_"))
async def dashboard_callback(call: types.CallbackQuery):
    """
    Handles advanced admin dashboard button callbacks.
    Only accessible by the bot owner.
    """
    from database import users, transactions
    if call.from_user is None or call.from_user.id != BOT_OWNER_ID:
        await call.answer("Not authorized.", show_alert=True)
        return
    if call.data == "admin_view_users":
        # Fetch all users and show a summary
        all_users = await users.get_all()
        user_count = len(all_users)
        banned_count = sum(1 for u in all_users if getattr(u, 'is_banned', 0))
        user_lines = []
        for u in all_users:
            status = "🚫 Banned" if getattr(u, 'is_banned', 0) else "✅ Active"
            first_name = getattr(u, 'first_name', '') or ''
            last_name = getattr(u, 'last_name', '') or ''
            username = getattr(u, 'username', '-') or '-'
            telegram_id = getattr(u, 'telegram_id', getattr(u, 'id', '-'))
            user_lines.append(f"<b>{first_name} {last_name}</b> (@{username}), ID: <code>{telegram_id}</code> - {status}")
        users_text = "\n".join(user_lines[:30])  # Limit to 30 users for display
        await call.message.answer(f"[User Management]\nTotal users: <b>{user_count}</b>\nBanned: <b>{banned_count}</b>\n\n{users_text if users_text else 'No users found.'}\n\nUse /ban or /unban commands for user control.")
    elif call.data == "admin_manage_subs":
        # Show how many users have active subscriptions
        all_users = await users.get_all()
        active_subs = 0
        expired_subs = 0
        now = datetime.now()
        for u in all_users:
            days_sub_end = getattr(u, 'days_sub_end', None)
            if days_sub_end:
                try:
                    sub_end = datetime.strptime(days_sub_end, "%Y-%m-%d %H:%M:%S")
                    if sub_end > now:
                        active_subs += 1
                    else:
                        expired_subs += 1
                except Exception:
                    expired_subs += 1
            else:
                expired_subs += 1
        await call.message.answer(f"[Subscription Management]\nActive subscriptions: <b>{active_subs}</b>\nExpired: <b>{expired_subs}</b>\nTotal users: <b>{len(all_users)}</b>\nUse /extend or /revoke commands for manual control.")
    elif call.data == "admin_payments":
        # Show total payments and recent transactions
        all_tx = []
        try:
            all_tx = await transactions.get_all()
        except Exception:
            pass
        tx_count = len(all_tx)
        await call.message.answer(f"[Payments/Transactions]\nTotal transactions: <b>{tx_count}</b>\nFeature: payment review coming soon.")
    elif call.data == "admin_health":
        memory = psutil.virtual_memory()
        await call.message.answer(
            f"[System Health]\n"
            f"Memory: {memory.percent}% used\n"
            f"CPU: {psutil.cpu_percent()}% utilization\n"
            f"Uptime: {datetime.now() - START_TIME}"
        )
    elif call.data == "admin_analytics":
        all_users = await users.get_all()
        now = datetime.now()
        active_last_week = 0
        for u in all_users:
            last_active = getattr(u, 'last_active', None)
            if last_active:
                try:
                    last_active_dt = datetime.strptime(last_active, "%Y-%m-%d %H:%M:%S")
                    if last_active_dt > now - timedelta(days=7):
                        active_last_week += 1
                except Exception:
                    pass
        await call.message.answer(f"[Analytics]\nActive users (7d): <b>{active_last_week}</b>\nTotal users: <b>{len(all_users)}</b>")
    elif call.data == "admin_notifications":
        await call.message.answer("[Admin Notifications]\nFeature coming soon: critical event alerts.")
    else:
        await call.answer("Unknown action.", show_alert=True)