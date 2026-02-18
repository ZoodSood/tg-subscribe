import dataclasses
from typing import Optional


@dataclasses.dataclass()
class User:
    id: int
    telegram_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    days_sub_end: str
    balance: int
    invite_link: str  # Unique invite link for this user (Telegram channel access only)
    is_banned: int = 0  # 0 = not banned, 1 = banned
    last_active: Optional[str] = None  # Last activity timestamp (ISO format)

    @staticmethod
    def get_fields_for_sql_query():
        fields = [field.name for field in dataclasses.fields(User)][1:]
        return f"({', '.join(fields)})"

    @staticmethod
    def get_table_name():
        return "Users"


@dataclasses.dataclass()
class Transaction:
    id: int
    txid: str
    owner_telegram_id: int
    status: bool
    weeks: int  # Number of weeks for the subscription
    created_at_timestamp: int

    @staticmethod
    def get_fields_for_sql_query():
        fields = [field.name for field in dataclasses.fields(Transaction)][1:]
        return f"({', '.join(fields)})"

    @staticmethod
    def get_table_name():
        return "Transactions"


@dataclasses.dataclass()
class PromoCode:
    """
    Dataclass representing a promo code for granting free access.
    Fields:
        code: The unique promo code string.
        is_active: Whether the promo code is currently valid.
        max_uses: Maximum number of times this code can be redeemed (None for unlimited).
        used_count: Number of times the code has been redeemed.
        created_by: Telegram ID of the creator (bot owner).
        created_at: Timestamp of creation.
        expires_at: Optional expiration timestamp.
        last_redeemed_by: Telegram ID of the last user who redeemed it (for audit).
    """
    id: int
    code: str
    is_active: int  # 1 = active, 0 = inactive
    max_uses: int  # 0 or NULL for unlimited
    used_count: int
    created_by: int
    created_at: str
    expires_at: str = None
    last_redeemed_by: int = None

    @staticmethod
    def get_fields_for_sql_query():
        fields = [field.name for field in dataclasses.fields(PromoCode)][1:]
        return f"({', '.join(fields)})"

    @staticmethod
    def get_table_name():
        return "PromoCodes"
