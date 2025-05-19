from typing import Dict
from data.config import SUBSCRIBE_AMOUNT_BY_PLANS

class PaymentService:
    """
    Service for payment-related business logic, such as calculating payment amounts.
    """
    @staticmethod
    def get_amount_for_plan(weeks: int) -> int:
        """
        Returns the required payment amount for a given subscription plan (in weeks).
        """
        return SUBSCRIBE_AMOUNT_BY_PLANS.get(weeks, 0)