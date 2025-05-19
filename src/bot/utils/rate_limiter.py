"""
Utility for simple in-memory rate limiting per user.
Limits how often a user can perform a sensitive action (e.g., payment initiation).
"""
import time
from typing import Dict

# Default: allow 1 action per 60 seconds per user
RATE_LIMIT_SECONDS = 5

# Stores last action timestamp per user_id
_last_action: Dict[int, float] = {}

def is_allowed(user_id: int, limit_seconds: int = RATE_LIMIT_SECONDS) -> bool:
    """
    Check if the user is allowed to perform the action now.
    Args:
        user_id (int): Telegram user ID
        limit_seconds (int): Minimum seconds between actions
    Returns:
        bool: True if allowed, False if rate limited
    """
    now = time.time()
    last = _last_action.get(user_id, 0)
    if now - last >= limit_seconds:
        _last_action[user_id] = now
        return True
    return False

def time_until_allowed(user_id: int, limit_seconds: int = RATE_LIMIT_SECONDS) -> int:
    """
    Returns seconds until the user can perform the action again.
    Args:
        user_id (int): Telegram user ID
        limit_seconds (int): Minimum seconds between actions
    Returns:
        int: Seconds remaining
    """
    now = time.time()
    last = _last_action.get(user_id, 0)
    remaining = int(limit_seconds - (now - last))
    return max(0, remaining)