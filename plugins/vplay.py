import asyncio
import logging
import os
import re
import time

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChatAdminRequired, UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall

import config
from clients import bot, assistant, call_py
from plugins.font_style import sc

log = logging.getLogger(__name__)

os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)

# chat_id -> original downloaded file path currently playing
active_streams = {}

# chat_id -> list of file paths waiting in line
video_queue = {}

# chat_id -> current volume percent (default 100)
chat_volume = {}

# chat_id -> "off" / "low" / "high"
chat_bass = {}

# chat_id -> original downloaded file (used to re-apply bass / skip without re-download)
_original_file = {}

# chat_id -> playback position (seconds) at the moment the current ffmpeg
# stream started, and the wall-clock time it started — used to estimate
# "where are we now" for /skip.
chat_position_base = {}
chat_position_started_at = {}

# (original_path, level) -> bass-boosted file path, so we don't re-encode twice
_bass_cache = {}

BASS_GAIN = {"low": 8, "high": 16}

# Small cache so we don't hit get_chat_member on every single command/click
_admin_cache = {}
_ADMIN_CACHE_TTL = 300  # seconds


async def _is_admin_or_sudo(client, chat_id, user_id) -> bool:
    if user_id is None:
        return False
    if config.SUDO_USERS and user_id in config.SUDO_USERS:
        return True

    cache_key = (chat_id, user_id)
    cached = _admin_cache.get(cache_key)
    now = time.time()
    if cached and (now - cached[1]) < _ADMIN_CACHE_TTL:
        return cached[0]

    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        is_admin = False

    _admin_cache[cache_key] = (is_admin, now)
    return is_admin


async def is_allowed(_, client, message: Message) -> bool:
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
    if not message.from_user:
        return False
    return await _is_admin_or_sudo(client, message.chat.id, message.from_user.id)


allowed_filter = filters.create(is_allowed)


async def _admin_only_notice(message: Message):
    await message.reply_text(f"❍ {sc('admin can use this command only')}")


@bot.on_message(filters.command(["vplay", "skip", "next"]) & filters.group & ~allowed_filter)
async def not_admin_notice(client, message: Message):
    await _admin_only_notice(message)


