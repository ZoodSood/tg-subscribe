import pytest
from unittest.mock import patch
from src.bot.utils import rate_limiter

def test_is_allowed_first_time():
    """Test that the first call to is_allowed is always allowed."""
    rate_limiter._last_action.clear()
    assert rate_limiter.is_allowed(123) is True

def test_is_allowed_within_limit():
    """Test that a second call within the limit is not allowed."""
    rate_limiter._last_action.clear()
    with patch('time.time', return_value=1000):
        assert rate_limiter.is_allowed(123) is True
    with patch('time.time', return_value=1001):
        assert rate_limiter.is_allowed(123) is False

def test_is_allowed_after_limit():
    """Test that a call after the limit has passed is allowed."""
    rate_limiter._last_action.clear()
    with patch('time.time', return_value=1000):
        assert rate_limiter.is_allowed(123) is True
    with patch('time.time', return_value=1006):
        assert rate_limiter.is_allowed(123) is True

def test_time_until_allowed():
    """Test time_until_allowed returns the correct remaining time."""
    rate_limiter._last_action.clear()
    with patch('time.time', return_value=1000):
        rate_limiter.is_allowed(123)
    with patch('time.time', return_value=1002):
        assert rate_limiter.time_until_allowed(123) == 3
    with patch('time.time', return_value=1006):
        assert rate_limiter.time_until_allowed(123) == 0

def test_time_until_allowed_no_previous_action():
    """Test time_until_allowed when there has been no previous action."""
    rate_limiter._last_action.clear()
    assert rate_limiter.time_until_allowed(123) == 0
