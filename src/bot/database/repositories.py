"""
repositories.py
Repository classes for database access, separating SQL logic from business logic.
"""
import logging
from typing import List, Optional, Union
import aiosqlite
from data.config import sqlite_database_filepath
from .models import User, Transaction, PromoCode

class UserRepository:
    """
    Repository for User-related database operations.
    """
    @staticmethod
    async def get(database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> Optional[User]:
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                if database_id is not None:
                    sql_query = f"SELECT * FROM {User.get_table_name()} WHERE id=?"
                    params = (database_id,)
                elif telegram_id is not None:
                    sql_query = f"SELECT * FROM {User.get_table_name()} WHERE telegram_id=?"
                    params = (telegram_id,)
                else:
                    return None
                cursor = await connection.execute(sql_query, params)
                row = await cursor.fetchone()
                if row is None:
                    return None
                return User(*row)
        except Exception as e:
            logging.error(f"UserRepository.get error: {e}")
            return None

    @staticmethod
    async def update_subscription_date(date: str, database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> bool:
        try:
            user = await UserRepository.get(database_id, telegram_id)
            if user is None:
                return False
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"UPDATE {User.get_table_name()} SET days_sub_end=? WHERE id=?"
                await connection.execute(sql_query, (date, user.id))
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"UserRepository.update_subscription_date error: {e}")
            return False

    @staticmethod
    async def create_if_not_exist(telegram_id: int, firstname: Optional[str], lastname: Optional[str], username: Optional[str], invite_link: Optional[str] = None) -> bool:
        try:
            record = await UserRepository.get(telegram_id=telegram_id)
            if record is None:
                async with aiosqlite.connect(sqlite_database_filepath) as connection:
                    await connection.execute(
                        f"""
                            INSERT INTO {User.get_table_name()} {User.get_fields_for_sql_query()} VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)
                        """,
                        (telegram_id, firstname, lastname, username, 0, 0, invite_link or '')
                    )
                    await connection.commit()
            return True
        except Exception as e:
            logging.error(f"UserRepository.create_if_not_exist error: {e}")
            return False

    @staticmethod
    async def get_all() -> List[User]:
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"SELECT * FROM {User.get_table_name()}"
                cursor = await connection.execute(sql_query)
                rows = await cursor.fetchall()
                return [User(*row) for row in rows]
        except Exception as e:
            logging.error(f"UserRepository.get_all error: {e}")
            return []

    @staticmethod
    async def increase_balance_by(points: int, database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> bool:
        try:
            user = await UserRepository.get(database_id, telegram_id)
            if user is None:
                return False
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"UPDATE {User.get_table_name()} SET balance=? WHERE id=?"
                await connection.execute(sql_query, (user.balance + points, user.id))
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"UserRepository.increase_balance_by error: {e}")
            return False

    @staticmethod
    async def ban_user(database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> bool:
        try:
            user = await UserRepository.get(database_id, telegram_id)
            if user is None:
                return False
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"UPDATE {User.get_table_name()} SET is_banned=1 WHERE id=?"
                await connection.execute(sql_query, (user.id,))
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"UserRepository.ban_user error: {e}")
            return False

    @staticmethod
    async def unban_user(database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> bool:
        try:
            user = await UserRepository.get(database_id, telegram_id)
            if user is None:
                return False
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"UPDATE {User.get_table_name()} SET is_banned=0 WHERE id=?"
                await connection.execute(sql_query, (user.id,))
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"UserRepository.unban_user error: {e}")
            return False

    @staticmethod
    async def update_last_active(database_id: Optional[int] = None, telegram_id: Optional[int] = None, timestamp: Optional[str] = None) -> bool:
        import datetime
        try:
            user = await UserRepository.get(database_id, telegram_id)
            if user is None:
                return False
            if timestamp is None:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"UPDATE {User.get_table_name()} SET last_active=? WHERE id=?"
                await connection.execute(sql_query, (timestamp, user.id))
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"UserRepository.update_last_active error: {e}")
            return False

