"""
Unit tests for solana_service.py (Solana payment and validation logic).
Mocks Solana API responses for reliability.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.bot.utils import solana_service

class TestSolanaService(unittest.TestCase):
    def setUp(self):
        # Example: set up test wallet addresses, signatures, etc.
        self.valid_signature = "test_signature"
        self.invalid_signature = "bad_signature"
        self.wallet = "test_wallet"
        self.amount = 1.23

    @patch("src.bot.utils.solana_service.requests.post")
    def test_validate_transaction_success(self, mock_post):
        # Mock a successful Solana API response
        mock_post.return_value.json.return_value = {
            "result": {
                "value": {
                    "meta": {"err": None},
                    "transaction": {"message": {"accountKeys": [self.wallet]}, "signatures": [self.valid_signature]}
                }
            }
        }
        mock_post.return_value.status_code = 200
        result = solana_service.validate_transaction(self.valid_signature, self.wallet, self.amount)
        self.assertTrue(result)

    @patch("src.bot.utils.solana_service.requests.post")
    def test_validate_transaction_failure(self, mock_post):
        # Mock a failed Solana API response (invalid signature)
        mock_post.return_value.json.return_value = {"result": {"value": None}}
        mock_post.return_value.status_code = 200
        result = solana_service.validate_transaction(self.invalid_signature, self.wallet, self.amount)
        self.assertFalse(result)

    @patch("src.bot.utils.solana_service.requests.post")
    def test_validate_transaction_api_error(self, mock_post):
        # Simulate API/network error
        mock_post.side_effect = Exception("API error")
        result = solana_service.validate_transaction(self.valid_signature, self.wallet, self.amount)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()