from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..data.config import private_channels


async def channels() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for name in private_channels.keys():
        builder.add(
            types.InlineKeyboardButton(
                text=name,
                url=private_channels[name]["invite_url"],
            )
        )
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


async def admin_dashboard_keyboard() -> types.InlineKeyboardMarkup:
    """Builds the inline keyboard for the admin dashboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="View Users", callback_data="admin_view_users")
    builder.button(text="Manage Subs", callback_data="admin_manage_subs")
    builder.button(text="Analytics", callback_data="admin_analytics")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
