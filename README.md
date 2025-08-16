# Telegram Bot with Subscription Functionality 🤖

## Overview
This Telegram bot provides a robust subscription management system, supporting advanced admin controls, analytics, and secure Solana-based payments. Originally based on a public template, it has been heavily customized for client needs, with nearly all legacy payment code removed and Solana as the exclusive payment method.

---

- [Introduction](#introduction)
- [Alternative Approach: Refactored Payment System](#alternative-approach-refactored-payment-system)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [Usage](#usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Alternative Approach: Refactored Payment System

This branch presents a significant refactoring of the bot's payment and subscription logic to enhance security, reliability, and maintainability. This alternative approach addresses several critical issues found in the original implementation.

Key improvements include:

- **Direct Solana RPC Integration**: The fragile reliance on public block explorers (like Solscan) has been replaced with direct communication with the Solana network via the `solana-py` library. This provides a more robust and secure method for verifying transactions.

- **Dynamic SOL/USD Pricing**: A new `PriceService` has been implemented to fetch real-time SOL/USD exchange rates from the CoinGecko API. This ensures that subscription prices are always accurate and reflect their intended USD value.

- **Centralized Validation Logic**: A dedicated `PaymentValidator` service has been introduced to centralize and streamline all payment validation logic. This includes checks for transaction uniqueness, signature validity, and payment amount correctness.

- **Improved Code Structure**: The codebase has been refactored to use consistent relative imports, making it more robust and easier to test and maintain.

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

This branch includes a new, comprehensive test suite built from the ground up to ensure the reliability and maintainability of the refactored payment system.

- **Unit Tests:** Cover core services, including `PriceService`, `SolanaService`, and `PaymentValidator`.
- **Integration Tests:** Validate the end-to-end payment flow in the `payment.py` handler.
- **Mocking**: All external services (CoinGecko API, Solana RPC) are mocked to ensure reliable and fast test execution.

### Running Tests

1.  Ensure you have created a `.env` file and installed all dependencies from `requirements.txt`.
2.  Run the full test suite from the root of the project:
    ```shell
    PYTHONPATH=. python -m pytest
    ```
    Or run specific tests:
    ```shell
    PYTHONPATH=. python -m pytest tests/unit/
    PYTHONPATH=. python -m pytest tests/integration/
    ```

## Project Structure

```
.
├── .env-dist
├── README.md
├── requirements.txt
├── tests/
│   ├── unit/
│   └── integration/
└── src/
    ├── bot/
    │   ├── app.py
    │   ├── data/
    │   │   └── config.py
    │   ├── database/
    │   ├── filters/
    │   ├── handlers/
    │   ├── keyboards/
    │   ├── loader.py
    │   ├── middlewares/
    │   ├── services/
    │   ├── statesgroup.py
    │   └── utils/
    └── db/
        └── database_schema.sql
```

## Installation
**Requirements:** Python 3.8–3.11

1.  **Clone the repository:**
    ```shell
    git clone https://github.com/ProgerOffline/subscribe.git
    cd subscribe
    ```
2.  **Create a virtual environment (recommended):**
    ```shell
    python -m venv venv
    ```
3.  **Activate the virtual environment:**
    - On Linux/macOS:
      ```shell
      source venv/bin/activate
      ```
    - On Windows:
      ```shell
      venv\Scripts\activate
      ```
4.  **Upgrade pip:**
    ```shell
    pip install --upgrade pip
    ```
5.  **Install dependencies:**
    ```shell
    pip install -r requirements.txt
    ```

## Configuration

Before running the bot, you need to configure the following parameters:

> **Note:** Create a bot on Telegram and obtain its token from BotFather.

### 1. Environment Variables
Rename `.env-dist` to `.env` and fill in your values. You will need to provide a valid Solana RPC URL.

```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_OWNER_ID=123456789
SOLANA_WALLET_ADDRESS=your-solana-wallet-address-here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### 2. Config File (`src/bot/data/config.py`)
This file controls all bot behavior. Key options:
```python
# Subscription pricing by plan (weeks: amount in USD)
SUBSCRIBE_AMOUNT_BY_PLANS = {
    1: 200,  # 1 week: $200
}

# Private channels managed by the bot
private_channels = {
    "Channel 1": {"id": -100123456789, "invite_url": "https://t.me/+ABCDEFGHIJKL"},
}

# Payment deviation settings (optional)
AMOUNT_DEVIATION_ENABLED = False  # Allow small deviation in payment amount
AMOUNT_DEVIATION_VALUE = 0.01     # Allowed deviation in SOL
```

## Running
1.  **Start the bot:**
    ```shell
    cd src/bot/
    python app.py
    ```
2.  The bot will now respond to commands and manage subscriptions/payments automatically.

## Usage
- **Admin Dashboard:** Access via Telegram (details in code or by contacting the bot owner).
- **User Subscription:** Users pay the required SOL amount to the configured wallet. The bot verifies payment and grants access to private channels.
- **Notifications:** Users are notified before their subscription expires.
- **Manual Management:** Admins can extend, revoke, or review subscriptions/payments from the dashboard.

## Troubleshooting
- **Bot not starting?** Check your Python version, virtual environment, and that all dependencies are installed.
- **Payments not detected?** Ensure the Solana wallet address and RPC URL are correct and that the bot has internet access.
- **Need to add more channels or admins?** Edit `private_channels` and `ADMINS_ID_LIST` in `config.py`.

## Notes
- Tron payment has been removed. Only Solana is supported.
- For automated testing and deployment, see the TODO list for planned improvements. (CI/CD pipeline with Docker coming soon)

---

For further help, open an issue or contact the project maintainer.
