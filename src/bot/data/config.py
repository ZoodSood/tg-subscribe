import os
from pathlib import Path

from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")

# The Telegram user ID of the bot owner. Set this in your .env file as BOT_OWNER_ID, or hardcode here for testing.
BOT_OWNER_ID = env.int("BOT_OWNER_ID", default=123456789)  # Replace 123456789 with your actual Telegram user ID
database_filename = "database.db"
schema_filename = "database_schema.sql"
project_filepath = Path(__file__).resolve().parent.parent.parent

sqlite_database_filepath = os.path.join(project_filepath, "db", database_filename)
sqlite_schema_filepath = os.path.join(project_filepath, "db", schema_filename)

# Securely load Solana wallet address from environment variable and validate format
SOLANA_WALLET_ADDRESS = env.str("SOLANA_WALLET_ADDRESS", default=None)
if not SOLANA_WALLET_ADDRESS:
    raise ValueError("SOLANA_WALLET_ADDRESS must be set in the environment variables.")
import re
if not re.fullmatch(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", SOLANA_WALLET_ADDRESS):
    raise ValueError("Invalid SOLANA_WALLET_ADDRESS format. Please check your configuration.")

# Key - count weeks
# Value - subscribe amount (USD equivalent in SOL, e.g., 200 means $200 worth of SOL)
# You can customise this dict
SUBSCRIBE_AMOUNT_BY_PLANS = {
    1: 200,  # 1 week: $200 (in SOL equivalent)
}
NUMBER_DAYS_FROM_ONE_PAYMENT = 7
SUBSCRIBE_END_NOTIFICATION_DAYS = [3, 1]

ADMINS_ID_LIST = []
private_channels = {
    "Channel 1": {"id": -100123456789, "invite_url": "https://t.me/+ABCDEFGHIJKL"},
    "Channel 2": {"id": -100123456789, "invite_url": "https://t.me/+ABCDEFGHIJKL"},
# Add more channels as needed
}

"""
    Use HTML to format text

    <b>bold</b>, <strong>bold</strong>
    <i>italic</i>, <em>italic</em>
    <u>underline</u>, <ins>underline</ins>
    <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
    <span class="tg-spoiler">spoiler</span>, <tg-spoiler>spoiler</tg-spoiler>
    <b>bold <i>italic bold <s>italic bold strikethrough <span class="tg-spoiler">italic bold strikethrough spoiler</span></s> <u>underline italic bold</u></i> bold</b>
    <a href="http://www.example.com/">inline URL</a>
    <a href="tg://user?id=123456789">inline mention of a user</a>
    <tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>
    <code>inline fixed-width code</code>
    <pre>pre-formatted fixed-width code block</pre>
    <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
    <blockquote>Block quotation started\nBlock quotation continued\nThe last line of the block quotation</blockquote>

    And user \n to print the next text on a new line
"""
MAILING_TEXT = "Hello"

# Optional: Enable/disable payment amount deviation and set allowed deviation value (in SOL)
# If enabled, allows a small deviation in the payment amount (in SOL). Disabled by default for strict payment validation.
AMOUNT_DEVIATION_ENABLED = False  # Admin can enable this to allow payment amount deviation
AMOUNT_DEVIATION_VALUE = 0.01  # Allow ±0.01 SOL deviation

# Function for per-user wallet generation tied to UID (to be implemented in solana_service or relevant module)
# def generate_user_wallet(telegram_uid: int) -> str:
#     """
#     Generates a unique Solana wallet address for a user based on their Telegram UID.
#     This ensures each user has a dedicated wallet for payments.
#     """
#     pass