def _safe_delete(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _parse_duration(text: str) -> int:
    """'5m' -> 300, '90s' -> 90, '2' -> 120 (bare number = minutes)."""
    match = re.fullmatch(r"(\d+)\s*(m|min|mins|s|sec|secs)?", text.strip().lower())
    if not match:
        raise ValueError("bad duration format")
    value = int(match.group(1))
    unit = match.group(2) or "m"
    return value if unit.startswith("s") else value * 60


# --------------------------------------------------------------------
# Auto-invite the assistant account into the group if it's missing, and
# try to give it admin rights so it's allowed to start the video chat.
#
# Bots can't reliably use add_chat_members() on a user they've never
# interacted with (Telegram rejects it as an unresolved peer, regardless
# of the bot's admin rights). The reliable way: the bot exports an
# invite link, and the ASSISTANT joins the group through that link
# itself.
#
# Separately, Telegram only allows an ADMIN to create a group's video
# chat (phone.CreateGroupCall -> CHAT_ADMIN_REQUIRED otherwise). So after
# joining, we also try to promote the assistant to admin. This only
# works if the BOT itself is an admin with "Add New Admins" rights — if
# not, promote silently fails and the user gets a clear error later
# telling them to do it manually.
# --------------------------------------------------------------------

async def _assistant_is_member(chat_id) -> bool:
    """Quick check: is the assistant already sitting in this group?"""
    try:
        await assistant.get_chat_member(chat_id, "me")
        return True
    except Exception as e:
        log.info(f"[assistant-invite] assistant not yet in {chat_id} ({e})")
        return False


async def _invite_assistant(client, chat_id):
    """
    Actually try to bring the assistant into the group (assumes the caller
    already knows the assistant is NOT a member yet).

    Returns (ok: bool, need_permission: bool, error: str | None).
    need_permission=True means the bot itself needs "invite users" rights.
    error holds the raw exception text for debugging when ok=False.
    """
    try:
        invite_link = await client.export_chat_invite_link(chat_id)
    except ChatAdminRequired as e:
        log.warning(f"[assistant-invite] bot lacks invite permission in {chat_id}: {e}")
        return False, True, str(e)
    except Exception as e:
        log.warning(f"[assistant-invite] export_chat_invite_link failed in {chat_id}: {e!r}")
        return False, False, str(e)

    try:
        await assistant.join_chat(invite_link)
    except UserAlreadyParticipant:
        return True, False, None
    except Exception as e:
        log.warning(f"[assistant-invite] assistant.join_chat failed in {chat_id}: {e!r}")
        return False, False, str(e)

    return True, False, None


async def _promote_assistant(client, chat_id):
    """
    Try to give the assistant admin rights so Telegram allows it to start
    (create) the group's video chat. If the bot itself isn't allowed to
    promote members, this just silently fails — the user will then see a
    clear CHAT_ADMIN_REQUIRED message telling them to do it manually.
    """
    try:
        assistant_user = await assistant.get_me()
        await client.promote_chat_member(
            chat_id,
            assistant_user.id,
            privileges=ChatPrivileges(
                can_manage_video_chats=True,
                can_invite_users=True,
                can_manage_chat=True,
            ),
        )
        return True
    except Exception as e:
        log.info(f"[assistant-invite] could not promote assistant in {chat_id}: {e!r}")
        return False


async def _ensure_assistant_in_group(client, chat_id):
    """
    Convenience wrapper: check + invite + try to promote, all in one call.
    Returns (ok: bool, need_permission: bool, error: str | None).
    """
    if not await _assistant_is_member(chat_id):
        ok, need_permission, error = await _invite_assistant(client, chat_id)
        if not ok:
            return ok, need_permission, error

    await _promote_assistant(client, chat_id)
    return True, False, None


# --------------------------------------------------------------------
# Player control buttons (Next / Volume / Bass) — VILLAIN_MUSIC font style.
# --------------------------------------------------------------------

def player_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(sc("next"), callback_data="vctl_next")],
            [InlineKeyboardButton(sc("volume"), callback_data="vctl_vol_open")],
        ]
    )


def queue_added_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(sc("next"), callback_data="vctl_next")]]
    )


def volume_markup(chat_id) -> InlineKeyboardMarkup:
    vol = chat_volume.get(chat_id, 100)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➖", callback_data="vctl_vol_delta_-10"),
                InlineKeyboardButton(f"{vol}%", callback_data="vctl_noop"),
                InlineKeyboardButton("➕", callback_data="vctl_vol_delta_10"),
            ],
            [
                InlineKeyboardButton("50%", callback_data="vctl_vol_set_50"),
                InlineKeyboardButton("100%", callback_data="vctl_vol_set_100"),
                InlineKeyboardButton("150%", callback_data="vctl_vol_set_150"),
                InlineKeyboardButton("200%", callback_data="vctl_vol_set_200"),
            ],
            [InlineKeyboardButton(sc("bass boost"), callback_data="vctl_bass_open")],
            [InlineKeyboardButton(sc("back"), callback_data="vctl_back")],
        ]
    )


def bass_markup(chat_id) -> InlineKeyboardMarkup:
    level = chat_bass.get(chat_id, "off")

    def label(l, text):
        return f"• {text} •" if level == l else text

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(label("off", sc("off")), callback_data="vctl_bass_set_off"),
                InlineKeyboardButton(label("low", sc("low")), callback_data="vctl_bass_set_low"),
                InlineKeyboardButton(label("high", sc("high")), callback_data="vctl_bass_set_high"),
            ],
            [InlineKeyboardButton(sc("back"), callback_data="vctl_vol_open")],
        ]
    )


