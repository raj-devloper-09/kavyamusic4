from pyrogram import filters
from pyrogram.types import Message

from clients import bot
from plugins.commands_data import ALL_SOON_COMMANDS
from plugins.font_style import sc

SOON_TEXT = (
    "**╭───────────────────⦿**\n"
    "**│ ▸ /{cmd} **\n"
    "**├───────────────────⦿**\n"
    f"**│ ▸ {sc('this feature is available soon')} **\n"
    f"**│ ▸ {sc('right now only')} /start {sc('and')} /vplay {sc('work')} **\n"
    "**╰───────────────────⦿**"
)


@bot.on_message(filters.command(ALL_SOON_COMMANDS))
async def coming_soon_handler(client, message: Message):
    cmd = message.command[0] if message.command else "command"
    await message.reply_text(SOON_TEXT.format(cmd=cmd))
