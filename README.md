# Telegram Bot with Subscription Functionality 🤖

## Overview
This Telegram bot provides a robust subscription management system, supporting advanced admin controls, analytics, and secure Solana-based payments. Originally based on a public template, it has been heavily customized for client needs, with all legacy Tron payment code removed and Solana as the exclusive payment method.

---

- [Introduction](#introduction)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [Usage](#usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

# Telegram Bot with Subscription Functionality 🤖
## Features
- **Solana-Only Payments:** Secure, validated payments using Solana.
- **Flexible Subscription Plans:** Support for multiple plans and durations, with customizable pricing.
- **Admin Dashboard:** Manage users, subscriptions, payments, and system health from a single interface.
- **User Management:** View, search, ban/unban users, and manually extend or revoke subscriptions.
- **Analytics & Reporting:** Track active users, revenue, churn, and more.
- **Scheduled Notifications:** Automated reminders for expiring subscriptions.
- **Security:** Robust validation of Solana transaction signatures, error handling, and anti-abuse mechanisms.
- **Multi-Channel Support:** Manage access to multiple private Telegram channels.
- **Configurable & Extensible:** All key options are set in a single config file.

## Testing

This project includes comprehensive unit and integration tests to ensure reliability and maintainability.

- **Unit Tests:** Cover core utilities such as `utils/solana_service.py` and payment handlers.
- **Integration Tests:** Validate end-to-end subscription flows, including admin, dashboard, and subscription modules.
- **Solana API Mocking:** Solana API responses are mocked to improve test reliability and eliminate external dependencies during testing.

### Running Tests

1. Activate your virtual environment (see Installation section).
2. Run all tests using:
   ```shell
   pytest
   ```
   Or run specific tests (e.g., unit or integration) with:
   ```shell
   pytest tests/unit/
   pytest tests/integration/
   ```

> **Note:** Ensure all dependencies are installed and configuration files are set up before running tests.

## Project Structure

```css
.
├── .env-dist
├── README.md
├── requirements.txt
└── src
    ├── bot
    │   ├── app.py
    │   ├── data
    │   │   └── config.py
    │   ├── database
    │   ├── filters
    │   ├── handlers
    │   ├── keyboards
    │   ├── loader.py
    │   ├── logs
    │   ├── middlewares
    │   ├── statesgroup.py
    │   └── utils
    └── db
        └── database_schema.sql
```

## Installation
**Requirements:** Python 3.8–3.11

1. **Clone the repository:**
   ```shell
   git clone https://github.com/ProgerOffline/subscribe.git
   cd subscribe
   ```
2. **Create a virtual environment (recommended):**
   ```shell
   python -m venv venv
   ```
3. **Activate the virtual environment:**
   - On Linux/macOS:
     ```shell
     source venv/bin/activate
     ```
   - On Windows:
     ```shell
     venv\Scripts\activate
     ```
4. **Upgrade pip:**
   ```shell
   pip install --upgrade pip
   ```
5. **Install dependencies:**
   ```shell
   pip install -r requirements.txt
   ```

## Configuration

Before running the bot, you need to configure the following parameters:

### 0.0 Create a bot on Telegram and obtain its token from BotFather.

### 1. Environment Variables
Rename `.env-dist` to `.env` and fill in your values:
```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_OWNER_ID=123456789
```

### 2. Config File (`src/bot/data/config.py`)
This file controls all bot behavior. Key options:
```python
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
BOT_OWNER_ID = env.int("BOT_OWNER_ID")

# Solana wallet address for receiving payments
SOLANA_WALLET_ADDRESS = "EnterYourSolanaWalletAddressHere"

# Subscription pricing by plan (weeks: amount in USD equivalent in SOL)
# Example: 1 week for $200 worth of SOL
SUBSCRIBE_AMOUNT_BY_PLANS = {
    1: 200,  # 1 week: $200 (in SOL equivalent)
}

# Subscription duration (days per payment)
NUMBER_DAYS_FROM_ONE_PAYMENT = 7

# Days before expiry to notify users
SUBSCRIBE_END_NOTIFICATION_DAYS = [3, 1]

# List of admin Telegram user IDs
ADMINS_ID_LIST = []

# Private channels managed by the bot
private_channels = {
    "Channel 1": {"id": -100123456789, "invite_url": "https://t.me/+ABCDEFGHIJKL"},
    "Channel 2": {"id": -100123456789, "invite_url": "https://t.me/+ABCDEFGHIJKL"},
    # Add more channels as needed
}

# Payment deviation settings (optional)
AMOUNT_DEVIATION_ENABLED = False  # Allow small deviation in payment amount
AMOUNT_DEVIATION_VALUE = 0.01     # Allowed deviation in SOL
```
**Tip:** All configuration is done in this file and your `.env` file. No code changes are needed for basic setup.

## Running
1. **Start the bot:**
   ```shell
   cd src/bot/
   python app.py
   ```
2. The bot will now respond to commands and manage subscriptions/payments automatically.

## Usage
- **Admin Dashboard:** Access via Telegram (details in code or by contacting the bot owner).
- **User Subscription:** Users pay the required SOL amount to the configured wallet. The bot verifies payment and grants access to private channels.
- **Notifications:** Users are notified before their subscription expires.
- **Manual Management:** Admins can extend, revoke, or review subscriptions/payments from the dashboard.

## Troubleshooting
- **Bot not starting?** Check your Python version, virtual environment, and that all dependencies are installed.
- **Payments not detected?** Ensure the Solana wallet address is correct and that the bot has internet access.
- **Need to add more channels or admins?** Edit `private_channels` and `ADMINS_ID_LIST` in `config.py`.

## Notes
- All Tron/legacy payment code has been removed. Only Solana is supported.
- For advanced customization, review the code in `src/bot/handlers/` and `src/bot/utils/solana_service.py`.
- For automated testing and deployment, see the TODO list for planned CI/CD improvements. (CI/CD pipeline coming soon)

---

For further help, open an issue or contact the project maintainer.