# --------------------------------------------------------------------
# Bass processing (ffmpeg re-encode) + starting/restarting a stream
# with the chat's current volume/bass settings + an optional seek.
# --------------------------------------------------------------------

async def _apply_bass(path, level):
    if level == "off":
        return path

    key = (path, level)
    cached = _bass_cache.get(key)
    if cached and os.path.exists(cached):
        return cached

    gain = BASS_GAIN[level]
    out_path = f"{path}.bass_{level}.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", path,
        "-af", f"bass=g={gain}",
        "-c:v", "copy",
        "-c:a", "aac",
        out_path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
    except Exception:
        return path

    if proc.returncode == 0 and os.path.exists(out_path):
        _bass_cache[key] = out_path
        return out_path
    return path  # bass processing failed — fall back to the original file


async def _start_stream(chat_id, path, seek_seconds=0):
    """Start (or restart — e.g. for bass toggle / /skip) playback of `path`."""
    _original_file[chat_id] = path
    chat_volume.setdefault(chat_id, 100)
    chat_bass.setdefault(chat_id, "off")

    play_path = await _apply_bass(path, chat_bass[chat_id])
    ffmpeg_params = f"-ss {seek_seconds}" if seek_seconds else None

    await call_py.play(
        chat_id,
        MediaStream(
            play_path,
            video_flags=MediaStream.Flags.REQUIRED,
            audio_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=ffmpeg_params,
        ),
    )

    if chat_volume[chat_id] != 100:
        try:
            await call_py.change_volume_call(chat_id, chat_volume[chat_id])
        except Exception:
            pass

    active_streams[chat_id] = path
    chat_position_base[chat_id] = seek_seconds
    chat_position_started_at[chat_id] = time.time()


def _current_position(chat_id) -> int:
    base = chat_position_base.get(chat_id, 0)
    started_at = chat_position_started_at.get(chat_id, time.time())
    return int(base + (time.time() - started_at))


async def play_next(chat_id):
    """
    Move to the next queued video. Called by /next, the Next button, and
    automatically when a stream ends. Sends its own status message.
    Returns True if a new video started, False if the queue was empty.
    """
    old_path = active_streams.pop(chat_id, None)
    _safe_delete(old_path)
    chat_volume.pop(chat_id, None)
    chat_bass.pop(chat_id, None)
    _original_file.pop(chat_id, None)
    chat_position_base.pop(chat_id, None)
    chat_position_started_at.pop(chat_id, None)

    queue = video_queue.get(chat_id) or []
    while queue:
        next_path = queue.pop(0)
        try:
            await _start_stream(chat_id, next_path)
            await bot.send_message(
                chat_id,
                f"❍ {sc('playing the next video from the queue')}",
                reply_markup=player_markup(),
            )
            return True
        except Exception:
            _safe_delete(next_path)
            continue

    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass
    await bot.send_message(chat_id, f"❍ {sc('queue is empty, stream stopped')}")
    return False


