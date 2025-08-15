import pytest
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.bot.keyboards import reply

@pytest.mark.asyncio
async def test_close_functionality_keyboard():
    keyboard = await reply.close_functionality()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 4
    assert keyboard.keyboard[0][0].text == "Balance"
    assert keyboard.keyboard[1][0].text == "Renew subscription"
    assert keyboard.keyboard[2][0].text == "Show close functionality"
    assert keyboard.keyboard[3][0].text == "Check subscription"

@pytest.mark.asyncio
async def test_retry_or_cancel_keyboard():
    keyboard = await reply.retry_or_cancel()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 2
    assert keyboard.keyboard[0][0].text == "Retry"
    assert keyboard.keyboard[1][0].text == "Cancel"

@pytest.mark.asyncio
async def test_make_subscribtion_keyboard():
    keyboard = await reply.make_subscribtion()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 3
    assert keyboard.keyboard[0][0].text == "Balance"
    assert keyboard.keyboard[1][0].text == "Make subscription"
    assert keyboard.keyboard[2][0].text == "Check subscription"

@pytest.mark.asyncio
async def test_confirm_transfer_keyboard():
    keyboard = await reply.confirm_transfer()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 2
    assert keyboard.keyboard[0][0].text == "Confirm transfer"
    assert keyboard.keyboard[1][0].text == "Back to main menu"

@pytest.mark.asyncio
async def test_check_transaction_keyboard():
    keyboard = await reply.check_transaction()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 1
    assert keyboard.keyboard[0][0].text == "Check transaction"

@pytest.mark.asyncio
async def test_back_to_main_menu_keyboard():
    keyboard = await reply.back_to_main_menu()
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 1
    assert keyboard.keyboard[0][0].text == "Back to main menu"

@pytest.mark.asyncio
async def test_subscription_termins_keyboard():
    plans = [1, 2, 4]
    keyboard = await reply.subscription_termins(plans)
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 2
    assert len(keyboard.keyboard[0]) == 3
    assert keyboard.keyboard[0][0].text == "1 week"
    assert keyboard.keyboard[0][1].text == "2 week"
    assert keyboard.keyboard[0][2].text == "4 week"
    assert keyboard.keyboard[1][0].text == "Back to main menu"


# --- inline.py tests ---
from src.bot.keyboards import inline
from aiogram import types
from unittest.mock import patch

@pytest.mark.asyncio
async def test_channels_keyboard():
    with patch('src.bot.keyboards.inline.private_channels', {"Channel 1": {"invite_url": "url1"}, "Channel 2": {"invite_url": "url2"}}):
        keyboard = await inline.channels()
        assert isinstance(keyboard, types.InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2
        assert keyboard.inline_keyboard[0][0].text == "Channel 1"
        assert keyboard.inline_keyboard[0][0].url == "url1"
        assert keyboard.inline_keyboard[1][0].text == "Channel 2"
        assert keyboard.inline_keyboard[1][0].url == "url2"

@pytest.mark.asyncio
async def test_admin_dashboard_keyboard():
    keyboard = await inline.admin_dashboard_keyboard()
    assert isinstance(keyboard, types.InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 3
    assert keyboard.inline_keyboard[0][0].text == "View Users"
    assert keyboard.inline_keyboard[0][0].callback_data == "admin_view_users"
    assert keyboard.inline_keyboard[1][0].text == "Manage Subs"
    assert keyboard.inline_keyboard[1][0].callback_data == "admin_manage_subs"
    assert keyboard.inline_keyboard[2][0].text == "Analytics"
    assert keyboard.inline_keyboard[2][0].callback_data == "admin_analytics"
