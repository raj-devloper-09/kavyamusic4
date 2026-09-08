from pyrogram import filters
from pyrogram.types import CallbackQuery

from clients import bot, call_py
from plugins.vplay import (
    active_streams,
    chat_volume,
    chat_bass,
    _original_file,
    _is_admin_or_sudo,
    _current_position,
    _start_stream,
    play_next,
    player_markup,
    volume_markup,
    bass_markup,
)
from plugins.font_style import sc


@bot.on_callback_query(filters.regex(r"^vctl_"))
async def controls_cb(client, cq: CallbackQuery):
    chat_id = cq.message.chat.id
    data = cq.data
    user_id = cq.from_user.id if cq.from_user else None

    if not await _is_admin_or_sudo(client, chat_id, user_id):
        await cq.answer(f"❍ {sc('admin can use this command only')}", show_alert=True)
        return

    if data == "vctl_noop":
        await cq.answer()
        return

    if data == "vctl_next":
        if chat_id not in active_streams:
            await cq.answer(f"❍ {sc('nothing is playing right now')}", show_alert=True)
            return
        try:
            await cq.message.edit_reply_markup(None)
        except Exception:
            pass
        await play_next(chat_id)
        await cq.answer()
        return

    if chat_id not in active_streams:
        await cq.answer(f"❍ {sc('nothing is playing right now')}", show_alert=True)
        return

    if data == "vctl_vol_open":
        await cq.message.edit_reply_markup(volume_markup(chat_id))
        await cq.answer()
        return

    if data == "vctl_bass_open":
        await cq.message.edit_reply_markup(bass_markup(chat_id))
        await cq.answer()
        return

    if data == "vctl_back":
        await cq.message.edit_reply_markup(player_markup())
        await cq.answer()
        return

    if data.startswith("vctl_vol_delta_"):
        delta = int(data.rsplit("_", 1)[1])
        vol = max(10, min(200, chat_volume.get(chat_id, 100) + delta))
        chat_volume[chat_id] = vol
        try:
            await call_py.change_volume_call(chat_id, vol)
        except Exception:
            pass
        await cq.message.edit_reply_markup(volume_markup(chat_id))
        await cq.answer(f"❍ {sc('volume')} : {vol}%")
        return

    if data.startswith("vctl_vol_set_"):
        vol = int(data.rsplit("_", 1)[1])
        chat_volume[chat_id] = vol
        try:
            await call_py.change_volume_call(chat_id, vol)
        except Exception:
            pass
        await cq.message.edit_reply_markup(volume_markup(chat_id))
        await cq.answer(f"❍ {sc('volume')} : {vol}%")
        return

    if data.startswith("vctl_bass_set_"):
        level = data.rsplit("_", 1)[1]
        chat_bass[chat_id] = level
        await cq.answer(f"❍ {sc('applying bass, please wait')}...")

        original = _original_file.get(chat_id)
        if original:
            current_pos = _current_position(chat_id)
            try:
                await _start_stream(chat_id, original, seek_seconds=current_pos)
            except Exception:
                pass

        await cq.message.edit_reply_markup(bass_markup(chat_id))
        return
