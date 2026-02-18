from datetime import datetime, timedelta
from typing import List, Optional, Union

import aiosqlite
from data.config import sqlite_database_filepath

from .models import Transaction


async def get(
    database_id: Optional[int] = None, txid: Optional[str] = None
) -> Union[Transaction, None]:
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


async def create(txid: str, user_telegram_id: int, weeks: int = 1) -> None:
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"""
            INSERT INTO {Transaction.get_table_name()}
            {Transaction.get_fields_for_sql_query()}
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            txid,
            user_telegram_id,
            False,
            weeks,
            int(datetime.now().timestamp()),
        )
        await connection.execute(sql_query, params)
        await connection.commit()


async def set_status(
    status: bool, database_id: Optional[int] = None, txid: Optional[str] = None
) -> None:
    transaction = await get(database_id, txid)
    if transaction is None:
        return None

    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"UPDATE {Transaction.get_table_name()} SET status=? WHERE id=?"
        await connection.execute(sql_query, (status, transaction.id))
        await connection.commit()


async def get_new() -> List[Transaction]:
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"""
            SELECT * FROM {Transaction.get_table_name()}
            WHERE status=?
            AND created_at_timestamp >= ?
        """
        params = (
            False,
            int((datetime.now() - timedelta(minutes=20)).timestamp()),
        )

        cursor = await connection.execute(sql_query, params)
        rows = await cursor.fetchall()

        return [Transaction(*row) for row in rows]

async def get_all() -> List[Transaction]:
    async with aiosqlite.connect(sqlite_database_filepath) as connection:
        sql_query = f"SELECT * FROM {Transaction.get_table_name()}"
        cursor = await connection.execute(sql_query)
        rows = await cursor.fetchall()
        return [Transaction(*row) for row in rows]
