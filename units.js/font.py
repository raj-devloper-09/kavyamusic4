"""
Small helper that turns normal text into the same 'sᴍᴀʟʟ ᴄᴀᴘs' look used
throughout VILLAIN_MUSIC's messages (start text, error text, buttons...).

This is ONLY a visual/design helper — it has nothing to do with the bot's
actual features. Used so plain English strings written in the plugins
automatically render in the VILLAIN_MUSIC font style.
"""

_MAP = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ",
    "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
    "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ",
    "w": "ᴡ", "y": "ʏ", "z": "ᴢ",
    # "s" and "x" are intentionally left as-is — VILLAIN_MUSIC does the same
    # since there's no widely-supported small-caps glyph for them.
}


def sc(text: str) -> str:
    """Convert text to VILLAIN_MUSIC-style small caps (lowercase only)."""
    return "".join(_MAP.get(ch.lower(), ch) if ch.islower() else ch for ch in text)


def box(title: str, lines, footer: str = None) -> str:
    """
    Render VILLAIN_MUSIC's boxed '├───⦿' card style.

    title: shown on the first line
    lines: list of strings, one per row
    footer: optional closing line (credits/tap-to-use hint etc.)
    """
    out = ["**╭───────────────────⦿**", f"**│ ▸ {title} **", "**├───────────────────⦿**"]
    for line in lines:
        out.append(f"**│ ▸ {line} **")
    out.append("**├───────────────────⦿**" if footer else "**╰───────────────────⦿**")
    if footer:
        out.append(f"**│ {footer} **")
        out.append("**╰───────────────────⦿**")
    return "\n".join(out)
