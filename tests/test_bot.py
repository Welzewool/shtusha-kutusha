import pytest
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from bot.database import init_db, add_reminder, get_pending_reminders, delete_reminder


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield
    # Очистка базы данных после каждого теста
    async with aiosqlite.connect('bot.db') as db:
        await db.execute('DELETE FROM reminders')
        await db.commit()


@pytest.mark.asyncio
async def test_reminder_workflow():
    test_time = datetime.now() + timedelta(hours=1)
    test_message = "Test reminder"

    # Тест добавления напоминания
    reminder_id = await add_reminder(123, 456, test_time, test_message)
    assert isinstance(reminder_id, int)

    # Тест получения напоминаний
    reminders = await get_pending_reminders()
    assert len(reminders) == 1
    assert reminders[0][4] == test_message

    # Тест удаления напоминания
    await delete_reminder(reminder_id)
    reminders = await get_pending_reminders()
    assert len(reminders) == 0


@pytest.mark.asyncio
async def test_invalid_reminder():
    with pytest.raises(Exception):
        await add_reminder(None, None, None, None)