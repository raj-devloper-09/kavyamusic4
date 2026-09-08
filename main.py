import asyncio
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import config  # noqa: E402
from clients import bot, assistant, call_py  # noqa: E402
from plugins.font_style import sc  # noqa: E402

import plugins.vplay      # noqa: E402,F401 - /vplay + /next (the only real features)
import plugins.basic      # noqa: E402,F401 - /start, /help, stream-end cleanup
import plugins.controls   # noqa: E402,F401 - Next/Volume/Bass inline buttons
import plugins.soon       # noqa: E402,F401 - "coming soon" catch-all


async def _log_to_group(client, text):
    if not config.LOG_GROUP_ID:
        return
    try:
        await client.send_message(config.LOG_GROUP_ID, text)
    except Exception as e:
        log.warning(f"Could not send log-group message: {e}")


async def start():
    await assistant.start()
    log.info("Assistant account started.")
    me_assistant = await assistant.get_me()
    await _log_to_group(
        assistant,
        f"❍ {sc('assistant started')}\n\n"
        f"{sc('name')} : {me_assistant.first_name}\n"
        f"{sc('id')} : `{me_assistant.id}`",
    )

    await bot.start()
    log.info("Bot started.")
    me_bot = await bot.get_me()
    await _log_to_group(
        bot,
        f"❍ {sc('bot started')}\n\n"
        f"{sc('name')} : {me_bot.first_name}\n"
        f"{sc('username')} : @{me_bot.username}",
    )

    await call_py.start()
    log.info("PyTgCalls started. Bot is ready — use /vplay in a group.")


if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
        loop.run_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
