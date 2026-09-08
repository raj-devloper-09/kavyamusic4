import random

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamEnded

import config
from clients import bot, call_py
from plugins.vplay import play_next, _ensure_assistant_in_group
from plugins.commands_data import CATEGORIES
from plugins.font_style import sc

# --------------------------------------------------------------------
# /start — VILLAIN_MUSIC look, 1:1:
#   • same box template:  ╭──⦿ / │ ▸ / ├──⦿ / ╰──⦿
#   • same random start VIDEO (not a photo) from config.START_VID
#   • same minimal-emoji, smallcaps wording style
# kavya-music-bot's actual working brain stays underneath — only
# /start and /vplay really work, everything else is "coming soon".
# --------------------------------------------------------------------

def start_caption(user_mention: str, bot_mention: str) -> str:
    return (
        "**╭───────────────────⦿**\n"
        f"**│ ▸ {sc('hey')} {user_mention} **\n"
        f"**│ ▸ {sc('i am')} {bot_mention} **\n"
        "**├───────────────────⦿**\n"
        f"**│ ▸ {sc('i have special features')}**\n"
        f"**│ ▸ {sc('all-in-one video chat bot')}**\n"
        "**├───────────────────⦿**\n"
        f"**│ ▸ {sc('bot for telegram groups')}**\n"
        f"**│ ▸ {sc('reply to any video with')} /vplay**\n"
        f"**│ ▸ {sc('lag-free, high-quality streams')}**\n"
        "**├───────────────────⦿**\n"
        f"**│ {sc('tap help below for commands')}**\n"
        "**╰───────────────────⦿**"
    )


def start_buttons(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    sc("add me in your group"),
                    url=f"https://t.me/{bot_username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(sc("owner"), url=f"tg://user?id={config.OWNER_ID}"),
                InlineKeyboardButton(sc("info"), callback_data="soon_info"),
            ],
            [
                InlineKeyboardButton(sc("support"), url=config.SUPPORT_CHAT),
                InlineKeyboardButton(sc("source"), url=config.SOURCE_URL),
            ],
            [
                InlineKeyboardButton(sc("help and commands"), callback_data="soon_help_open"),
            ],
        ]
    )


@bot.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    me = await client.get_me()
    user_mention = message.from_user.mention if message.from_user else sc("there")
    caption = start_caption(user_mention, me.mention)
    markup = start_buttons(me.username)

    try:
        await message.reply_video(
            random.choice(config.START_VID), caption=caption, reply_markup=markup
        )
    except Exception:
        try:
            # Video failed to load — fall back to the photo.
            await message.reply_photo(photo=config.START_IMG, caption=caption, reply_markup=markup)
        except Exception:
            # Even the photo failed — plain text so /start never breaks.
            await message.reply_text(caption, reply_markup=markup)


@bot.on_callback_query(filters.regex(r"^soon_info$"))
async def start_info_cb(client, cq: CallbackQuery):
    me = await client.get_me()
    text = (
        "**╭───────────────────⦿**\n"
        f"**│ ▸ {sc('bot info')} **\n"
        "**├───────────────────⦿**\n"
        f"**│ ▸ {sc('name')} : {me.first_name}**\n"
        f"**│ ▸ {sc('username')} : @{me.username}**\n"
        f"**│ ▸ {sc('working features')} : /start, /vplay**\n"
        f"**│ ▸ {sc('everything else is coming soon')}**\n"
        "**╰───────────────────⦿**"
    )
    back_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(sc("back"), callback_data="soon_start_back")]]
    )
    await cq.message.edit_caption(caption=text, reply_markup=back_markup)
    await cq.answer()


@bot.on_callback_query(filters.regex(r"^soon_start_back$"))
async def start_back_cb(client, cq: CallbackQuery):
    me = await client.get_me()
    user_mention = cq.from_user.mention if cq.from_user else sc("there")
    caption = start_caption(user_mention, me.mention)
    await cq.message.edit_caption(caption=caption, reply_markup=start_buttons(me.username))
    await cq.answer()


# --------------------------------------------------------------------
# /help — categorised command menu (VILLAIN_MUSIC style buttons).
# Everything here is just a NAME LIST for looks — the only commands that
# actually do something are /start and /vplay. Running anything else
# triggers the "coming soon" reply handled in plugins/soon.py.
# --------------------------------------------------------------------

CATEGORY_KEYS = list(CATEGORIES.keys())


