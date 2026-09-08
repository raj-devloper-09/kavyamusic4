from pyrogram import Client
from pytgcalls import PyTgCalls

import config

# The BOT — handles all commands (/start, /vplay work; everything else is
# just shown/replied to as "coming soon")
bot = Client(
    name="vplay_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

# The ASSISTANT — a real user account that joins the group's video chat
# and does the actual streaming (bots cannot join voice/video chats directly)
assistant = Client(
    name="vplay_assistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING,
)

# PyTgCalls instance is bound to the ASSISTANT client, not the bot
call_py = PyTgCalls(assistant)
