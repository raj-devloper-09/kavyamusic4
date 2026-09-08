"""
Small helper that turns normal text into the same 'sᴍᴀʟʟ ᴄᴀᴘs' look used
throughout VILLAIN_MUSIC's messages. Visual/design helper only.
"""

_MAP = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ",
    "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
    "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ",
    "w": "ᴡ", "y": "ʏ", "z": "ᴢ",
}


def sc(text: str) -> str:
    """Convert text to VILLAIN_MUSIC-style small caps (lowercase only)."""
    return "".join(_MAP.get(ch.lower(), ch) if ch.islower() else ch for ch in text)