@bot.on_message(filters.command("vplay") & filters.group & allowed_filter)
async def vplay_handler(client, message: Message):
    replied = message.reply_to_message

    if not replied or not (replied.video or replied.document):
        await message.reply_text(
            f"❍ {sc('reply to a')} **{sc('video')}** {sc('with')} /vplay\n\n"
            f"▸ {sc('send a video in this group')}\n"
            f"▸ {sc('reply to that video with')} /vplay"
        )
        return

    if replied.document and not (replied.document.mime_type or "").startswith("video/"):
        await message.reply_text(f"❍ {sc('that file does not look like a video')}")
        return

    status_msg = await message.reply_text(f"❍ {sc('downloading video, please wait')}...")

    file_path = os.path.join(config.DOWNLOADS_DIR, f"{message.chat.id}_{int(time.time())}.mp4")

    try:
        await client.download_media(replied, file_name=file_path)
    except Exception as e:
        await status_msg.edit_text(f"❍ {sc('failed to download video')}\n\n`{e}`")
        return

    chat_id = message.chat.id

    if chat_id in active_streams:
        video_queue.setdefault(chat_id, []).append(file_path)
        position = len(video_queue[chat_id])
        await status_msg.edit_text(
            f"❍ {sc('added to queue')}, {sc('position')} #{position}\n"
            f"▸ {sc('it will play automatically once the current video ends, or tap next below')}",
            reply_markup=queue_added_markup(),
        )
        return

    # Make sure the assistant account is actually in this group (and, if
    # possible, an admin) before we try to join the video chat with it.
    ok, need_permission, join_error = await _ensure_assistant_in_group(client, chat_id)
    if not ok:
        if need_permission:
            await status_msg.edit_text(
                f"❍ {sc('bot requires invite users via link permission')}\n"
                f"▸ {sc('to invite the assistant account to this chat')}\n\n"
                f"{sc('please make me admin with add members / invite users permission, then try again')}"
            )
        else:
            await status_msg.edit_text(
                f"❍ {sc('could not add the assistant account to this group')}\n"
                f"▸ {sc('please add')} @khushi_masti {sc('manually, then try again')}\n\n"
                f"{sc('reason')} : `{join_error}`"
            )
        _safe_delete(file_path)
        return

    await status_msg.edit_text(f"❍ {sc('please wait')}...\n\n{sc('joining video chat and starting stream')}")

    try:
        await _start_stream(chat_id, file_path)
        await status_msg.edit_text(
            f"❍ {sc('now playing your video in the group video chat')}",
            reply_markup=player_markup(),
        )

    except NoActiveGroupCall:
        await status_msg.edit_text(
            f"❍ {sc('no active videochat found')}\n\n"
            f"{sc('please start a videochat in your group and try again')}"
        )
        _safe_delete(file_path)

    except ChatAdminRequired:
        await status_msg.edit_text(
            f"❍ {sc('assistant needs admin rights to start the video chat')}\n"
            f"▸ {sc('please make the assistant account admin in this group')} "
            f"({sc('with start video chats permission')}), {sc('then try again')}"
        )
        _safe_delete(file_path)

    except Exception as e:
        await status_msg.edit_text(f"❍ {sc('could not start stream')}\n\n`{e}`")
        _safe_delete(file_path)


@bot.on_message(filters.command("next") & filters.group & allowed_filter)
async def next_handler(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in active_streams and not video_queue.get(chat_id):
        await message.reply_text(f"❍ {sc('nothing is playing right now')}")
        return
    await play_next(chat_id)


@bot.on_message(filters.command("skip") & filters.group & allowed_filter)
async def skip_handler(client, message: Message):
    chat_id = message.chat.id

    if chat_id not in active_streams:
        await message.reply_text(f"❍ {sc('nothing is playing right now')}")
        return

    if len(message.command) < 2:
        await message.reply_text(
            f"❍ {sc('example')} :\n\n/skip `5m` {sc('or')} /skip `90s`"
        )
        return

    try:
        skip_seconds = _parse_duration(message.command[1])
    except ValueError:
        await message.reply_text(
            f"❍ {sc('invalid time format, use e.g.')} `5m` {sc('or')} `90s`"
        )
        return

    new_pos = max(0, _current_position(chat_id) + skip_seconds)

    status = await message.reply_text(f"❍ {sc('seeking')}...\n\n{sc('please hold on')}...")
    original = _original_file.get(chat_id)
    if not original:
        await status.edit_text(f"❍ {sc('could not skip, no active file found')}")
        return

    try:
        await _start_stream(chat_id, original, seek_seconds=new_pos)
        mins, secs = divmod(new_pos, 60)
        await status.edit_text(
            f"❍ {sc('stream successfully seeked')}\n\n"
            f"{sc('duration')} : {mins}m {secs}s",
            reply_markup=player_markup(),
        )
    except Exception as e:
        await status.edit_text(f"❍ {sc('failed to seek')}\n\n`{e}`")