class TransactionRepository:
    """
    Repository for Transaction-related database operations.
    """
    @staticmethod
    async def get(database_id: Optional[int] = None, txid: Optional[str] = None) -> Optional[Transaction]:
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                if database_id is not None:
                    sql_query = f"SELECT * FROM {Transaction.get_table_name()} WHERE id=?"
                    params = (database_id,)
                elif txid is not None:
                    sql_query = f"SELECT * FROM {Transaction.get_table_name()} WHERE txid=?"
                    params = (txid,)
                else:
                    return None
                cursor = await connection.execute(sql_query, params)
                row = await cursor.fetchone()
                if row is None:
                    return None
                return Transaction(*row)
        except Exception as e:
            logging.error(f"TransactionRepository.get error: {e}")
            return None

    @staticmethod
    async def create(txid: str, user_telegram_id: int, weeks: int = 1) -> bool:
        from datetime import datetime
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                await connection.execute(
                    f"""
                        INSERT INTO {Transaction.get_table_name()} {Transaction.get_fields_for_sql_query()} VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (txid, user_telegram_id, False, weeks, int(datetime.now().timestamp()))
                )
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"TransactionRepository.create error: {e}")
            return False

    @staticmethod
    async def set_status(status: bool, database_id: Optional[int] = None, txid: Optional[str] = None) -> bool:
        try:
            transaction = await TransactionRepository.get(database_id, txid)
            if transaction is None:
                return False
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"UPDATE {Transaction.get_table_name()} SET status=? WHERE id=?"
                await connection.execute(sql_query, (status, transaction.id))
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"TransactionRepository.set_status error: {e}")
            return False

    @staticmethod
    async def get_new() -> List[Transaction]:
        from datetime import datetime, timedelta
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                sql_query = f"""
                    SELECT * FROM {Transaction.get_table_name()} WHERE status=? AND created_at_timestamp >= ?
                """
                cursor = await connection.execute(sql_query, (False, int((datetime.now() - timedelta(minutes=20)).timestamp())))
                rows = await cursor.fetchall()
                return [Transaction(*row) for row in rows]
        except Exception as e:
            logging.error(f"TransactionRepository.get_new error: {e}")
            return []

class PromoCodeRepository:
    """
    Repository for PromoCode-related database operations.
    """
    @staticmethod
    async def create(code: str, max_uses: int, created_by: int, expires_at: str = None) -> bool:
        """
        Create a new promo code.
        """
        import aiosqlite
        from data.config import sqlite_database_filepath
        from datetime import datetime, timezone
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                await connection.execute(
                    f"""
                        INSERT INTO PromoCodes (code, is_active, max_uses, used_count, created_by, created_at, expires_at, last_redeemed_by)
                        VALUES (?, 1, ?, 0, ?, ?, ?, NULL)
                    """,
                    (code, max_uses, created_by, datetime.now(timezone.utc).isoformat(), expires_at)
                )
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"PromoCodeRepository.create error: {e}")
            return False

    @staticmethod
    async def get_by_code(code: str):
        """
        Retrieve a promo code by its code string.
        """
        import aiosqlite
        from data.config import sqlite_database_filepath
        from .models import PromoCode
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                cursor = await connection.execute(
                    f"SELECT * FROM PromoCodes WHERE code=?", (code,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return PromoCode(*row)
        except Exception as e:
            logging.error(f"PromoCodeRepository.get_by_code error: {e}")
            return None

    @staticmethod
    async def redeem(code: str, user_telegram_id: int) -> bool:
        """
        Redeem a promo code for a user, increment usage, and deactivate if max uses reached.
        """
        import aiosqlite
        from data.config import sqlite_database_filepath
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                cursor = await connection.execute(
                    f"SELECT * FROM PromoCodes WHERE code=?", (code,)
                )
                row = await cursor.fetchone()
                if row is None:
                    return False
                promo = list(row)
                used_count = promo[4] + 1
                max_uses = promo[3]
                is_active = promo[2]
                if not is_active or (max_uses and used_count > max_uses):
                    return False
                await connection.execute(
                    f"UPDATE PromoCodes SET used_count=?, last_redeemed_by=?, is_active=? WHERE code=?",
                    (used_count, user_telegram_id, 0 if (max_uses and used_count >= max_uses) else 1, code)
                )
                await connection.commit()
            return True
        except Exception as e:
            logging.error(f"PromoCodeRepository.redeem error: {e}")
            return False

    @staticmethod
    async def get_all() -> List[PromoCode]:
        """
        List all promo codes.
        """
        import aiosqlite
        from data.config import sqlite_database_filepath
        from .models import PromoCode
        try:
            async with aiosqlite.connect(sqlite_database_filepath) as connection:
                cursor = await connection.execute(f"SELECT * FROM PromoCodes")
                rows = await cursor.fetchall()
                return [PromoCode(*row) for row in rows]
        except aiosqlite.Error as e:
            logging.error(f"PromoCodeRepository.get_all database error: {e}")
            return []
