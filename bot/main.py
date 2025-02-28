import os
import logging
import discord
import datetime
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateparser import parse
from dotenv import load_dotenv
from bot.database import init_db, add_reminder, get_pending_reminders, delete_reminder

discord.voice_client.VoiceClient.warn_nacl = False

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            help_command=None
        )

        self.scheduler = AsyncIOScheduler()

    async def setup_hook(self):
        logger.info('Инициализация бота и базы данных ...')
        await init_db()
        self.scheduler.start()
        # await self.load_extension('bot.tasks')
        await self.tree.sync()
        logger.info('Бот готов к работе')

bot = MyBot()

@bot.event
async def on_ready():
    logger.info(f'{bot.user} успешно запущен!')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await restore_reminders()


async def restore_reminders():
    try:
        reminders = await get_pending_reminders()
        logger.info(f"Восстановление {len(reminders)} напоминания из базы данных")
        for reminder in reminders:
            reminder_id, user_id, channel_id, reminder_time, message, _ = reminder
            reminder_time = datetime.datetime.fromisoformat(reminder_time)
            bot.scheduler.add_job(
                send_reminder,
                'date',
                run_date=reminder_time,
                args=(user_id, channel_id, message, reminder_id),
                id=str(reminder_id)
            )
        logger.info("Успешно восстановлены все напоминания")
    except Exception as e:
        logger.error(f"Ошибка восстановления напоминаний: {str(e)}")

async def send_reminder(user_id: int, channel_id: int, message: str, reminder_id: int):
    try:
        channel = bot.get_channel(channel_id)
        user = bot.get_user(user_id)
        if channel and user:
            await channel.send(f'{user.mention}, Вы просили напомнить: {message}')
            await delete_reminder(reminder_id)
            logger.info(f"Sent reminder {reminder_id} to user {user_id}")
        else:
            logger.warning(f"Не удается отправить напоминание {reminder_id} - канал или юзер не найдены")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания {reminder_id}: {str(e)}")

@bot.hybrid_command()
async def active_developer_badge(ctx: commands.Context):
    """Получить бейдж активного разработчика Discord"""
    try:
        embed = discord.Embed(
            title="Program Ran Successfully",
            description=(
                "**+** You have ran the bot correctly and have claimed your Discord Developer Badge.\n\n"
                "**+** It may take up to 24 hours or a tiny bit more for your badge to shop up here "
                "(https://discord.com/developers/active-developer)\n\n**+**"
            ),
            colour=0x00f53d
        )
        embed.set_footer(text="This bot started")
        await ctx.send(embed=embed)
        logger.info(f"Active developer badge command used by {ctx.author.id}")
    except Exception as e:
        logger.error(f"Error in active_developer_badge: {str(e)}")

@bot.hybrid_command()
async def remind(ctx: commands.Context, time_str: str, *, message: str):
    """Установить напоминание
    Пример: /remind in 1 hour Приготовить пюрешечку с котлетками или /remind через 1 час(либо минуты)
    Пример 2: /remind 18:25 Приготовить пюрешечку с котлетками
    Поддерживаемые форматы:
        "in 1 hour" (через 1 час)
        "in 30 minutes" (через 30 минут)
        "tomorrow at 9am" (завтра в 9 утра)

    Абсолютное время:
    "2025-02-28 18:00"
    "28.02.2025 18:00"
    """
    try:
        now = datetime.datetime.now()
        reminder_time = parse(time_str, settings={'RELATIVE_BASE': now})

        if not reminder_time or reminder_time < now:
            await ctx.send("Пожалуйста, укажите корректное время в будущем (Например: 18:25)", ephemeral=True)
            logger.warning(f"Invalid time format from user {ctx.author.id}: {time_str}")
            return

        reminder_id = await add_reminder(ctx.author.id, ctx.channel.id, reminder_time, message)
        bot.scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time,
            args=(ctx.author.id, ctx.channel.id, message, reminder_id),
            id=str(reminder_id)
        )
        await ctx.send(f"Напоминание установлено на {reminder_time.strftime('%d-%m-%Y %H:%M')}")
        logger.info(f"New reminder added by {ctx.author.id}: {message} at {reminder_time}")
    except Exception as e:
        logger.error(f"Error in remind command: {str(e)}")
        await ctx.send(f"Ошибка: {str(e)}", ephemeral=True)


if __name__ == '__main__':
    try:
        logger.info("Starting bot...")
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.critical(f"Failed to start bot: {str(e)}")
        raise
