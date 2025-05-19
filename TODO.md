# TODO & Ideas

This file tracks planned improvements, ideas, and future features for the Telegram subscription bot.

## Dependency Upgrades
- [x] Regularly update all dependencies in requirements.txt (especially aiogram, aiohttp, aiosqlite, etc.)
- [x] Monitor for security advisories and breaking changes

## Payment & Security
- [x] Ensure Solana is the exclusive payment method (remove legacy/unused payment code)
- [x] Improve error handling in payment and transaction modules
- [x] Add more robust validation for Solana transaction signatures
- [x] Consider rate limiting and anti-abuse mechanisms
- [ ] Implement robust transaction validation logic in payment handler (see commented-out validate_transaction in payment.py)

## Testing
- [x] Add unit tests for utils/solana_service.py and payment handlers
- [x] Add integration tests for subscription flows
- [x] Mock Solana API responses for test reliability
- [x] Integration test coverage for admin, dashboard, and subscription modules

## Documentation
- [x] Expand README with setup, deployment, and troubleshooting sections
- [x] Document all configuration options in config.py
- [x] Add code comments and docstrings throughout the codebase

## Features & Improvements
- [x] Admin dashboard for managing users and subscriptions
    - [x] User management (view, search, ban/unban users)
    - [x] Extend or revoke subscriptions manually
    - [x] Review and manage payments/transactions
    - [x] System health/status monitoring (uptime, error logs)
    - [x] Analytics and reporting (active users, revenue, churn)
    - [x] Admin notifications for critical events
- [x] Analytics/reporting for subscription activity
- [x] Scheduled notifications for expiring subscriptions

## Miscellaneous
- [x] Refactor utility functions for clarity and reusability
- [x] Clean up deprecated files (e.g., tronscan_service.py)
- [ ] Add CI/CD pipeline for automated testing and deployment

---
Feel free to add more ideas or mark completed items!