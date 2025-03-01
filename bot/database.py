import aiosqlite
import datetime
from typing import List, Tuple

DB_NAME = '/app/bot/bot.db'


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS reminders
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id INTEGER NOT NULL,
                           channel_id INTEGER NOT NULL,
                           reminder_time TEXT NOT NULL,
                           message TEXT NOT NULL,
                           created_at TEXT NOT NULL)''')
        await db.commit()

async def add_reminder(user_id: int, channel_id: int, reminder_time: datetime.datetime, message: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''INSERT INTO reminders 
                                  (user_id, channel_id, reminder_time, message, created_at)
                                  VALUES (?, ?, ?, ?, ?)''',
                                  (user_id, channel_id, reminder_time.isoformat(), message,
                                   datetime.datetime.now().isoformat()))
        await db.commit()
        return cursor.lastrowid


async def delete_reminder(reminder_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
        await db.commit()

async def get_pending_reminders() -> List[Tuple]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''SELECT * FROM reminders 
                                  WHERE reminder_time > ?''',
                                  (datetime.datetime.now().isoformat(),))
        return await cursor.fetchall()
