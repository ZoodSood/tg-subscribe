from typing import List, Optional, Union

import aiosqlite
from data.config import sqlite_database_filepath

from .models import User


async def get(
    database_id: Optional[int] = None, telegram_id: Optional[int] = None
) -> Union[User, None]:
    """
    Securely fetch a user by database_id or telegram_id. Returns User object or None.
    """
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


async def update_subscription_date(
    date: str,
    database_id: Optional[int] = None,
    telegram_id: Optional[int] = None,
) -> None:
    user = await get(database_id, telegram_id)
    if user is None:
        return None

    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {User.get_table_name()} SET days_sub_end=? WHERE id=?"
        await connection.execute(sql_query, (date, user.id))
        await connection.commit()


async def create_if_not_exist(
    telegram_id: int,
    firstname: Union[str, None],
    lastname: Union[str, None],
    username: Union[str, None],
    invite_link: Union[str, None] = None,
) -> None:
    record = await get(telegram_id=telegram_id)
    if record is None:
        async with aiosqlite.connect(sqlite_database_filepath) as connection:
            sql_query = f"""
                INSERT INTO {User.get_table_name()}
                {User.get_fields_for_sql_query()}
                VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)
            """
            params = (
                telegram_id,
                firstname,
                lastname,
                username,
                0,
                0,
                invite_link or '',
            )
            await connection.execute(sql_query, params)
            await connection.commit()


async def update_invite_link(
    invite_link: str,
    database_id: Optional[int] = None,
    telegram_id: Optional[int] = None,
) -> None:
    user = await get(database_id, telegram_id)
    if user is None:
        return

    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {User.get_table_name()} SET invite_link=? WHERE id=?"
        await connection.execute(sql_query, (invite_link, user.id))
        await connection.commit()


async def get_all() -> List[User]:
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"SELECT * FROM {User.get_table_name()}"
        cursor = await connection.execute(sql_query)
        rows = await cursor.fetchall()
        return [User(*row) for row in rows]


async def increase_balance_by(
    points: int,
    database_id: Optional[int] = None,
    telegram_id: Optional[int] = None,
) -> None:
    user = await get(database_id, telegram_id)
    if user is None:
        return

    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {User.get_table_name()} SET balance=? WHERE id=?"
        await connection.execute(sql_query, (user.balance + points, user.id))
        await connection.commit()


async def ban_user(database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> None:
    """
    Ban a user by setting is_banned to 1.
    """
    user = await get(database_id, telegram_id)
    if user is None:
        return
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {User.get_table_name()} SET is_banned=1 WHERE id=?"
        await connection.execute(sql_query, (user.id,))
        await connection.commit()


async def unban_user(database_id: Optional[int] = None, telegram_id: Optional[int] = None) -> None:
    """
    Unban a user by setting is_banned to 0.
    """
    user = await get(database_id, telegram_id)
    if user is None:
        return
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {User.get_table_name()} SET is_banned=0 WHERE id=?"
        await connection.execute(sql_query, (user.id,))
        await connection.commit()


async def update_last_active(database_id: Optional[int] = None, telegram_id: Optional[int] = None, timestamp: Optional[str] = None) -> None:
    """
    Update the last_active field for a user.
    If timestamp is None, use current datetime.
    """
    import datetime
    user = await get(database_id, telegram_id)
    if user is None:
        return
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {User.get_table_name()} SET last_active=? WHERE id=?"
        await connection.execute(sql_query, (timestamp, user.id))
        await connection.commit()