def help_home_markup() -> InlineKeyboardMarkup:
    rows, row = [], []
    for i, cat in enumerate(CATEGORY_KEYS, start=1):
        row.append(InlineKeyboardButton(cat, callback_data=f"soon_cat_{i}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(sc("close"), callback_data="soon_close")])
    return InlineKeyboardMarkup(rows)


HELP_HOME_TEXT = (
    "**╭───────────────────⦿**\n"
    f"**│ ▸ {sc('help & commands')} **\n"
    "**├───────────────────⦿**\n"
    f"**│ ▸ {sc('only')} /start {sc('and')} /vplay {sc('actually work right now')} **\n"
    f"**│ ▸ {sc('everything below is coming soon')} **\n"
    "**╰───────────────────⦿**\n\n"
    f"❍ {sc('tap a category to see its commands')}"
)


@bot.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    await message.reply_text(HELP_HOME_TEXT, reply_markup=help_home_markup())


@bot.on_callback_query(filters.regex(r"^soon_help_open$"))
async def help_open_cb(client, cq: CallbackQuery):
    if cq.message.photo or cq.message.video:
        await cq.message.delete()
        await cq.message.reply_text(HELP_HOME_TEXT, reply_markup=help_home_markup())
    else:
        await cq.message.edit_text(HELP_HOME_TEXT, reply_markup=help_home_markup())
    await cq.answer()


@bot.on_callback_query(filters.regex(r"^soon_cat_(\d+)$"))
async def help_category_cb(client, cq: CallbackQuery):
    idx = int(cq.matches[0].group(1)) - 1
    if idx < 0 or idx >= len(CATEGORY_KEYS):
        await cq.answer(sc("not found"), show_alert=True)
        return

    cat = CATEGORY_KEYS[idx]
    cmds = CATEGORIES[cat]
    cmd_list = ", ".join(f"`/{c}`" for c in cmds)

    text = (
        "**╭───────────────────⦿**\n"
        f"**│ ▸ {cat} **\n"
        "**├───────────────────⦿**\n"
        f"**│ ▸ {sc('this feature is available soon')} **\n"
        "**╰───────────────────⦿**\n\n"
        f"{cmd_list}"
    )
    back_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(sc("back"), callback_data="soon_help_open")]]
    )
    await cq.message.edit_text(text, reply_markup=back_markup, disable_web_page_preview=True)
    await cq.answer()


@bot.on_callback_query(filters.regex(r"^soon_close$"))
async def help_close_cb(client, cq: CallbackQuery):
    await cq.message.delete()
    await cq.answer()


# --------------------------------------------------------------------
# Auto-cleanup when a /vplay stream naturally ends (unchanged behaviour).
# --------------------------------------------------------------------

@call_py.on_update()
async def on_stream_end(client, update: Update):
    if isinstance(update, StreamEnded):
        await play_next(update.chat_id)


# --------------------------------------------------------------------
# Auto-invite the assistant the moment the BOT is added to a group —
# no need to wait for someone to run /vplay first.
#
# If the assistant is already in the group -> silently do nothing.
# If it's missing and we can add it -> add it, confirm quietly.
# If we can't add it because the bot has no "invite users" admin
# right -> ask the group to grant that permission.
# --------------------------------------------------------------------

@bot.on_message(filters.new_chat_members)
async def on_bot_added_to_group(client, message: Message):
    me = await client.get_me()
    if not any(u.id == me.id for u in message.new_chat_members):
        return  # some other user joined, not the bot itself — ignore

    chat_id = message.chat.id
    status = await message.reply_text(
        f"❍ {sc('thanks for adding me')}\n{sc('checking assistant account')}..."
    )

    ok, need_permission = await _ensure_assistant_in_group(client, chat_id)

    if ok:
        await status.edit_text(
            f"❍ {sc('assistant account is ready in this group')}\n"
            f"▸ {sc('reply to a video with')} /vplay {sc('to start streaming')}"
        )
    elif need_permission:
        await status.edit_text(
            f"❍ {sc('bot requires invite users via link permission')}\n"
            f"▸ {sc('to invite the assistant account to this chat')}\n\n"
            f"{sc('please make me admin with add members / invite users permission, then send')} "
            f"/vplay {sc('again')}"
        )
    else:
        await status.edit_text(
            f"❍ {sc('could not add the assistant account to this group')}\n"
            f"▸ {sc('please add')} @khushi_masti {sc('manually, then try')} /vplay"
        )
